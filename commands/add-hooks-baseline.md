---
description: Add recommended baseline hook set to project .cursor/hooks.json.
---

Add the recommended baseline hook set for this repository.
Hooks are written to project-local `.cursor/hooks.json`.

Run these commands in order:
1. `python scripts/add_hook.py session-drift-validator`
2. `python scripts/add_hook.py session-handoff-check`
3. `python scripts/add_hook.py destructive-command-guard`
4. `python scripts/add_hook.py secret-leak-guard`
5. `python scripts/add_hook.py session-handoff-reminder`

If `scripts/add_hook.py` does not exist in the current project, run this fallback:

```bash
python -c "from pathlib import Path; import subprocess, sys; root=Path.cwd(); hooks_config=root/'.cursor/hooks.json'; candidates=[Path.home()/'.cursor/plugins/local/cursor-code-config/scripts/add_hook.py', Path.home()/'.cursor/plugins/local/cursor-config-hardening/scripts/add_hook.py']; script=next((p for p in candidates if p.exists()), None); assert script is not None, 'Could not locate installed plugin add_hook.py'; hook_names=['session-drift-validator','session-handoff-check','destructive-command-guard','secret-leak-guard','session-handoff-reminder']; [subprocess.run([sys.executable, str(script), name, '--settings', str(hooks_config)], check=True) for name in hook_names]"
```

After running:
- Show all command outputs.
- Confirm which hooks config file was updated.
