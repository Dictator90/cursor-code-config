# Principle 18 - Multi-Session Coordination

## Problem

Single-session handoffs solve "what is next?", but they do not fully solve
parallel work. When multiple sessions run on the same repository, naive
handoff storage creates collisions and lost context:

- Last writer wins if everyone writes to one file.
- Sessions overwrite each other's partial state.
- Resume flows become non-deterministic ("which handoff is the latest for my task?").

This is a coordination problem, not only a documentation problem.

## Solution: Append-Only Session Handoffs

Use an append-only model with one file per session under `.cursor/handoffs/`:

```
.cursor/handoffs/
  2026-04-14_11-30_a1b2c3d4.md
  2026-04-14_12-10_e5f6g7h8.md
  INDEX.md
```

Rules:

1. Never overwrite old handoffs.
2. Always write a new file with a unique session suffix.
3. Always append one index entry to `INDEX.md`.
4. Read the latest relevant handoff by topic/session ID, not by file name guess.

## Coordination Invariants

These invariants keep multi-session continuity reliable:

- **Uniqueness:** each session writes to its own file.
- **Immutability:** old handoffs are historical records, not mutable state.
- **Discoverability:** `INDEX.md` is the canonical lookup table.
- **Bounded recap:** resume reads only recent/relevant entries, not full history.

## Recommended Index Format

One line per handoff:

```text
<timestamp> | <session-short-id> | <topic> | <relative-path>
```

Example:

```text
2026-04-14 11:30 | a1b2c3d4 | drift-validator | .cursor/handoffs/2026-04-14_11-30_a1b2c3d4.md
```

## Operational Guidance

- For one-off short tasks, a single latest handoff may be enough.
- For long-running or parallel work, always use the append-only model.
- Keep tactical details in handoffs and strategic evolution in project chronicles.

## Relationship to Other Principles

- **07 Codified Context:** handoff files are runtime context artifacts.
- **16 Project Chronicles:** chronicles explain history; handoffs transfer state.
- **11 Documentation Integrity:** links and paths in handoffs must stay valid.
- **04 Deterministic Orchestration:** naming/indexing rules should be mechanical.
