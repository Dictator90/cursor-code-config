---
description: Install full Cursor code-config baseline in current project.
---

Install the production baseline in one run.

From your **target project root** (not from the plugin repo), point Python at the plugin's
`run_install_code_config.py` script under your Cursor plugins directory.

On Windows (PowerShell), after setting an environment variable with the plugin path:

```powershell
$env:CURSOR_CODE_CONFIG_ROOT = "C:\path\to\cursor-code-config"
python "$env:CURSOR_CODE_CONFIG_ROOT\scripts\run_install_code_config.py"
```

On macOS / Linux (bash/zsh), after setting an environment variable with the plugin path:

```bash
export CURSOR_CODE_CONFIG_ROOT="/path/to/cursor-code-config"
python "$CURSOR_CODE_CONFIG_ROOT/scripts/run_install_code_config.py"
```

These Python scripts live **inside the plugin**, not in your project:
- `run_install_code_config.py` locates `install_code_config.py` inside the plugin install tree.
- `install_code_config.py` then applies the baseline to **the project in your current working directory** (the root where you run the command).

Do not copy these scripts into your projects; always call them from the plugin location.

If you installed the plugin in a non-default location, adjust the path so that it points
to your `cursor-code-config/scripts/run_install_code_config.py`.

After running:
- Show output from baseline, hooks setup, doctor, and deterministic gates.
- Confirm `.cursor/hooks.json` was updated in the current project.
- Confirm `.cursor/rules/*.mdc` runtime pack and `.cursor/.code-config-install.json` were created in the current project.
- Confirm `python scripts/check_deterministic_gates.py --evidence-mode auto` completed.
