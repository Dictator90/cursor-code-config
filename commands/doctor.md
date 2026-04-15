---
description: Run baseline doctor checks for current project.
---

Run baseline diagnostics:

1. Check whether `scripts/doctor.py` exists in the current project root.
2. If it exists, run `python scripts/doctor.py`.
3. If it does not exist, run this fallback from the current project root:

```bash
python -c "import json; from pathlib import Path; root=Path.cwd(); contains=lambda p,s: p.exists() and s in p.read_text(encoding='utf-8'); checks={'cursor_baseline_rule': (root/'.cursor/rules/cursor-only-baseline.md').exists(), 'cursor_handoff_rule': (root/'.cursor/rules/session-handoff.md').exists(), 'npm_min_release_age': contains(root/'.npmrc','min-release-age=7'), 'uv_exclude_newer': contains(root/'uv.toml','exclude-newer')}; status='PASS' if all(checks.values()) else 'FAIL'; print(json.dumps({'status':status,'checks':checks}, indent=2)); raise SystemExit(0 if status=='PASS' else 1)"
```

4. Show the JSON output.
5. If status is FAIL, summarize which checks failed.
