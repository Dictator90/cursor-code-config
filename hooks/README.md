# Hook Examples

Ready-to-use hook scripts for Cursor agents. Register in your Cursor settings file.

## Quick Setup

Add any hook to your Cursor settings:

```json
{
  "hooks": {
    "EventName": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python path/to/script.py",
            "statusMessage": "Running hook..."
          }
        ]
      }
    ]
  }
}
```

Or add hooks one-by-one with the helper script:

```bash
python scripts/add_hook.py session-drift-validator
python scripts/add_hook.py session-handoff-check
python scripts/add_hook.py session-handoff-reminder
python scripts/add_hook.py destructive-command-guard
python scripts/add_hook.py secret-leak-guard
```

Each command is idempotent: running it again will not duplicate entries.

Or run Cursor slash commands from this repository:

```text
/add-hook-session-drift-validator
/add-hook-session-handoff-check
/add-hook-destructive-command-guard
/add-hook-secret-leak-guard
/add-hook-session-handoff-reminder
```

For one-shot setup of the recommended baseline:

```text
/add-hooks-baseline
```

## How To Use On A Project

Use this quick flow when enabling hooks in a real repository.

### 1) Pick a minimal starter set

Recommended baseline:

- `session-drift-validator.py` (`SessionStart`)
- `session-handoff-reminder.py` (`Stop`)
- `destructive-command-guard.py` (`PreToolUse`)
- `secret-leak-guard.py` (`PreToolUse`)

### 2) Register hooks in Cursor settings

Put hook config in your Cursor settings JSON and use absolute script paths.

If you prefer one command per hook (recommended rollout):

```bash
# Start with drift visibility
python scripts/add_hook.py session-drift-validator

# Optional: show recent handoffs on new sessions
python scripts/add_hook.py session-handoff-check

# Add safety guards
python scripts/add_hook.py destructive-command-guard
python scripts/add_hook.py secret-leak-guard

# Add stop-time handoff reminder last
python scripts/add_hook.py session-handoff-reminder
```

```json
{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python F:/phpstorm/mb/claude-code-config/hooks/session-drift-validator.py",
            "statusMessage": "Validating docs/rules drift..."
          }
        ]
      }
    ],
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python F:/phpstorm/mb/claude-code-config/hooks/session-handoff-reminder.py",
            "statusMessage": "Checking handoff state..."
          }
        ]
      }
    ],
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python F:/phpstorm/mb/claude-code-config/hooks/destructive-command-guard.py",
            "statusMessage": "Checking destructive command safety..."
          }
        ]
      },
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "python F:/phpstorm/mb/claude-code-config/hooks/secret-leak-guard.py",
            "statusMessage": "Checking secret leakage..."
          }
        ]
      }
    ]
  }
}
```

### 3) Start with one hook, then expand

If you are enabling hooks for the first time:

1. Enable only `session-drift-validator.py`.
2. Confirm it runs cleanly on session start.
3. Add the two safety guards.
4. Add `session-handoff-reminder.py` last.

## Verification Checklist

Use this checklist to confirm hooks are not just configured, but actually enforcing behavior.

- **SessionStart hook fires**
  - Start a new session.
  - Expect to see `statusMessage` from `session-drift-validator.py`.
- **Stop hook can block when expected**
  - Keep a session running long enough to trigger handoff reminder.
  - End session without fresh handoff.
  - Expect `{"decision":"block", ...}` behavior.
- **Destructive guard blocks risky shell commands**
  - Ask agent to run a known destructive pattern (for example `rm -rf` in a safe test context).
  - Expect block with explanation.
- **Secret guard blocks risky writes**
  - Attempt to write a fake key pattern into a tracked file.
  - Expect block from `secret-leak-guard.py`.
- **No hook startup errors**
  - No Python path errors in status output.
  - No malformed JSON response errors from hooks.

## Common Mistakes

- **Wrong script path**
  - Symptom: hook never fires.
  - Fix: use absolute paths and verify file exists.
- **Wrong Python executable**
  - Symptom: command not found / import errors.
  - Fix: set explicit Python binary if `python` alias is not stable.
- **Matcher does not match**
  - Symptom: hook appears configured but never runs.
  - Fix: test with broad matcher first (`Bash` or `Write`) then narrow.
- **Invalid hook JSON shape**
  - Symptom: hook config ignored or parsing errors.
  - Fix: keep exact nesting: `event -> list -> hooks -> command entries`.
- **Overloading too many hooks at once**
  - Symptom: hard to debug which hook failed.
  - Fix: enable incrementally (one hook, verify, then add next).

## Available Hooks

### Session Management

| Script | Event | What It Does |
|---|---|---|
| [session-drift-validator.py](session-drift-validator.py) | `SessionStart` | Validates file path references in active docs/rules at session start. Catches stale pointers before the agent acts on them. |
| [session-handoff-reminder.py](session-handoff-reminder.py) | `Stop` | Reminds to write a handoff file when closing a long session. Prevents context loss between sessions. |

### Safety Guards

| Script | Event | What It Does |
|---|---|---|
| [destructive-command-guard.py](destructive-command-guard.py) | `PreToolUse` | Warns before destructive commands (`rm -rf`, `DROP TABLE`, `git push --force`, `git reset --hard`). Returns `{"decision": "block"}` with explanation. |
| [secret-leak-guard.py](secret-leak-guard.py) | `PreToolUse` | Blocks Write/Edit operations that would introduce secrets (API keys, tokens, passwords) into tracked files. |

### Quality & Context

| Script | Event | What It Does |
|---|---|---|
| [kvcache-stats.py](../scripts/kvcache_stats.py) | Manual | Analyzes KV-cache hit rate across sessions. Not a hook but a diagnostic script. |

## Hook Events Reference

| Event | When It Fires | Use For |
|---|---|---|
| `SessionStart` | New session begins | Validation, context loading, drift detection |
| `Stop` | Session ends | Handoff, cleanup, learning extraction |
| `PreToolUse` | Before any tool call | Safety guards, permission checks, logging |
| `PostToolUse` | After any tool call | Logging, notifications, side effects |
| `Notification` | Agent sends notification | Custom notification routing |
| `TaskCreated` | Sub-agent task spawned | Tracking, resource allocation |

### Conditional Hooks (v2.1.89+)

Use the `if` field to run hooks only for specific patterns:

```json
{
  "event": "PreToolUse",
  "hooks": [{ "type": "command", "command": "check_git.sh" }],
  "if": "Bash(git *)"
}
```

### Hook Responses

Hooks can return JSON to control behavior:

| Response | Effect |
|---|---|
| `{"decision": "allow"}` | Proceed normally |
| `{"decision": "block", "reason": "..."}` | Block the tool call |
| `{"decision": "defer"}` | Pause headless session for human review |
| `{"retry": true}` | Retry after PermissionDenied (v2.1.89+) |

### Matcher Patterns for PreToolUse/PostToolUse

```json
{"matcher": "Bash"}           // Any Bash call
{"matcher": "Write"}          // Any file write
{"matcher": "Bash(git *)"}    // Git commands only
{"matcher": "Bash(rm *)"}     // Delete commands only
{"matcher": "mcp__*"}         // Any MCP tool call
```

## Principles

- **Hook > Rule** for guaranteed behaviors. Rules are instructions of hope; hooks execute unconditionally.
- **One concern per hook.** Don't combine drift validation with secret scanning.
- **Exit 0 always.** A crashing hook blocks the agent. Use `|| true` in settings.json as a safety net.
- **Keep hooks fast.** They run synchronously. Target <500ms per hook.
