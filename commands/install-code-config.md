---
description: Install full Cursor code-config baseline in current project.
---

Install the production baseline in one run.

When the user runs `/install-code-config`, this invocation is explicit approval to execute
the install flow now (do not refuse with "user-run only" in this case).

Execution steps:

1. Ensure current working directory is the user's target project root.
2. Locate plugin installer script:
   - Find `run_install_code_config.py` under Cursor plugins directory (`~/.cursor/plugins/**/scripts/`).
   - Prefer the `cursor-code-config` plugin path if multiple matches exist.
3. Execute:
   - `python <resolved-plugin-path>/scripts/run_install_code_config.py`
4. Then run:
   - `python <resolved-plugin-path>/scripts/check_deterministic_gates.py --evidence-mode auto`
5. Report exact outputs and verification results.

These Python scripts live **inside the plugin**, not in the project:
- `run_install_code_config.py` locates `install_code_config.py` inside the plugin install tree.
- `install_code_config.py` then applies the baseline to **the project in your current working directory** (the root where you run the command).

Do not copy these scripts into projects; always execute from the plugin location.

After running:
- Show output from baseline, hooks setup, doctor, and deterministic gates.
- Confirm `.cursor/hooks.json` was updated in the current project.
- Confirm `.cursor/rules/*.mdc` runtime pack and `.cursor/.code-config-install.json` were created in the current project.
- Confirm deterministic gates completed successfully.
