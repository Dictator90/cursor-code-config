---
name: cursor-hardening
description: Use when a repository must become Cursor-only and you need deterministic safety, supply-chain, and reference checks.
---

# Cursor Hardening Skill

## What this plugin provides

- A baseline checker to verify required hardening files exist.
- A baseline applier to create missing Cursor-only defaults.
- Deterministic checks that avoid user-home fallback behavior by default.

## Commands

Run from repository root:

```bash
python scripts/doctor.py
python scripts/apply_baseline.py
```

## Required files validated by doctor

- `.cursor/rules/cursor-only-baseline.md`
- `.cursor/rules/session-handoff.md`
- `.npmrc` containing `min-release-age=7`
- `uv.toml` containing `exclude-newer = "7 days"`
