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
apply_script=pick('apply_baseline.py'); \
add_hook_script=pick('add_hook.py'); \
doctor_script=pick('doctor.py'); \
subprocess.run([sys.executable, str(apply_script)], check=True); \
hooks=root/'.cursor/hooks.json'; \
for name in ['session-drift-validator','session-handoff-check','destructive-command-guard','secret-leak-guard','session-handoff-reminder']: \
  subprocess.run([sys.executable, str(add_hook_script), name, '--hooks-config', str(hooks)], check=True); \
subprocess.run([sys.executable, str(doctor_script)], check=True); \
print('install-code-config completed')"
```

After running:
- Show output from baseline, hooks setup, and doctor.
- Confirm `.cursor/hooks.json` was updated in the current project.
