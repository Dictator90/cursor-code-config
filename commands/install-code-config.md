---
description: Install full Cursor code-config baseline in current project.
---

Install the production baseline in one run.

Run this command from project root:

```bash
python scripts/run_install_code_config.py
```

After running:
- Show output from baseline, hooks setup, doctor, and deterministic gates.
- Confirm `.cursor/hooks.json` was updated in the current project.
- Confirm `.cursor/rules/*.mdc` runtime pack and `.cursor/.code-config-install.json` were created in the current project.
- Confirm `python scripts/check_deterministic_gates.py --evidence-mode auto` completed.
