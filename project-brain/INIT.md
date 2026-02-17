# INIT — Read This First

You are an LLM starting a new session. This folder is a **Project Brain** — a persistent long-term memory system designed for you.

## What to do right now

1. Read `INDEX-MASTER.md` in this directory. It contains a fat index of every knowledge file in this brain. Each entry has enough detail to tell you whether you need to open the full file or not.
2. The user will give you a task. Use the index to find relevant files, load only what you need, and get to work.

## How this system works

- **You have no memory between sessions.** This brain is your memory. Everything you need to know is stored as `.md` files in typed directories.
- **Fat indexes save your context tokens.** INDEX-MASTER.md summarizes every file so you can skip files you don't need without opening them.
- **File types:** SPEC (design decisions), CODE (implementation docs), RULE (business rules), LEARN (discovered knowledge), LOG (decision rationale), RESET (pre-built context packages for specific tasks).

## Directory layout

```
project-brain/
├── INIT.md              ← You are here
├── INDEX-MASTER.md      ← Load this first. Fat index of everything.
├── brain.py             ← CLI search tool (user runs this, not you)
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
- **RESET files bridge sessions.** If the current task will continue in a future session, generate a RESET file listing exactly what files and context the next session needs.

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
