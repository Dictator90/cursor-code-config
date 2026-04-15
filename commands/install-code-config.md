---
description: Install full Cursor code-config baseline in current project.
---

Install the production baseline in one run.

Run this command from project root:

```bash
python -c "from pathlib import Path; import subprocess, sys; root=Path.cwd(); plugin_root=Path(__file__).resolve().parents[1] if '__file__' in globals() else None; \
def pick(script_name): \
  local=root/'scripts'/script_name; \
  if local.exists(): return local; \
  plugins=Path.home()/'.cursor/plugins'; \
  candidates=[]; \
  if plugins.exists(): \
    candidates.extend(sorted(plugins.glob(f'local/*/scripts/{script_name}'))); \
    candidates.extend(sorted(plugins.glob(f'*/scripts/{script_name}'))); \
  if plugin_root is not None: \
    candidates.append(plugin_root/'scripts'/script_name); \
  found=next((p for p in candidates if p.exists()), None); \
  if found is None: raise SystemExit(f'Missing required script: {script_name}'); \
  return found; \
install_script=pick('install_code_config.py'); \
subprocess.run([sys.executable, str(install_script)], check=True)"
```

After running:
- Show output from baseline, hooks setup, doctor, and deterministic gates.
- Confirm `.cursor/hooks.json` was updated in the current project.
- Confirm `.cursor/rules/*.mdc` runtime pack and `.cursor/.code-config-install.json` were created in the current project.
- Confirm `python scripts/check_deterministic_gates.py --evidence-mode auto` completed.
