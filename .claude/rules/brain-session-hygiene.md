# Brain Session Hygiene

This project contains a **Project Brain** — a persistent LTM system in `project-brain/`.

## Session Start
- Check `project-brain/SESSION-HANDOFF.md` — if it exists, the previous session left unfinished work. Deposit any uncommitted discoveries before starting new work.
- Load `project-brain/INDEX-MASTER.md` to orient on all available knowledge.

## During Work
- When you discover something new (edge case, bug, decision, insight), deposit it as a LEARN or LOG file and update INDEX-MASTER.md before the session ends.
- When you modify or create any brain `.md` file, update its fat index entry in INDEX-MASTER.md in the same operation.

## Session End
- **Always** write `project-brain/SESSION-HANDOFF.md` before the session ends. Capture: what you were doing, what's done, what's left, uncommitted decisions, and what the next session should load.
- **Always** append an entry to `project-brain/logs/LOG-002_project-timeline.md` with date, session type, key actions, files created/modified, and decisions made.

## Handoff Triggers
Write SESSION-HANDOFF.md whenever:
- User says to end, clear, compact, or exit
- Context window feels high (long session, many tool calls)
- Before a long tool operation that might fail
- After completing a major milestone
- When user switches tasks mid-session
- When you detect you're going in circles
