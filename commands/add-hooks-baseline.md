---
description: Add recommended baseline hook set to Cursor settings.
---

Add the recommended baseline hook set for this repository.

Run these commands in order:
1. `python scripts/add_hook.py session-drift-validator`
2. `python scripts/add_hook.py session-handoff-check`
3. `python scripts/add_hook.py destructive-command-guard`
4. `python scripts/add_hook.py secret-leak-guard`
5. `python scripts/add_hook.py session-handoff-reminder`

After running:
- Show all command outputs.
- Confirm which settings file was updated.
