# Cursor Config Hardening (Plugin)

Cursor-native adaptation of the configuration system described in the original article and repository:
- Source concept repo: [AnastasiyaW/claude-code-config](https://github.com/AnastasiyaW/claude-code-config)

This repository is a **single plugin** (`cursor-config-hardening`) with principles, hooks, templates, rules, scripts, commands, and skills wired for Cursor.

## What Is Implemented

- `principles/` - architectural principles (`01`-`18`), including multi-session coordination.
- `alternatives/` - approach comparisons (orchestration, handoff, context, optimization, etc.).
- `hooks/` - drift, destructive-command, secret-leak, and handoff hooks.
- `templates/` - starter templates for policy, review, handoff, chronicle, and memory.
- `rules/` + `.cursor/rules/` - runtime guidance and continuity protocol.
- `scripts/` - deterministic setup and verification (`apply_baseline.py`, `doctor.py`, validators).
- `.cursor/commands/` - slash commands for enabling hooks from the agent.
- `skills/` - domain skill catalog + `CURSOR-HARDENING` operational skill.

## Quick Start (for project users)

1. Open your target project in Cursor.
2. Connect/install this plugin (`cursor-config-hardening`).
3. From project root, apply baseline:
   - `python scripts/apply_baseline.py`
4. Enable hooks (recommended one-shot):
   - `/add-hooks-baseline`
   - or one-by-one: `/add-hook-session-drift-validator`, `/add-hook-destructive-command-guard`, etc.
5. Verify:
   - `python scripts/doctor.py`
   - `python scripts/check_cursor_only_surface.py`
   - `python scripts/validate_config.py --strict`
   - or use slash commands: `/doctor`, `/check-cursor-only-surface`, `/validate-config-strict`

## Cursor Commands (Agent Slash Commands)

These commands are available via `.cursor/commands/`:

- `/apply-baseline` -> `python scripts/apply_baseline.py`
- `/doctor` -> `python scripts/doctor.py`
- `/check-cursor-only-surface` -> `python scripts/check_cursor_only_surface.py`
- `/validate-config-strict` -> `python scripts/validate_config.py --strict`

## Where Files Are Written

- **Written in the current project** (safe/project-local):
  - `.cursor/rules/cursor-only-baseline.md`
  - `.cursor/rules/session-handoff.md`
  - `.npmrc` (`min-release-age=7`)
  - `uv.toml` (`exclude-newer = "7 days"`)
  - session continuity files in `.cursor/handoffs/` (when using handoff flow)
- **Written in the current project** (safe/project-local):
  - `.cursor/hooks.json` and `.cursor/hooks/*.py` when running hook-enable commands (`/add-hook-*` or `python scripts/add_hook.py ...`)

`scripts/apply_baseline.py` and `scripts/doctor.py` are explicitly project-root based (`Path.cwd()`), so baseline files are created/checked in the active project.

## About Extra Skill vs Original

`skills/CURSOR-HARDENING/SKILL.md` is an additional Cursor operational helper.  
It is intentionally added to improve setup UX and deterministic rollout; it does not replace or conflict with the original logic from the article.

## Safety/Compatibility Notes

- Plugin manifest: `.cursor-plugin/plugin.json`
- Plugin commands: `.cursor/commands/`
- Plugin remains root-scoped (`.`) via `.cursor-plugin/marketplace.json` and `.agents/plugins/marketplace.json`.
- Hooks are not auto-injected silently; they are added explicitly via `/add-hook-*` commands for controlled rollout.

## License

MIT
