---
description: Add recommended baseline hook set to project .cursor/settings.json.
---

Add the recommended baseline hook set for this repository.
Hooks are written to project-local `.cursor/settings.json`.

Run these commands in order:
1. `python scripts/add_hook.py session-drift-validator`
2. `python scripts/add_hook.py session-handoff-check`
3. `python scripts/add_hook.py destructive-command-guard`
4. `python scripts/add_hook.py secret-leak-guard`
5. `python scripts/add_hook.py session-handoff-reminder`

If `scripts/add_hook.py` does not exist in the current project, run this fallback:

```bash
python -c "import json; from pathlib import Path; root=Path.cwd(); settings_path=root/'.cursor/settings.json'; settings_path.parent.mkdir(parents=True, exist_ok=True); settings=json.loads(settings_path.read_text(encoding='utf-8')) if settings_path.exists() and settings_path.read_text(encoding='utf-8').strip() else {}; hooks=settings.setdefault('hooks', {}); plugin_roots=[Path.home()/'.cursor/plugins/local/cursor-code-config/hooks', Path.home()/'.cursor/plugins/local/cursor-config-hardening/hooks']; hooks_root=next((p for p in plugin_roots if p.exists()), None); assert hooks_root is not None, 'Could not locate installed plugin hooks directory'; specs=[('SessionStart',None,'session-drift-validator.py','Validating docs/rules drift...'),('SessionStart',None,'session-handoff-check.py','Checking for handoffs...'),('PreToolUse','Bash','destructive-command-guard.py','Checking destructive command safety...'),('PreToolUse','Write|Edit','secret-leak-guard.py','Checking secret leakage...'),('Stop',None,'session-handoff-reminder.py','Checking handoff state...')]; changed=[]; \
for event,matcher,file,status in specs: \
  event_list=hooks.setdefault(event, []); \
  block=next((b for b in event_list if ((matcher is None and 'matcher' not in b) or (matcher is not None and b.get('matcher')==matcher)), None); \
  block=block if block is not None else ({'hooks': []} if matcher is None else {'matcher': matcher, 'hooks': []}); \
  (event_list.append(block) if block not in event_list else None); \
  cmd=f'python \"{(hooks_root/file).as_posix()}\"'; \
  entry={'type':'command','command':cmd,'statusMessage':status}; \
  exists=any(h.get('type')==entry['type'] and h.get('command')==entry['command'] for h in block.get('hooks',[])); \
  (block.setdefault('hooks', []).append(entry), changed.append(file)) if not exists else None; \
settings_path.write_text(json.dumps(settings, indent=2)+'\n', encoding='utf-8'); print(f'[add-hooks] Updated {settings_path}'); print('[add-hooks] Added hooks: '+(', '.join(changed) if changed else 'none (already present)'))"
```

After running:
- Show all command outputs.
- Confirm which settings file was updated.
