---
description: Apply Cursor hardening baseline in current project.
---

Run baseline setup for the current project:

1. Check whether `scripts/apply_baseline.py` exists in the current project root.
2. If it exists, run `python scripts/apply_baseline.py`.
3. If it does not exist, run this fallback from the current project root:

```bash
python -c "from pathlib import Path; root=Path.cwd(); br='''# Cursor-only baseline\n\n- Keep this repository Cursor-only.\n- Prefer AGENTS.md and .cursor/rules for operational guidance.\n- Enforce deterministic checks in CI before merge.\n'''; hr='''# Session handoff\n\n- Write concise handoff notes for multi-step tasks.\n- Include: goal, completed work, blockers, next action.\n'''; created=[]; p1=root/'.cursor/rules/cursor-only-baseline.md'; p1.parent.mkdir(parents=True,exist_ok=True); (created.append(str(p1)) if not p1.exists() else None); (p1.write_text(br,encoding='utf-8') if not p1.exists() else None); p2=root/'.cursor/rules/session-handoff.md'; p2.parent.mkdir(parents=True,exist_ok=True); (created.append(str(p2)) if not p2.exists() else None); (p2.write_text(hr,encoding='utf-8') if not p2.exists() else None); npm=root/'.npmrc'; uv=root/'uv.toml'; n=npm.read_text(encoding='utf-8') if npm.exists() else ''; u=uv.read_text(encoding='utf-8') if uv.exists() else ''; add1='min-release-age=7'; add2='exclude-newer = \"7 days\"'; npm.write_text((n + ('\n' if n and not n.endswith('\n') else '') + add1 + '\n') if add1 not in n else n, encoding='utf-8'); uv.write_text((u + ('\n' if u and not u.endswith('\n') else '') + add2 + '\n') if add2 not in u else u, encoding='utf-8'); print('Baseline applied.'); print('Created files:' if created else 'No new files created.'); [print('- '+x) for x in created]"
```

4. Show command output.
5. If baseline files were created, list which ones were added.
