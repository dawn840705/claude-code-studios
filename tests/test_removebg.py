"""Tests for scripts/removebg.py — the deterministic remove.bg gate.

The point of these tests is the **exit-code contract**, because that is what
`$remove-bg` reads instead of parsing stdout:

    0  every requested image processed
    1  partial failure, or nothing processed because everything was skipped
    2  all failed / 402 insufficient credits / 403 auth / --max-calls tripped
    3  could not run (no API key, bad path) — nothing called, nothing charged

Every test runs against a local stub HTTP server. **No test may reach the real
remove.bg API** — that would cost credits and make CI depend on a third party.
`ENDPOINT_*` is monkeypatched per test, so a regression that hardcodes the real
URL will surface here as a network error rather than a silent charge.
"""

import http.server
import json
import os
import struct
import subprocess
import sys
import threading
import zlib

import pytest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(REPO, "scripts", "removebg.py")

sys.path.insert(0, os.path.join(REPO, "scripts"))
import removebg  # noqa: E402


# --------------------------------------------------------------------------
# Fixtures
# --------------------------------------------------------------------------

def _png_bytes(w: int = 8, h: int = 8) -> bytes:
    """A real (if boring) PNG, so preflight sees a plausible image file."""
    def chunk(tag: bytes, data: bytes) -> bytes:
        body = tag + data
        return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body) & 0xFFFFFFFF)

    raw = b"".join(b"\x00" + b"\xff\x00\x00\xff" * w for _ in range(h))
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(raw))
        + chunk(b"IEND", b"")
    )


@pytest.fixture
def images(tmp_path):
    """Three valid PNGs plus one zero-byte file that preflight must reject."""
    raw = tmp_path / "raw"
    raw.mkdir()
    for name in ("a", "b", "c"):
        (raw / f"{name}.png").write_bytes(_png_bytes())
    (raw / "broken.png").write_bytes(b"")
    return raw


class _Stub:
    """Configurable remove.bg stand-in. `mode` drives the POST response."""

    def __init__(self, mode: str = "ok", fail_on: int | None = None):
        self.mode = mode
        self.fail_on = fail_on
        self.calls = 0
        outer = self

        class Handler(http.server.BaseHTTPRequestHandler):
            def log_message(self, *a):  # keep pytest output clean
                pass

            def do_GET(self):  # /account
                self._json(200, {
                    "data": {"attributes": {
                        "credits": {"total": 42.5, "subscription": 40,
                                    "payasyougo": 2.5, "enterprise": 0},
                        "api": {"free_calls": 50, "sizes": "all"},
                    }}
                })

            def do_POST(self):  # /removebg
                self.rfile.read(int(self.headers.get("Content-Length", 0)))
                outer.calls += 1
                n = outer.calls
                if outer.mode == "402":
                    return self._err(402, "Insufficient credits", "insufficient_credits")
                if outer.mode == "403":
                    return self._err(403, "Invalid API Key", "auth_failed")
                if outer.mode == "allfail":
                    return self._err(400, "Could not process image", "unknown_foreground")
                if outer.mode == "partial" and n == outer.fail_on:
                    return self._err(400, "Could not process image", "unknown_foreground")
                if outer.mode == "429then200" and n <= 2:
                    return self._err(429, "Rate limit exceeded", "rate_limit_exceeded",
                                     extra={"Retry-After": "0"})
                blob = _png_bytes()
                self.send_response(200)
                self.send_header("Content-Type", "image/png")
                self.send_header("Content-Length", str(len(blob)))
                self.send_header("X-Credits-Charged", "0.25")
                self.send_header("X-Width", "8")
                self.send_header("X-Height", "8")
                self.end_headers()
                self.wfile.write(blob)

            def _json(self, code, payload, extra=None):
                body = json.dumps(payload).encode()
                self.send_response(code)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                for k, v in (extra or {}).items():
                    self.send_header(k, v)
                self.end_headers()
                self.wfile.write(body)

            def _err(self, code, title, ecode, extra=None):
                self._json(code, {"errors": [{"title": title, "code": ecode}]}, extra)

        self._srv = http.server.HTTPServer(("127.0.0.1", 0), Handler)
        self.port = self._srv.server_address[1]
        threading.Thread(target=self._srv.serve_forever, daemon=True).start()

    def close(self):
        self._srv.shutdown()
        self._srv.server_close()


@pytest.fixture
def stub(monkeypatch):
    """Factory. Repoints the module's endpoints at the local stub."""
    made = []

    def make(mode="ok", fail_on=None):
        s = _Stub(mode, fail_on)
        made.append(s)
        monkeypatch.setattr(removebg, "ENDPOINT_REMOVEBG", f"http://127.0.0.1:{s.port}/removebg")
        monkeypatch.setattr(removebg, "ENDPOINT_ACCOUNT", f"http://127.0.0.1:{s.port}/account")
        monkeypatch.setenv(removebg.DEFAULT_KEY_ENV, "stub-key-0123456789")
        return s

    yield make
    for s in made:
        s.close()


def run_args(images, out, *extra):
    return ["run", str(images), "--out", str(out), *extra]


# --------------------------------------------------------------------------
# Exit-code contract — the reason this file exists
# --------------------------------------------------------------------------

def test_all_succeed_exits_0(images, tmp_path, stub):
    stub("ok")
    assert removebg.main(run_args(images, tmp_path / "out")) == removebg.EXIT_OK


def test_partial_failure_exits_1(images, tmp_path, stub):
    stub("partial", fail_on=2)
    assert removebg.main(run_args(images, tmp_path / "out")) == removebg.EXIT_WARN


def test_all_fail_exits_2(images, tmp_path, stub):
    stub("allfail")
    assert removebg.main(run_args(images, tmp_path / "out")) == removebg.EXIT_ABORT


def test_insufficient_credits_exits_2(images, tmp_path, stub):
    s = stub("402")
    assert removebg.main(run_args(images, tmp_path / "out")) == removebg.EXIT_ABORT
    # A 402 stops the batch — it must not keep spending on the remaining images.
    assert s.calls == 1


def test_auth_failure_exits_2(images, tmp_path, stub):
    s = stub("403")
    assert removebg.main(run_args(images, tmp_path / "out")) == removebg.EXIT_ABORT
    assert s.calls == 1


def test_everything_skipped_exits_1(images, tmp_path, stub):
    """Second run over the same outputs processes nothing — a warning, not a pass."""
    stub("ok")
    out = tmp_path / "out"
    assert removebg.main(run_args(images, out)) == removebg.EXIT_OK
    assert removebg.main(run_args(images, out)) == removebg.EXIT_WARN


def test_missing_api_key_exits_3(images, tmp_path, monkeypatch):
    monkeypatch.delenv(removebg.DEFAULT_KEY_ENV, raising=False)
    assert removebg.main(run_args(images, tmp_path / "out")) == removebg.EXIT_CANNOT_RUN


def test_missing_input_path_exits_3(tmp_path, stub):
    stub("ok")
    assert removebg.main(["estimate", str(tmp_path / "nope"), "--out", str(tmp_path / "o")]) \
        == removebg.EXIT_CANNOT_RUN


def test_empty_directory_exits_3(tmp_path, stub):
    stub("ok")
    empty = tmp_path / "empty"
    empty.mkdir()
    assert removebg.main(["estimate", str(empty), "--out", str(tmp_path / "o")]) \
        == removebg.EXIT_CANNOT_RUN


# --------------------------------------------------------------------------
# Cost safety
# --------------------------------------------------------------------------

def test_estimate_makes_no_billable_call(images, tmp_path, stub):
    """The cost disclosure must not itself cost anything."""
    s = stub("ok")
    assert removebg.main(["estimate", str(images), "--out", str(tmp_path / "out")]) == removebg.EXIT_OK
    assert s.calls == 0


def test_dry_run_makes_no_billable_call(images, tmp_path, stub):
    s = stub("ok")
    assert removebg.main(run_args(images, tmp_path / "out", "--dry-run")) == removebg.EXIT_OK
    assert s.calls == 0


def test_max_calls_ceiling_aborts_before_any_call(images, tmp_path, stub):
    """The seatbelt: if the input set outgrew the approved plan, spend nothing."""
    s = stub("ok")
    assert removebg.main(run_args(images, tmp_path / "out", "--max-calls", "2")) == removebg.EXIT_ABORT
    assert s.calls == 0


def test_preview_is_four_times_cheaper_than_full():
    """The default exists because of this ratio — guard it against edits."""
    assert removebg.CREDIT_ESTIMATE["preview"] * 4 == removebg.CREDIT_ESTIMATE["full"]


def test_run_defaults_to_preview(images, tmp_path, stub):
    stub("ok")
    manifest = tmp_path / "r.json"
    removebg.main(run_args(images, tmp_path / "out", "--manifest", str(manifest)))
    assert json.loads(manifest.read_text())["params"]["size"] == "preview"


def test_api_key_is_not_a_cli_argument():
    """Keys on the command line leak into shell history and `ps` output."""
    proc = subprocess.run([sys.executable, SCRIPT, "run", "--help"],
                          capture_output=True, text=True, check=True,
                          encoding="utf-8", errors="replace")
    assert "--api-key " not in proc.stdout
    assert "--api-key-env" in proc.stdout
    assert "--api-key-file" in proc.stdout


# --------------------------------------------------------------------------
# Preflight, batching, reporting
# --------------------------------------------------------------------------

def test_zero_byte_file_is_skipped_without_calling(images, tmp_path, stub):
    s = stub("ok")
    manifest = tmp_path / "r.json"
    removebg.main(run_args(images, tmp_path / "out", "--manifest", str(manifest)))
    report = json.loads(manifest.read_text())
    assert s.calls == 3                      # a, b, c — not broken.png
    assert report["skipped"] == 1
    skipped = [r for r in report["results"] if r["status"] == "skipped"][0]
    assert "empty" in skipped["reason"]


def test_oversized_file_is_skipped_without_calling(tmp_path, stub):
    s = stub("ok")
    raw = tmp_path / "raw"
    raw.mkdir()
    big = raw / "huge.png"
    big.write_bytes(_png_bytes() + b"\x00" * (removebg.MAX_UPLOAD_BYTES + 1))
    assert removebg.main(run_args(raw, tmp_path / "out")) == removebg.EXIT_WARN
    assert s.calls == 0


def test_report_records_measured_credits_not_the_estimate(images, tmp_path, stub):
    """X-Credits-Charged is the truth; the estimate table is an approximation."""
    stub("partial", fail_on=2)
    manifest = tmp_path / "r.json"
    removebg.main(run_args(images, tmp_path / "out", "--manifest", str(manifest)))
    report = json.loads(manifest.read_text())
    assert report["estimated_credits_total"] == 0.75   # 3 planned × 0.25
    assert report["credits_charged_total"] == 0.5      # only 2 succeeded
    assert report["succeeded"] == 2 and report["failed"] == 1


def test_outputs_are_written(images, tmp_path, stub):
    stub("ok")
    out = tmp_path / "out"
    removebg.main(run_args(images, out))
    assert sorted(p.name for p in out.glob("*.png")) == ["a-nobg.png", "b-nobg.png", "c-nobg.png"]


def test_overwrite_reprocesses(images, tmp_path, stub):
    s = stub("ok")
    out = tmp_path / "out"
    removebg.main(run_args(images, out))
    assert removebg.main(run_args(images, out, "--overwrite")) == removebg.EXIT_OK
    assert s.calls == 6


def test_recursive_finds_nested_images(images, tmp_path, stub):
    s = stub("ok")
    nested = images / "sub"
    nested.mkdir()
    (nested / "d.png").write_bytes(_png_bytes())
    removebg.main(run_args(images, tmp_path / "out"))
    assert s.calls == 3
    s.calls = 0
    removebg.main(run_args(images, tmp_path / "out2", "--recursive"))
    assert s.calls == 4


def test_rate_limit_is_retried(tmp_path, stub):
    s = stub("429then200")
    raw = tmp_path / "raw"
    raw.mkdir()
    (raw / "a.png").write_bytes(_png_bytes())
    assert removebg.main(run_args(raw, tmp_path / "out")) == removebg.EXIT_OK
    assert s.calls == 3   # two 429s, then success


def test_retries_are_bounded(tmp_path, stub):
    """A 429 that outlasts the retry budget must fail, not loop forever."""
    s = stub("429then200")   # 429s on calls 1 and 2
    raw = tmp_path / "raw"
    raw.mkdir()
    (raw / "a.png").write_bytes(_png_bytes())
    # --retries 0 exhausts the budget on the first 429.
    assert removebg.main(run_args(raw, tmp_path / "out", "--retries", "0")) == removebg.EXIT_ABORT
    assert s.calls == 1      # no retry was attempted


# --------------------------------------------------------------------------
# account
# --------------------------------------------------------------------------

def test_account_reports_balance(stub, capsys):
    stub("ok")
    assert removebg.main(["account", "--json"]) == removebg.EXIT_OK
    info = json.loads(capsys.readouterr().out)
    assert info["total_credits"] == 42.5
    assert info["free_calls_remaining"] == 50


def test_account_never_prints_the_key(stub, capsys):
    stub("ok")
    removebg.main(["account"])
    assert "stub-key-0123456789" not in capsys.readouterr().out


def test_account_without_key_exits_3(monkeypatch):
    monkeypatch.delenv(removebg.DEFAULT_KEY_ENV, raising=False)
    assert removebg.main(["account"]) == removebg.EXIT_CANNOT_RUN
