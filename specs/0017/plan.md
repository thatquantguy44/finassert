# 0017 — Canonical master handoff: plan

## Approach

1. Build staged/commit/history validation and explicit Git-context refresh.
2. Test real temporary repos and failures, then wire pre-commit/pre-push/CI.
3. Add filesystem-only baseline, context refresh, read-only check, atomic
   checkpoint and explicit recovery without invoking Git.
4. Update canonical instructions and bootstrap a complete master checkpoint.
5. Verify the real hook/push path and non-Git filesystem flow; retain results in
   the local/master handoffs.

## Dependencies and affected areas

scripts/check_handoff.py, .githooks/, a dedicated .github/workflows/handoff.yml,
tests/unit/test_handoff.py, AGENTS.md, CONTRIBUTING.md and the spec catalog.
Existing Python APIs, financial semantics and Excel implementation are unchanged.

## Verification

```bash
.venv/bin/python -m pytest -q tests/unit/test_handoff.py
.venv/bin/python -m pytest -q
.venv/bin/ruff check .
.venv/bin/ruff format --check .
.venv/bin/mkdocs build --strict
python3 scripts/check_handoff.py --staged
python3 scripts/check_handoff.py --filesystem-init --filesystem-root /path/to/non-git-project
python3 scripts/check_handoff.py --filesystem-check --filesystem-root /path/to/non-git-project
git diff --check
```

Check all new local Markdown links/anchors. Stage intended work, refresh generated
context, explicitly stage the master, then exercise the actual hooks. Record
expected rejections before successful recovery; do not use a bypass to deliver.
