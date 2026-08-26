#!/usr/bin/env python3
"""doc_relink.py — markdown link integrity for documentation reorganizations.

Two subcommands, exit code is the verdict (deterministic gate):

  check  ROOT [--docs DIR] [--extra PATH ...] [--baseline F] [--write-baseline F]
      Scan markdown files and report relative links whose target does not
      exist. With --baseline, exit 1 only when NEW breaks appear beyond the
      baseline (pre-existing rot does not fail the gate).

  relink ROOT [--docs DIR] [--extra PATH ...] [--dry-run]
      Run AFTER `git mv` while the renames are still STAGED and UNCOMMITTED.
      Reads git's rename map (`git diff --cached --name-status -M`) and
      rewrites links in two passes:
        pass 1 — inbound: links in any scanned file that pointed at a moved
                 file are re-aimed at its new location;
        pass 2 — outbound: links FROM moved markdown files whose directory
                 depth changed are recomputed against their old location.
      Links that were already broken before the move are left untouched —
      this tool never invents targets.

Exit codes: 0 = pass / 1 = gate failed (new breaks) / 2 = usage or env error.

Known limits (by design, documented in the doc-relink skill):
  - Only inline links `](target)` are handled; angle-bracket links
    `](<path with spaces>)` and reference-style links are not rewritten.
  - Files git does not track (gitignored assets moved by hand) never appear
    in the rename map; fix those references manually.

Standard library only.
"""
from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
import urllib.parse

_CONSOLE_DIR = os.path.dirname(os.path.abspath(__file__))
if _CONSOLE_DIR not in sys.path:
    sys.path.insert(0, _CONSOLE_DIR)
from console_encoding import force_utf8  # noqa: E402

LINK_RE = re.compile(r"\]\(([^)\s#]+)(#[^)]*)?\)")
CHECKED_EXT = re.compile(
    r"\.(md|markdown|html?|png|jpe?g|webp|gif|svg|csv|tsv|pdf|txt|sh|py|cs|json"
    r"|ya?ml|xml|inputactions|xlsx?|mp3|wav|ogg|mp4)$",
    re.I,
)
SKIP_PREFIX = ("http://", "https://", "mailto:", "file://", "tel:", "data:")
QUOTE_SAFE = "/-_.~()!,'&+@="


def iter_markdown(docs_root: str, extras: list[str]):
    for dirpath, _dirnames, filenames in os.walk(docs_root):
        for fn in filenames:
            if fn.lower().endswith((".md", ".markdown")):
                yield os.path.join(dirpath, fn)
    for extra in extras:
        if os.path.isdir(extra):
            for dirpath, _dirnames, filenames in os.walk(extra):
                for fn in filenames:
                    if fn.lower().endswith((".md", ".markdown")):
                        yield os.path.join(dirpath, fn)
        elif os.path.isfile(extra):
            yield extra


def read_text(path: str):
    try:
        with open(path, encoding="utf-8", newline="") as f:
            return f.read()
    except (OSError, UnicodeDecodeError):
        return None


def scan_broken(root: str, docs_root: str, extras: list[str]):
    """Yield (relpath, raw_target) for every relative link that does not resolve."""
    for fpath in iter_markdown(docs_root, extras):
        text = read_text(fpath)
        if text is None:
            continue
        dirpath = os.path.dirname(fpath)
        for m in LINK_RE.finditer(text):
            raw = m.group(1)
            if raw.startswith(SKIP_PREFIX):
                continue
            target = urllib.parse.unquote(raw)
            if target.endswith("/"):
                cand = os.path.normpath(os.path.join(dirpath, target))
                if not os.path.isdir(cand):
                    yield os.path.relpath(fpath, root), raw
                continue
            if not CHECKED_EXT.search(target):
                continue
            cand = os.path.normpath(os.path.join(dirpath, target))
            if not os.path.exists(cand):
                yield os.path.relpath(fpath, root), raw


def rename_map(root: str):
    """Staged renames as {old_abs_lower: new_abs} plus ordered (old, new) pairs."""
    try:
        out = subprocess.run(
            ["git", "-C", root, "diff", "--cached", "--name-status", "-M"],
            capture_output=True, text=True, encoding="utf-8", check=True,
        ).stdout
    except (subprocess.CalledProcessError, FileNotFoundError) as exc:
        print(f"error: cannot read staged renames from git: {exc}", file=sys.stderr)
        sys.exit(2)
    pairs = []
    lookup = {}
    for line in out.splitlines():
        parts = line.split("\t")
        if parts[0].startswith("R") and len(parts) == 3:
            old = os.path.normpath(os.path.join(root, parts[1]))
            new = os.path.normpath(os.path.join(root, parts[2]))
            pairs.append((old, new))
            lookup[old.lower()] = new
    return lookup, pairs


def rewrite(fpath: str, edits: list[tuple[str, str]], dry: bool):
    text = read_text(fpath)
    if text is None:
        return 0
    for old, new in edits:
        text = text.replace("(" + old, "(" + new)
    if not dry:
        with open(fpath, "w", encoding="utf-8", newline="") as f:
            f.write(text)
    return len(edits)


def cmd_check(args) -> int:
    root = os.path.abspath(args.root)
    docs = os.path.join(root, args.docs)
    broken = sorted(set(scan_broken(root, docs, [os.path.join(root, e) for e in args.extra])))
    lines = [f"{src}\t{tgt}" for src, tgt in broken]
    print(f"broken={len(broken)}")
    if args.write_baseline:
        with open(args.write_baseline, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + ("\n" if lines else ""))
        print(f"baseline written: {args.write_baseline}")
        return 0
    if args.baseline:
        try:
            with open(args.baseline, encoding="utf-8") as f:
                base = {ln.rstrip("\n") for ln in f if ln.strip()}
        except OSError as exc:
            print(f"error: cannot read baseline: {exc}", file=sys.stderr)
            return 2
        # A break survives a move: same target, source path changed. Compare by
        # (source basename, target) as well so relocated-but-identical rot does
        # not fail the gate.
        base_loose = {(os.path.basename(ln.split("\t")[0]), ln.split("\t")[1]) for ln in base if "\t" in ln}
        new = [ln for ln in lines
               if ln not in base
               and (os.path.basename(ln.split("\t")[0]), ln.split("\t")[1]) not in base_loose]
        if new:
            print(f"NEW breaks vs baseline: {len(new)}")
            for ln in new:
                print("  " + ln)
            return 1
        print("no new breaks vs baseline")
    else:
        for ln in lines:
            print("  " + ln)
    return 0


def cmd_relink(args) -> int:
    root = os.path.abspath(args.root)
    docs = os.path.join(root, args.docs)
    extras = [os.path.join(root, e) for e in args.extra]
    lookup, pairs = rename_map(root)
    print(f"rename map entries: {len(pairs)}")
    if not pairs:
        print("nothing staged as renamed — run after `git mv`, before commit", file=sys.stderr)
        return 2

    files_changed = links_changed = 0

    # pass 1 — inbound
    for fpath in iter_markdown(docs, extras):
        text = read_text(fpath)
        if text is None:
            continue
        dirpath = os.path.dirname(fpath)
        edits = []
        for m in LINK_RE.finditer(text):
            raw = m.group(1)
            if raw.startswith(SKIP_PREFIX):
                continue
            resolved = os.path.normpath(os.path.join(dirpath, urllib.parse.unquote(raw))).lower()
            if resolved in lookup:
                newrel = os.path.relpath(lookup[resolved], dirpath).replace("\\", "/")
                edits.append((raw, urllib.parse.quote(newrel, safe=QUOTE_SAFE)))
        if edits:
            n = rewrite(fpath, edits, args.dry_run)
            files_changed += 1
            links_changed += n
            print(f"  inbound  {os.path.relpath(fpath, root)}: {n}")

    # pass 2 — outbound from moved markdown files
    for oldabs, newabs in pairs:
        if not newabs.lower().endswith((".md", ".markdown")) or not os.path.exists(newabs):
            continue
        olddir, newdir = os.path.dirname(oldabs), os.path.dirname(newabs)
        if olddir == newdir:
            continue
        text = read_text(newabs)
        if text is None:
            continue
        edits = []
        for m in LINK_RE.finditer(text):
            raw = m.group(1)
            if raw.startswith(SKIP_PREFIX):
                continue
            target = urllib.parse.unquote(raw)
            if os.path.exists(os.path.normpath(os.path.join(newdir, target))):
                continue  # already resolves from the new home (sibling moved along)
            old_resolved = os.path.normpath(os.path.join(olddir, target))
            dest = lookup.get(old_resolved.lower(),
                              old_resolved if os.path.exists(old_resolved) else None)
            if dest is None:
                continue  # was broken before the move — not ours to invent
            newrel = os.path.relpath(dest, newdir).replace("\\", "/")
            edits.append((raw, urllib.parse.quote(newrel, safe=QUOTE_SAFE)))
        if edits:
            n = rewrite(newabs, edits, args.dry_run)
            files_changed += 1
            links_changed += n
            print(f"  outbound {os.path.relpath(newabs, root)}: {n}")

    verb = "would rewrite" if args.dry_run else "rewrote"
    print(f"{verb} {links_changed} links across {files_changed} files")
    return 0


def main() -> int:
    force_utf8()  # 판정이 콘솔 코드페이지에 좌우되지 않게 (console_encoding 참조)
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)

    def common(p):
        p.add_argument("root", help="repository root")
        p.add_argument("--docs", default="Documents",
                       help="docs directory relative to root (default: Documents)")
        p.add_argument("--extra", action="append", default=[],
                       help="extra file or directory (relative to root) to scan, repeatable "
                            "(e.g. CLAUDE.md, .claude/commands)")

    p_check = sub.add_parser("check", help="report broken relative links")
    common(p_check)
    p_check.add_argument("--baseline", help="baseline file; exit 1 only on NEW breaks")
    p_check.add_argument("--write-baseline", help="write current breaks to this file and exit 0")

    p_rel = sub.add_parser("relink", help="rewrite links for staged git renames (2 passes)")
    common(p_rel)
    p_rel.add_argument("--dry-run", action="store_true", help="report without writing")

    args = ap.parse_args()
    return cmd_check(args) if args.cmd == "check" else cmd_relink(args)


if __name__ == "__main__":
    sys.exit(main())
