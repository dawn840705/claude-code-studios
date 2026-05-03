#!/usr/bin/env python3
"""
Generic pay-as-you-go API CLI template.

Use this as the starting point for wrapping a new third-party AI service
(image / 3D / audio / video / text). The pattern handles:

  - .env auto-loading (project root + script dir)
  - Bearer / API-key header authentication
  - Async job submission + polling (record-info pattern)
  - Sync request/response (immediate binary or JSON)
  - File downloads from result URLs
  - Workshop output directory discipline
  - Subcommand-style CLI with argparse

Adopted services using this pattern in the wild:
  - Suno (sunoapi.org) — async, polling, multi-variant, stem separation
  - ElevenLabs — sync, binary audio response, voice library
  - Tripo3D — async, polling, 3D mesh + image
  - Generic OpenAI-style completion endpoints — sync JSON

Replace the placeholders marked with ⚠️ FIXME and customize.
Keeps the load_env / headers / _post / _get / _poll helpers.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Any

import requests  # python3 -m pip install requests

# ⚠️ FIXME — service base URL
API_BASE = "https://api.example.com"

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent  # adjust depth to your repo layout
OUTPUT_DIR = SCRIPT_DIR / "output"

POLL_INTERVAL_SEC = 6
POLL_TIMEOUT_SEC = 600


# ────────────────────────────────────────────
# Environment loading

def load_env() -> str:
    """Load .env from project root or script dir, return the API key."""
    for candidate in (PROJECT_ROOT / ".env", SCRIPT_DIR / ".env"):
        if candidate.exists():
            for line in candidate.read_text().splitlines():
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

    # ⚠️ FIXME — env var name (and any fallbacks for legacy spellings)
    key = (os.environ.get("EXAMPLE_API_KEY")
           or os.environ.get("EXAMPLE_API")
           or "").strip()
    if not key:
        sys.exit("EXAMPLE_API_KEY not set. Put it in .env or export it.")
    return key


# ────────────────────────────────────────────
# HTTP helpers

def headers(api_key: str, json_body: bool = True) -> dict[str, str]:
    """Build request headers. ⚠️ FIXME — choose Bearer vs custom header."""
    # Bearer style (most common):
    h = {"Authorization": f"Bearer {api_key}"}
    # OR custom header style (e.g. ElevenLabs uses xi-api-key):
    # h = {"xi-api-key": api_key}

    h["Accept"] = "application/json"
    if json_body:
        h["Content-Type"] = "application/json"
    return h


def _unwrap(r: requests.Response) -> dict[str, Any]:
    """Parse JSON, surface API errors clearly."""
    try:
        payload = r.json()
    except ValueError:
        sys.exit(f"non-JSON response ({r.status_code}): {r.text[:300]}")

    # ⚠️ FIXME — many APIs return {"code": <n>, "data": {...}} envelope.
    # Adjust to your service's error contract.
    code = payload.get("code")
    if r.status_code >= 400 or (code is not None and code != 200):
        sys.exit(f"API error ({r.status_code}, code={code}): "
                 f"{json.dumps(payload, ensure_ascii=False, indent=2)[:600]}")
    return payload.get("data", payload)


def _post(api_key: str, path: str, body: dict[str, Any]) -> dict[str, Any]:
    r = requests.post(f"{API_BASE}{path}", headers=headers(api_key),
                      json=body, timeout=60)
    return _unwrap(r)


def _get(api_key: str, path: str,
         params: dict[str, str] | None = None) -> dict[str, Any]:
    r = requests.get(f"{API_BASE}{path}",
                     headers=headers(api_key, json_body=False),
                     params=params, timeout=30)
    return _unwrap(r)


def _post_audio(api_key: str, path: str, body: dict[str, Any],
                params: dict[str, str] | None = None) -> bytes:
    """For endpoints that return binary (mp3 / png / etc) directly."""
    h = headers(api_key, json_body=True)
    h["Accept"] = "audio/mpeg"  # ⚠️ FIXME — adjust per response type
    r = requests.post(f"{API_BASE}{path}", headers=h, json=body,
                      params=params, timeout=300, stream=True)
    if r.status_code >= 400:
        try:
            err = r.json()
        except ValueError:
            err = {"raw": r.text[:300]}
        sys.exit(f"API error ({r.status_code}): "
                 f"{json.dumps(err, ensure_ascii=False, indent=2)[:600]}")
    return r.content


# ────────────────────────────────────────────
# Async polling pattern (skip if API is sync-only)

def _poll(api_key: str, path: str, task_id: str) -> dict[str, Any]:
    """Poll record-info endpoint until success / fail / timeout."""
    deadline = time.time() + POLL_TIMEOUT_SEC
    last_status = ""
    while time.time() < deadline:
        data = _get(api_key, path, params={"taskId": task_id})
        status = (data.get("status") or "").upper()
        if status != last_status:
            print(f"  [{time.strftime('%H:%M:%S')}] status={status}")
            last_status = status
        if status == "SUCCESS":
            return data
        # ⚠️ FIXME — adjust failure status set per service
        if status in ("FAIL", "ERROR", "TIMEOUT"):
            sys.exit(f"task failed: "
                     f"{json.dumps(data, ensure_ascii=False, indent=2)[:600]}")
        time.sleep(POLL_INTERVAL_SEC)
    sys.exit(f"timeout after {POLL_TIMEOUT_SEC}s. Re-run with: status {task_id}")


# ────────────────────────────────────────────
# File helpers

def _slugify(text: str, maxlen: int = 40) -> str:
    """Filesystem-safe slug."""
    s = re.sub(r"[^A-Za-z0-9가-힣\-_]+", "-", text).strip("-")
    return (s[:maxlen] or "untitled").lower()


def _download(url: str, dest: Path) -> None:
    """Stream a URL to disk."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    r = requests.get(url, stream=True, timeout=120)
    r.raise_for_status()
    with open(dest, "wb") as f:
        for chunk in r.iter_content(chunk_size=1 << 14):
            if chunk:
                f.write(chunk)
    print(f"  saved → {dest.relative_to(PROJECT_ROOT)}")


# ────────────────────────────────────────────
# Subcommands — ⚠️ FIXME — replace with your service's commands

def cmd_credits(args, api_key: str) -> None:
    """Free read-only call — verify API key and check balance."""
    data = _get(api_key, "/v1/credits")  # ⚠️ FIXME — actual path
    print(json.dumps(data, ensure_ascii=False, indent=2))


def cmd_generate(args, api_key: str) -> None:
    """Async job submission. Returns a task ID for polling."""
    body = {
        "prompt": args.prompt,
        # ⚠️ FIXME — required body fields
    }
    data = _post(api_key, "/v1/generate", body)
    task_id = data.get("taskId")
    print(f"taskId: {task_id}")
    print(f"→ python {Path(sys.argv[0]).name} status {task_id}")


def cmd_status(args, api_key: str) -> None:
    """Poll until success."""
    data = _poll(api_key, "/v1/generate/record-info", args.task_id)
    print(json.dumps(data, ensure_ascii=False, indent=2)[:1000])


# ────────────────────────────────────────────
# Argparse — ⚠️ FIXME — adjust subcommand names + flags

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="example", description="Example API CLI")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("credits", help="Check API balance")

    g = sub.add_parser("generate", help="Submit a generation job")
    g.add_argument("prompt")

    s = sub.add_parser("status", help="Poll job status")
    s.add_argument("task_id")

    return p


COMMANDS = {
    "credits": cmd_credits,
    "generate": cmd_generate,
    "status": cmd_status,
}


def main() -> None:
    args = build_parser().parse_args()
    api_key = load_env()
    COMMANDS[args.cmd](args, api_key)


if __name__ == "__main__":
    main()


# ────────────────────────────────────────────
# Adoption checklist
#
#   [ ] Replace API_BASE
#   [ ] Replace EXAMPLE_API_KEY env var name (+ fallbacks if needed)
#   [ ] Choose auth header (Authorization: Bearer  vs  custom)
#   [ ] Adjust _unwrap() to your service's error envelope
#   [ ] Replace subcommands (credits / generate / status / etc.)
#   [ ] Adjust POLL_INTERVAL_SEC / POLL_TIMEOUT_SEC if needed
#   [ ] Add OUTPUT_DIR to .gitignore (it's a workshop, not production)
#   [ ] Document costs in your project's api-cost-log.md
#   [ ] Wire to /api-cost-gate before any generate calls
