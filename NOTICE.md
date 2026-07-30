# Third-Party Notices

`claude-code-studios` is MIT licensed (see [`LICENSE`](LICENSE)). It also
contains code and documentation copied from third-party projects. Their
license terms are reproduced below in full, as MIT requires.

---

## im-not-ai

- **Upstream**: <https://github.com/epoko77-ai/im-not-ai>
- **License**: MIT
- **Vendored at**: commit `53e24e8` (v2.3.0), retrieved 2026-07-30
- **Vendored in**: v0.6.0

### What was copied

| Destination | Files | Modified? |
|---|---|---|
| `scripts/` | `verify_gates.py`, `verify_change_rate.py`, `prepare_monolith_input.py`, `build_quick_rules.py`, `build_diagnosis_rules.py` | Path constants only (see below) |
| `scripts/` | `reassemble_chunks.py` | Unmodified |
| `skills/humanize-korean/` | `SKILL.md` + `reference/` (14 files) | Reference-directory renamed; frontmatter converted to the studios 5-field convention |
| `tests/` | 26 files — 11 `test_*.py`, `humanize_asserts.py`, `humanize_runner.py`, `generate_fixtures.py`, `fixtures.json`, `README.md`, and `golden/` (`checks.py`, `README.md`, 2 fixture sets) | Path constants only |

**The one systematic change**: upstream hardcodes the reference directory as
`.claude/skills/humanize-korean/references`. In studios the skill lives at the
repo root and the convention is a singular `reference/` (established by
`skills/web-ai-patterns/`), so every occurrence became
`skills/humanize-korean/reference`. Nothing else in the runtime was altered —
verified by reproducing the upstream test result exactly (185 passed,
1 skipped, 12 subtests).

### What was deliberately not copied

- `agents/` release-only tooling (`translationese-research-distiller`,
  `korean-translation-scholar`, `taxonomy-gap-analyzer`,
  `post-editese-metric-engineer`, `quick-rules-integrator`) — one-off
  instruments for upstream's academic-absorption cycle, unrelated to the
  rewriting runtime.
- `codex/`, `commands/*.toml`, `gemini-extension.json`, `GEMINI.md` — Codex
  and Gemini CLI adapters; studios targets Claude Code only.
- `assets/` and the Pillow-dependent scripts (`build_social_preview*.py`,
  `make_thumbnail.py`) — upstream's social-preview tooling. Excluding these is
  what keeps the vendored runtime on the Python standard library with **zero
  third-party dependencies**.
- `tests/test_humanize_live.py` — invokes the `claude` CLI per fixture (paid,
  tens of seconds per call).
- `tests/test_install_flags.sh` — tests `install.sh`, which studios does not
  vendor (it ships as a marketplace plugin).

### License

```
MIT License

Copyright (c) 2026 epoko77-ai

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## Keeping this file honest

When re-syncing with upstream, update the vendored commit above and record any
new local modifications in the table. Local fixes to upstream bugs should be
sent back as pull requests rather than kept as private divergence.
