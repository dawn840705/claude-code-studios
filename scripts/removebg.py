#!/usr/bin/env python3
"""remove.bg 배경 제거 CLI — 결정적 게이트 (LLM 콜 0).

`/remove-bg` 스킬의 실행부. 스킬은 비용 공시와 매니페스트 서술을 맡고,
과금·호출·판정은 전부 이 스크립트가 한다. **판정은 종료 코드가 내린다** —
에이전트가 stdout을 파싱해 성공 여부를 재해석하면 안 된다.

  API 문서: https://www.remove.bg/api
  엔드포인트: POST https://api.remove.bg/v1.0/removebg
             GET  https://api.remove.bg/v1.0/account

표준 라이브러리만 사용한다 (urllib / json / argparse). 서드파티 의존 없음.

서브커맨드:
    account                       잔여 크레딧 조회
    estimate  <입력...>           호출 없이 크레딧 추정만 (= run --dry-run)
    run       <입력...>           실제 배경 제거

사용 예:
    export REMOVE_BG_API_KEY=xxxx
    python3 scripts/removebg.py account
    python3 scripts/removebg.py estimate assets/raw/ --size preview
    python3 scripts/removebg.py run assets/raw/hero.png --out assets/cutout/
    python3 scripts/removebg.py run assets/raw/ --out assets/cutout/ \
        --size preview --type product --format png \
        --manifest assets/cutout/removebg-report.json

Exit code (docs/deterministic-gates.md 계약):
    0 — 전 건 성공 (또는 dry-run 이 정상 완료)
    1 — 경고: 일부 성공 / 일부 실패, 혹은 전 건 스킵
    2 — 중단: 전 건 실패, 인증 실패(403), 크레딧 부족(402), 사전 검증 탈락
    3 — 실행 불가: API 키 없음, 입력 경로 없음, 잘못된 인자 — **판정 없음**
        (3 을 통과로 읽지 말 것: 게이트가 돌지 못했다는 뜻이다.)
"""

from __future__ import annotations

import argparse
import json
import mimetypes
import os
import sys
import time
import urllib.error
import urllib.request
import uuid

API_BASE = "https://api.remove.bg/v1.0"
ENDPOINT_REMOVEBG = f"{API_BASE}/removebg"
ENDPOINT_ACCOUNT = f"{API_BASE}/account"

DEFAULT_KEY_ENV = "REMOVE_BG_API_KEY"

# 업로드 상한 (remove.bg 사이트 config: max_file_size_limit_mb = 22)
MAX_UPLOAD_BYTES = 22 * 1024 * 1024

IMAGE_EXTS = (".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff")

# 크레딧 추정 표 — **추정치이며 요금제/정책 변경에 따라 달라진다.**
# 확정 과금액은 응답 헤더 X-Credits-Charged 가 유일한 진실이고, run 은 그
# 실측값을 리포트에 기록한다. 추정표는 사전 승인(4점 공시)용으로만 쓴다.
#   preview / small / regular : 최대 0.25MP  → 0.25 크레딧
#   그 외 (auto/medium/hd/full/4k)          → 1 크레딧
CREDIT_ESTIMATE = {
    "preview": 0.25,
    "small": 0.25,
    "regular": 0.25,
    "auto": 1.0,
    "medium": 1.0,
    "hd": 1.0,
    "full": 1.0,
    "4k": 1.0,
}

SIZE_CHOICES = tuple(CREDIT_ESTIMATE)
TYPE_CHOICES = ("auto", "person", "product", "animal", "car", "transportation", "graphics", "other")
TYPE_LEVEL_CHOICES = ("none", "1", "2", "latest")
FORMAT_CHOICES = ("auto", "png", "jpg", "zip")
CHANNEL_CHOICES = ("rgba", "alpha")
POSITION_HINT = "center | original | 'X%% Y%%'"   # argparse help 용 — %% 는 리터럴 %

EXT_BY_FORMAT = {"png": ".png", "jpg": ".jpg", "zip": ".zip"}


# --------------------------------------------------------------------------
# 종료 코드
# --------------------------------------------------------------------------

EXIT_OK = 0
EXIT_WARN = 1
EXIT_ABORT = 2
EXIT_CANNOT_RUN = 3


class CannotRun(Exception):
    """게이트를 실행할 수 없는 상태 — exit 3. 통과가 아니다."""


class Abort(Exception):
    """호출은 했으나 계속하면 안 되는 상태 (인증/크레딧) — exit 2."""


# --------------------------------------------------------------------------
# 인증
# --------------------------------------------------------------------------

def load_api_key(env_name: str, key_file: str | None) -> str:
    """API 키를 환경변수 또는 파일에서 읽는다.

    CLI 인자로는 절대 받지 않는다 — 셸 히스토리와 프로세스 목록에 남는다.
    """
    if key_file:
        if not os.path.isfile(key_file):
            raise CannotRun(f"API key file not found: {key_file}")
        key = open(key_file, encoding="utf-8").read().strip()
        if not key:
            raise CannotRun(f"API key file is empty: {key_file}")
        return key
    key = os.environ.get(env_name, "").strip()
    if not key:
        raise CannotRun(
            f"no API key: environment variable {env_name} is unset or empty.\n"
            f"  export {env_name}=<your key>   # https://www.remove.bg/dashboard#api-key\n"
            f"  또는 --api-key-file <path> 사용"
        )
    return key


def redact(key: str) -> str:
    return f"{key[:4]}…{key[-2:]}" if len(key) > 8 else "…"


# --------------------------------------------------------------------------
# HTTP
# --------------------------------------------------------------------------

def encode_multipart(fields: dict[str, str], files: dict[str, tuple[str, bytes]]) -> tuple[bytes, str]:
    """multipart/form-data 본문을 만든다. 반환: (body, content_type)."""
    boundary = f"----removebg{uuid.uuid4().hex}"
    out = bytearray()
    for name, value in fields.items():
        out += f"--{boundary}\r\n".encode()
        out += f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode()
        out += f"{value}\r\n".encode()
    for name, (filename, blob) in files.items():
        ctype = mimetypes.guess_type(filename)[0] or "application/octet-stream"
        out += f"--{boundary}\r\n".encode()
        out += (
            f'Content-Disposition: form-data; name="{name}"; filename="{os.path.basename(filename)}"\r\n'
        ).encode()
        out += f"Content-Type: {ctype}\r\n\r\n".encode()
        out += blob + b"\r\n"
    out += f"--{boundary}--\r\n".encode()
    return bytes(out), f"multipart/form-data; boundary={boundary}"


def http_call(url: str, api_key: str, *, body: bytes | None = None,
              content_type: str | None = None, timeout: int = 120):
    """반환: (status, headers dict, payload bytes). HTTPError 도 정상 반환한다."""
    req = urllib.request.Request(url, data=body, method="POST" if body else "GET")
    req.add_header("X-Api-Key", api_key)
    req.add_header("Accept", "application/json")
    if content_type:
        req.add_header("Content-Type", content_type)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, dict(resp.headers), resp.read()
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers or {}), e.read()
    except urllib.error.URLError as e:
        raise CannotRun(f"network error calling {url}: {e.reason}") from e


def parse_api_errors(payload: bytes) -> str:
    """remove.bg 오류 본문 {"errors":[{"title":...,"code":...}]} 를 한 줄로."""
    try:
        data = json.loads(payload.decode("utf-8", "replace"))
    except (ValueError, UnicodeDecodeError):
        return payload[:200].decode("utf-8", "replace").strip() or "(no error body)"
    errs = data.get("errors") or []
    parts = []
    for e in errs:
        title = e.get("title") or "unknown error"
        code = e.get("code")
        parts.append(f"{title} [{code}]" if code else title)
    return "; ".join(parts) or "(no error body)"


# --------------------------------------------------------------------------
# account
# --------------------------------------------------------------------------

def fetch_account(api_key: str) -> dict:
    status, _, payload = http_call(ENDPOINT_ACCOUNT, api_key)
    if status == 403:
        raise Abort(f"authentication failed (403): {parse_api_errors(payload)}")
    if status != 200:
        raise Abort(f"account lookup failed ({status}): {parse_api_errors(payload)}")
    try:
        data = json.loads(payload.decode("utf-8"))
    except (ValueError, UnicodeDecodeError) as e:
        raise Abort(f"account response was not JSON: {e}") from e
    attrs = (data.get("data") or {}).get("attributes") or {}
    credits = attrs.get("credits") or {}
    api = attrs.get("api") or {}
    return {
        "total_credits": credits.get("total"),
        "subscription_credits": credits.get("subscription"),
        "payg_credits": credits.get("payasyougo"),
        "enterprise_credits": credits.get("enterprise"),
        "free_calls_remaining": api.get("free_calls"),
        "sizes_allowed": api.get("sizes"),
    }


# --------------------------------------------------------------------------
# 입력 수집 + 사전 검증
# --------------------------------------------------------------------------

def is_url(s: str) -> bool:
    return s.startswith("http://") or s.startswith("https://")


def collect_inputs(targets: list[str], recursive: bool) -> list[str]:
    """파일 / 디렉터리 / URL 을 평평한 입력 목록으로 편다."""
    found: list[str] = []
    for t in targets:
        if is_url(t):
            found.append(t)
            continue
        if os.path.isfile(t):
            found.append(t)
            continue
        if os.path.isdir(t):
            if recursive:
                for root, _, names in os.walk(t):
                    found += [
                        os.path.join(root, n) for n in sorted(names)
                        if n.lower().endswith(IMAGE_EXTS)
                    ]
            else:
                found += [
                    os.path.join(t, n) for n in sorted(os.listdir(t))
                    if n.lower().endswith(IMAGE_EXTS)
                    and os.path.isfile(os.path.join(t, n))
                ]
            continue
        raise CannotRun(f"input path does not exist: {t}")
    # 중복 제거 (순서 유지)
    return list(dict.fromkeys(found))


def output_path(src: str, out_dir: str, fmt: str, suffix: str) -> str:
    if is_url(src):
        stem = os.path.splitext(os.path.basename(src.split("?")[0]))[0] or "image"
    else:
        stem = os.path.splitext(os.path.basename(src))[0]
    ext = EXT_BY_FORMAT.get(fmt, ".png")  # format=auto 는 PNG/JPG 중 선택되지만
    return os.path.join(out_dir, f"{stem}{suffix}{ext}")  # 확장자는 PNG 로 고정 저장


def preflight(src: str) -> str | None:
    """호출 전에 결정적으로 걸러낼 수 있는 문제. 통과면 None."""
    if is_url(src):
        return None
    if not os.path.isfile(src):
        return "file disappeared before upload"
    size = os.path.getsize(src)
    if size == 0:
        return "file is empty (0 bytes)"
    if size > MAX_UPLOAD_BYTES:
        return f"file is {size / 1048576:.1f}MB, over the {MAX_UPLOAD_BYTES // 1048576}MB upload limit"
    return None


# --------------------------------------------------------------------------
# 호출 파라미터
# --------------------------------------------------------------------------

def build_fields(args) -> dict[str, str]:
    fields: dict[str, str] = {
        "size": args.size,
        "type": args.type,
        "format": args.format,
        "channels": args.channels,
    }
    if args.type_level != "auto":
        fields["type_level"] = args.type_level
    if args.bg_color:
        fields["bg_color"] = args.bg_color
    if args.bg_image_url:
        fields["bg_image_url"] = args.bg_image_url
    if args.roi:
        fields["roi"] = args.roi
    if args.crop:
        fields["crop"] = "true"
        if args.crop_margin:
            fields["crop_margin"] = args.crop_margin
    if args.scale:
        fields["scale"] = args.scale
    if args.position:
        fields["position"] = args.position
    if args.add_shadow:
        fields["add_shadow"] = "true"
    if args.no_semitransparency:
        fields["semitransparency"] = "false"
    return fields


# --------------------------------------------------------------------------
# 단건 처리
# --------------------------------------------------------------------------

def remove_one(src: str, dst: str, api_key: str, fields: dict[str, str],
               *, retries: int, timeout: int) -> dict:
    """1장 처리. 반환 레코드에는 항상 status 키가 있다."""
    rec: dict = {"input": src, "output": dst, "status": "failed", "credits_charged": None}

    problem = preflight(src)
    if problem:
        rec.update(status="skipped", reason=problem, billable=False)
        return rec

    call_fields = dict(fields)
    files: dict[str, tuple[str, bytes]] = {}
    if is_url(src):
        call_fields["image_url"] = src
    else:
        with open(src, "rb") as fh:
            files["image_file"] = (src, fh.read())

    attempt = 0
    while True:
        attempt += 1
        body, ctype = encode_multipart(call_fields, files)
        status, headers, payload = http_call(
            ENDPOINT_REMOVEBG, api_key, body=body, content_type=ctype, timeout=timeout
        )

        if status == 200:
            os.makedirs(os.path.dirname(os.path.abspath(dst)), exist_ok=True)
            with open(dst, "wb") as fh:
                fh.write(payload)
            charged = headers.get("X-Credits-Charged")
            rec.update(
                status="ok",
                billable=True,
                bytes=len(payload),
                credits_charged=float(charged) if charged else None,
                width=headers.get("X-Width"),
                height=headers.get("X-Height"),
                detected_type=headers.get("X-Type"),
            )
            return rec

        # 402 / 403 은 배치 전체를 세운다 — 나머지를 계속 쏘면 손해만 커진다.
        if status == 402:
            raise Abort(f"insufficient credits (402): {parse_api_errors(payload)}")
        if status == 403:
            raise Abort(f"authentication failed (403): {parse_api_errors(payload)}")

        if status == 429 and attempt <= retries:
            wait = int(headers.get("Retry-After") or 0) or min(2 ** attempt, 60)
            time.sleep(wait)
            continue

        rec.update(
            status="failed",
            billable=False,
            http_status=status,
            reason=parse_api_errors(payload),
        )
        return rec


# --------------------------------------------------------------------------
# 서브커맨드
# --------------------------------------------------------------------------

def cmd_account(args) -> int:
    api_key = load_api_key(args.api_key_env, args.api_key_file)
    info = fetch_account(api_key)
    if args.json:
        print(json.dumps(info, indent=2, ensure_ascii=False))
    else:
        print(f"remove.bg account (key {redact(api_key)})")
        print(f"  total credits        : {info['total_credits']}")
        print(f"  ├ subscription       : {info['subscription_credits']}")
        print(f"  ├ pay-as-you-go      : {info['payg_credits']}")
        print(f"  └ enterprise         : {info['enterprise_credits']}")
        print(f"  free preview calls   : {info['free_calls_remaining']}")
        print(f"  sizes allowed        : {info['sizes_allowed']}")
    return EXIT_OK


def build_plan(args) -> dict:
    """호출 없이 계산할 수 있는 전부 — 4점 공시의 '비용 추정' 근거."""
    inputs = collect_inputs(args.input, args.recursive)
    if not inputs:
        raise CannotRun(
            f"no images found in {args.input} "
            f"(looked for {', '.join(IMAGE_EXTS)}{'; use --recursive for subfolders' if not args.recursive else ''})"
        )

    per_image = CREDIT_ESTIMATE[args.size]
    items, billable = [], 0
    for src in inputs:
        dst = output_path(src, args.out, args.format, args.suffix)
        problem = preflight(src)
        if problem:
            items.append({"input": src, "output": dst, "action": "skip", "reason": problem})
            continue
        if os.path.exists(dst) and not args.overwrite:
            items.append({
                "input": src, "output": dst, "action": "skip",
                "reason": "output already exists (use --overwrite to replace)",
            })
            continue
        items.append({"input": src, "output": dst, "action": "call",
                      "estimated_credits": per_image})
        billable += 1

    return {
        "endpoint": ENDPOINT_REMOVEBG,
        "params": build_fields(args),
        "output_dir": args.out,
        "inputs_found": len(inputs),
        "billable_calls": billable,
        "skipped": len(inputs) - billable,
        "credits_per_image_estimate": per_image,
        "estimated_credits_total": round(billable * per_image, 4),
        "estimate_note": (
            "추정치다. 확정 과금액은 응답 헤더 X-Credits-Charged 를 따르며 "
            "run 결과 리포트의 credits_charged_total 이 실측값이다."
        ),
        "items": items,
    }


def cmd_estimate(args) -> int:
    plan = build_plan(args)
    if args.check_balance:
        api_key = load_api_key(args.api_key_env, args.api_key_file)
        plan["account"] = fetch_account(api_key)
    if args.json:
        print(json.dumps(plan, indent=2, ensure_ascii=False))
    else:
        print("=== remove.bg — dry run (호출 없음) ===")
        print(f"  images found     : {plan['inputs_found']}")
        print(f"  billable calls   : {plan['billable_calls']}  (skipped {plan['skipped']})")
        print(f"  size / type      : {args.size} / {args.type}")
        print(f"  est. credits     : ~{plan['estimated_credits_total']} "
              f"({plan['credits_per_image_estimate']}/image, 추정)")
        print(f"  output dir       : {plan['output_dir']}")
        if "account" in plan:
            print(f"  current balance  : {plan['account']['total_credits']} credits, "
                  f"{plan['account']['free_calls_remaining']} free preview calls")
        for it in plan["items"][:20]:
            mark = "→" if it["action"] == "call" else "·"
            note = "" if it["action"] == "call" else f"  ({it['reason']})"
            print(f"    {mark} {it['input']}{note}")
        if len(plan["items"]) > 20:
            print(f"    … and {len(plan['items']) - 20} more")
    if args.manifest:
        write_manifest(args.manifest, plan)
    return EXIT_OK


def write_manifest(path: str, data: dict) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False)


def cmd_run(args) -> int:
    if args.dry_run:
        return cmd_estimate(args)

    plan = build_plan(args)
    api_key = load_api_key(args.api_key_env, args.api_key_file)
    fields = build_fields(args)

    if args.max_calls is not None and plan["billable_calls"] > args.max_calls:
        raise Abort(
            f"plan needs {plan['billable_calls']} billable calls but --max-calls is "
            f"{args.max_calls}. 예상 밖의 과금을 막기 위해 중단한다."
        )

    records: list[dict] = []
    aborted: str | None = None
    for it in plan["items"]:
        if it["action"] == "skip":
            records.append({"input": it["input"], "output": it["output"],
                            "status": "skipped", "reason": it["reason"],
                            "billable": False, "credits_charged": None})
            continue
        try:
            rec = remove_one(it["input"], it["output"], api_key, fields,
                             retries=args.retries, timeout=args.timeout)
        except Abort as e:
            aborted = str(e)
            break
        records.append(rec)
        if not args.quiet:
            mark = {"ok": "✓", "skipped": "·", "failed": "✗"}[rec["status"]]
            tail = f"  ({rec.get('reason')})" if rec["status"] != "ok" else \
                   f"  [{rec.get('credits_charged')} credits]"
            print(f"  {mark} {rec['input']} → {rec['output']}{tail}", flush=True)
        if args.sleep:
            time.sleep(args.sleep)

    ok = sum(1 for r in records if r["status"] == "ok")
    failed = sum(1 for r in records if r["status"] == "failed")
    skipped = sum(1 for r in records if r["status"] == "skipped")
    charged = round(sum(r.get("credits_charged") or 0 for r in records), 4)

    report = {
        "endpoint": ENDPOINT_REMOVEBG,
        "params": fields,
        "output_dir": args.out,
        "planned_billable_calls": plan["billable_calls"],
        "estimated_credits_total": plan["estimated_credits_total"],
        "credits_charged_total": charged,
        "succeeded": ok,
        "failed": failed,
        "skipped": skipped,
        "aborted": aborted,
        "results": records,
    }
    if args.manifest:
        write_manifest(args.manifest, report)

    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print("\n=== remove.bg — result ===")
        print(f"  succeeded {ok} · failed {failed} · skipped {skipped}")
        print(f"  credits charged (실측) : {charged}   (estimate was ~{plan['estimated_credits_total']})")
        if args.manifest:
            print(f"  report                 : {args.manifest}")
        if aborted:
            print(f"  ABORTED: {aborted}")

    if aborted:
        raise Abort(aborted)
    if failed and ok:
        return EXIT_WARN            # 부분 실패 = 경고
    if failed and not ok:
        return EXIT_ABORT           # 전 건 실패 = 중단
    if not ok and skipped:
        return EXIT_WARN            # 아무것도 처리 못 함 (전부 스킵)
    return EXIT_OK


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------

def add_auth_args(p: argparse.ArgumentParser) -> None:
    p.add_argument("--api-key-env", default=DEFAULT_KEY_ENV,
                   help=f"API 키를 담은 환경변수 이름 (기본 {DEFAULT_KEY_ENV})")
    p.add_argument("--api-key-file", help="API 키가 든 파일 경로 (환경변수보다 우선)")
    p.add_argument("--json", action="store_true", help="JSON 으로 출력")


def add_call_args(p: argparse.ArgumentParser) -> None:
    p.add_argument("input", nargs="+", help="이미지 파일 / 디렉터리 / http(s) URL")
    p.add_argument("--out", default="out", help="출력 디렉터리 (기본 out/)")
    p.add_argument("--suffix", default="-nobg", help="출력 파일명 접미사 (기본 -nobg)")
    p.add_argument("--recursive", action="store_true", help="디렉터리를 재귀 탐색")
    p.add_argument("--overwrite", action="store_true", help="기존 출력 파일 덮어쓰기")
    p.add_argument("--manifest", help="결과 리포트를 쓸 JSON 경로")

    p.add_argument("--size", default="preview", choices=SIZE_CHOICES,
                   help="출력 해상도. preview(≈0.25 크레딧) / full 등(≈1 크레딧). 기본 preview")
    p.add_argument("--type", default="auto", choices=TYPE_CHOICES, help="피사체 종류 (기본 auto)")
    p.add_argument("--type-level", default="auto", choices=("auto",) + TYPE_LEVEL_CHOICES,
                   help="분류 상세도 (기본 auto = 파라미터 미전송)")
    p.add_argument("--format", default="png", choices=FORMAT_CHOICES, help="출력 포맷 (기본 png)")
    p.add_argument("--channels", default="rgba", choices=CHANNEL_CHOICES,
                   help="rgba = 잘라낸 이미지, alpha = 마스크만 (기본 rgba)")
    p.add_argument("--bg-color", help="배경색 (예: 81d4fa, red, #81d4fa77)")
    p.add_argument("--bg-image-url", help="배경으로 합성할 이미지 URL")
    # argparse 는 help 문자열에 %% 서식을 적용한다 — 리터럴 %는 반드시 %% 로 쓴다.
    p.add_argument("--roi", help="관심 영역 (예: '0%% 0%% 100%% 100%%' 또는 '10px 20px 300px 400px')")
    p.add_argument("--crop", action="store_true", help="피사체 경계로 잘라내기")
    p.add_argument("--crop-margin", help="crop 여백 (예: 10px, 5%%) — --crop 과 함께")
    p.add_argument("--scale", help="피사체 크기 비율 (예: 80%%)")
    p.add_argument("--position", default=None, help=f"피사체 위치: {POSITION_HINT}")
    p.add_argument("--add-shadow", action="store_true", help="그림자 추가 (car/product 지원)")
    p.add_argument("--no-semitransparency", action="store_true",
                   help="반투명 영역 처리 끄기 (기본은 켜짐)")


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(
        prog="removebg.py",
        description="remove.bg 배경 제거 — 결정적 CLI (exit code 가 판정이다)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="exit: 0 성공 · 1 부분 실패/전량 스킵 · 2 중단 · 3 실행 불가(판정 없음)",
    )
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_acc = sub.add_parser("account", help="잔여 크레딧 조회")
    add_auth_args(p_acc)
    p_acc.set_defaults(func=cmd_account)

    p_est = sub.add_parser("estimate", help="호출 없이 크레딧 추정")
    add_auth_args(p_est)
    add_call_args(p_est)
    p_est.add_argument("--check-balance", action="store_true",
                       help="account 를 조회해 현재 잔액도 함께 표시 (과금 없음)")
    p_est.set_defaults(func=cmd_estimate)

    p_run = sub.add_parser("run", help="배경 제거 실행 (과금 발생)")
    add_auth_args(p_run)
    add_call_args(p_run)
    p_run.add_argument("--dry-run", action="store_true", help="estimate 와 동일 — 호출하지 않는다")
    p_run.add_argument("--max-calls", type=int,
                       help="과금 호출 상한. 계획이 이를 넘으면 exit 2 로 중단")
    p_run.add_argument("--retries", type=int, default=3, help="429 재시도 횟수 (기본 3)")
    p_run.add_argument("--sleep", type=float, default=0.0, help="호출 간 대기 초 (기본 0)")
    p_run.add_argument("--timeout", type=int, default=120, help="요청 타임아웃 초 (기본 120)")
    p_run.add_argument("--quiet", action="store_true", help="건별 진행 출력 끄기")
    p_run.add_argument("--check-balance", action="store_true", help=argparse.SUPPRESS)
    p_run.set_defaults(func=cmd_run)

    args = ap.parse_args(argv)

    try:
        return args.func(args)
    except CannotRun as e:
        print(f"removebg: cannot run — {e}", file=sys.stderr)
        print("removebg: exit 3 = 게이트 실행 불가. 통과로 읽지 말 것.", file=sys.stderr)
        return EXIT_CANNOT_RUN
    except Abort as e:
        print(f"removebg: ABORT — {e}", file=sys.stderr)
        return EXIT_ABORT
    except KeyboardInterrupt:
        print("removebg: interrupted", file=sys.stderr)
        return EXIT_ABORT


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
