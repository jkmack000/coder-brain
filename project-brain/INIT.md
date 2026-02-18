# INIT — Read This First

You are an LLM starting a new session. This folder is a **Project Brain** — a persistent long-term memory system designed for you.

## What to do right now

1. **Check for `SESSION-HANDOFF.md`** in this directory. If it exists, read it first — it tells you what was happening when the last session ended, what's unfinished, and what to do next. Deposit any uncommitted decisions or discoveries into proper LTM files before starting new work.
2. Read `INDEX-MASTER.md`. It contains a fat index of every knowledge file in this brain. Each entry has enough detail to tell you whether you need to open the full file or not.
3. The user will give you a task. Use the index to find relevant files, load only what you need, and get to work.

## How this system works

- **You have no memory between sessions.** This brain is your memory. Everything you need to know is stored as `.md` files in typed directories.
- **Fat indexes save your context tokens.** INDEX-MASTER.md summarizes every file so you can skip files you don't need without opening them.
- **File types:** SPEC (design decisions), CODE (implementation docs), RULE (business rules), LEARN (discovered knowledge), LOG (decision rationale), RESET (pre-built context packages for specific tasks).
- **SPEC-001** is the full architecture document. Read it if you need to understand the system deeply.

## Directory layout

```
project-brain/
├── INIT.md              ← You are here
├── SESSION-HANDOFF.md   ← Check this first if it exists. Last session's state.
├── INDEX-MASTER.md      ← Load this second. Fat index of everything.
├── brain.py             ← CLI search tool (user runs this, not you)
├── archive/             ← Retired files (kept for reference)
├── indexes/             ← Sub-indexes when file count exceeds ~75
├── reset-files/         ← Pre-built context packages for tasks
├── templates/           ← File templates for each type
├── specs/               ← SPEC files (design, architecture)
├── code/                ← CODE files (implementation docs)
├── rules/               ← RULE files (business rules)
├── learnings/           ← LEARN files (discovered knowledge)
└── logs/                ← LOG files (decision rationale)
```

## Key rules

- **Don't open files speculatively.** Read the fat index first. Every file you open costs tokens you can't get back.
- **Deposit new knowledge.** If you discover something during a session (edge case, bug, decision), write it as a LEARN or LOG file and update INDEX-MASTER.md before the session ends.
- **Deduplicate during ingestion.** Before writing new files from source material, scan INDEX-MASTER.md fat index entries and compare against the new content. Only deposit what is genuinely new: a new fact, a contradiction to existing knowledge, a different parameter with evidence, or a new limitation. If the source just restates what's already in the brain, note it was reviewed but don't create duplicate files. When in doubt, enrich an existing file rather than creating a new one.
- **Periodic consolidation.** After every ~20-30 new files, do a cleanup pass: merge redundant files that say the same thing from different sources, resolve contradictions between files, tighten fat index summaries, and retire superseded files. This is a dedicated session type — don't try to do it mid-work.
- **RESET files bridge sessions.** If the current task will continue in a future session, generate a RESET file listing exactly what files and context the next session needs.
- **Append to `LOG-002_project-timeline.md` before ending any session.** This is the project's chronological record. Add a dated entry with: session type, key actions, files created/modified, decisions made, and blockers. See the entry format template inside the file.
- **Write SESSION-HANDOFF.md whenever session state is at risk.** This is mandatory. Capture: what you were doing, what's done, what's left, any undocumented decisions or discoveries, and what the next session should load. Overwrite the previous handoff — only the latest matters. Triggers:
  - User says to end, clear, compact, or exit the session
  - Context window reaches ~80% usage (and after every interaction past that point)
  - Before a long tool operation that might fail or time out
  - After completing a major milestone within a session
  - When the user switches tasks mid-session
  - When you detect you're going in circles

## User shorthand commands

The user may use these shorthand phrases:
- **"Ingest this into [brain name]"** = Read the source, extract knowledge, write typed .md files, update INDEX-MASTER.md with fat index entries.
- **"Deposit this as [TYPE]"** = Write a single .md file of that type and add its fat index entry.
- **"Index this"** = Add/update the fat index entry in INDEX-MASTER.md for an existing file.
- **"Handoff"** = Write SESSION-HANDOFF.md right now.

## CLI tool (brain.py)

The user can run these commands from a terminal (you don't need to — you read files directly):

```
uv run brain.py status                  # Overview of the brain
uv run brain.py search "query"          # Search fat indexes
uv run brain.py recall "task"           # Generate a RESET file
uv run brain.py deposit --type TYPE --tags "tags"  # Add a new file
uv run brain.py ingest "source.md"      # Extract knowledge from a source
uv run brain.py init "Project Name"     # Scaffold a new brain (for new projects)
```
