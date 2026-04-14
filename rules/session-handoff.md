# Session Handoff - Seamless Transitions Between Sessions

Drop this file into `.cursor/rules/session-handoff.md` (project-local) to enable manual handoff triggers.

## Manual trigger

When the user sends one of these phrases (or a close equivalent), immediately
write a new handoff file under `.cursor/handoffs/` following the format below
and stop working until the user confirms.

**Trigger phrases:**

- "prepare handoff"
- "save context for new chat"
- "write handoff"
- "handoff this session"
- "we're closing, write handoff"
- "hand off this conversation"

**What to do when triggered:**

1. Write `.cursor/handoffs/YYYY-MM-DD_HH-MM_<session-short-id>.md` with the real
   content of the current session, not a template.
2. If the session covered multiple areas, group by topic instead of one flat
   list.
3. Always fill the "what did NOT work" section, even if everything succeeded -
   include false positives, near-misses, or discarded approaches.
4. Keep the file under 1500 tokens. It is a briefing, not a log.
5. Append one line to `.cursor/handoffs/INDEX.md`:
   `<timestamp> | <session-short-id> | <topic> | <relative-path>`.
6. After writing, tell the user: "Handoff written to `.cursor/handoffs/...`,
   [N] lines. You can open a new chat now."
7. **Do NOT continue working** after writing the handoff. The user is closing
   the session.

**What NOT to include:**

- Raw tool call history or intermediate file reads
- Narrative of "I did X, then Y, then Z" - describe what is *currently true*,
  not what you did
- Duplicated content from project rules or memory

## At session start

Check for recent files in `.cursor/handoffs/`. If they exist:

1. Read the most recent handoff silently.
2. Briefly summarize to the user in 3-5 lines: goal, current state, next step.
3. Ask: continue from the handoff, or start a new task?
4. Keep handoff files append-only; do not rewrite old handoffs.

## At session end (long sessions over 15 minutes)

If the user has not explicitly triggered a handoff, write one before ending
the session anyway. This complements the Stop hook automation - if the hook
is not configured or fails to fire, the rule provides a fallback.

## HANDOFF.md format

```markdown
# Session Handoff - YYYY-MM-DD HH:MM

## Goal
What we were trying to accomplish and why.

## Done
- Concrete results with absolute file paths
- Grouped by topic if multiple areas

## What did NOT work
- Approach A - failed because [specific reason, with error message if any]
- Library B - version 2.x has [specific issue], fell back to 1.9

## Current state
- Working: [features/endpoints verified]
- Broken: [what's failing, with the actual error]
- Blocked: [what is waiting on external dependency]

## Key decisions
- Chose X over Y because [reason]
- Deferred Z until [condition]

## Next step
[A single concrete action to begin the next session - not a list]
```

File location:
- `.cursor/handoffs/YYYY-MM-DD_HH-MM_<session-short-id>.md`

Index format:
- `.cursor/handoffs/INDEX.md` (append-only)
- Example entry: `2026-04-14 11:30 | a1b2c3d4 | drift-validator | .cursor/handoffs/2026-04-14_11-30_a1b2c3d4.md`

## Why rules, not hooks

A `Stop` hook can force handoff writing mechanically, but requires the user
to configure Cursor settings with a Python script. This rule works
immediately in any session because Cursor reads `.cursor/rules/*.md` as part
of the system prompt.

**Use both:** the rule handles deliberate triggers and older sessions started
before automation was added. The hook handles forgetful users and guarantees
handoff for very long sessions.

See [alternatives/session-handoff.md](../alternatives/session-handoff.md) for
all 5 approaches (manual, hook, journal, framework, memory-only) compared
with pros, cons, and when-to-choose guidance.

For multi-session safety guarantees (append-only model, index invariants),
see [principles/18-multi-session-coordination.md](../principles/18-multi-session-coordination.md).

## Connection to Project Chronicles

For long-running projects (spanning weeks/months with 3+ handoffs), handoffs
alone don't tell the story of how a project evolved. **Project chronicles**
solve this by maintaining a single condensed timeline per project.

When writing a handoff for a long-running project:
1. Add `**Project:** <slug>` to the handoff header
2. After writing the handoff, append a 3-7 line entry to
   `.cursor/chronicles/<slug>.md`
3. Chronicle entry = strategic digest (decisions, turns, results), NOT a
   handoff copy

When starting a session on a long-running project:
1. Read `.cursor/chronicles/<slug>.md` for strategic context
2. Read the latest handoff for tactical context
3. Together they answer both "how did we get here?" and "what's next?"

See [principles/16-project-chronicles.md](../principles/16-project-chronicles.md)
for the full pattern and [templates/chronicle.md](../templates/chronicle.md)
for the file template.
