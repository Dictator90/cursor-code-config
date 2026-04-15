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
- `commands/` - production onboarding command and validation utilities.
- `skills/` - domain skill catalog + `CURSOR-HARDENING` operational skill.

## Quick Start (for project users)

1. Open your target project in Cursor.
2. Connect/install this plugin (`cursor-config-hardening`).
3. Run single onboarding command:
   - `/install-code-config`
4. Validate after install (optional but recommended):
   - `/check-cursor-only-surface`
   - `/validate-config-strict`

## Cursor Commands (Agent Slash Commands)

These commands are provided by `commands/` in this plugin:

- `/install-code-config` -> baseline + hooks + doctor in one run
- `/check-cursor-only-surface` -> `python scripts/check_cursor_only_surface.py`
- `/validate-config-strict` -> `python scripts/validate_config.py --strict`

## Where Files Are Written

- **Written in the current project** (safe/project-local):
  - `.cursor/.supply-chain-policy.json` (enable/disable checks, min age days, ignore lists per ecosystem)
  - session continuity files in `.cursor/handoffs/` (when using handoff flow)
- **Written in the current project** (safe/project-local):
  - `.cursor/hooks.json` and `.cursor/hooks/*.py` when running `/install-code-config`
  - runtime hooks are project-local; plugin-level `hooks/hooks.json` is the baseline schema source

`scripts/apply_baseline.py`, `scripts/add_hook.py`, and `scripts/doctor.py` are project-root based (`Path.cwd()`), so all runtime files are created/checked in the active project.

## About Extra Skill vs Original

`skills/CURSOR-HARDENING/SKILL.md` is an additional Cursor operational helper.  
It is intentionally added to improve setup UX and deterministic rollout; it does not replace or conflict with the original logic from the article.

## Safety/Compatibility Notes

- Plugin manifest: `.cursor-plugin/plugin.json`
- Plugin commands: `commands/`
- Plugin remains root-scoped (`.`) via `.cursor-plugin/marketplace.json` and `.agents/plugins/marketplace.json`.
- Hooks are not auto-injected silently; they are added explicitly during `/install-code-config`.

## Migration Note

- Production onboarding is consolidated into `/install-code-config`.
- Legacy granular install commands were removed from the published command surface.

## License

MIT
