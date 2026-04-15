---
description: Save a session handoff now (manual, deduplicated).
---

Save a handoff immediately using the same protocol as stop-hook reminders.

Execution policy:
- This command saves handoff context from the current chat on user request.
- Keep handoffs append-only in `.cursor/handoffs/`.
- Do not create duplicates.

Steps:
1. Read `.cursor/rules/session-handoff.mdc` and follow its required sections and quality limits.
2. Ensure `.cursor/handoffs/INDEX.md` exists (create with template only if missing).
3. Build filename: `.cursor/handoffs/YYYY-MM-DD_HH-MM_<session-short-id>.md`.
4. Dedup before writing:
   - If a recent handoff for the same session already exists (same `<session-short-id>` and written in this session), do not create a new file.
   - If the latest handoff already captures the same goal/current-state/next-step, do not create a new file.
   - In dedup cases, report the existing file path and stop.
5. If no duplicate, write one handoff file with sections:
   - Goal
   - Done
   - What did NOT work (with reason)
   - Current state (working/broken/blocked)
   - Key decisions
   - Next step (single actionable step)
6. Append exactly one line to `.cursor/handoffs/INDEX.md`:
   - `- YYYY-MM-DD_HH-MM_<session-short-id>.md - short topic summary`
7. After writing, stop further implementation unless user asks to continue.
