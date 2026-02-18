# Fat Index Discipline

## Index-First Rule
**Never open a brain file speculatively.** Always read `project-brain/INDEX-MASTER.md` first. Each fat index entry contains enough detail to determine whether the full file is needed. Every file you open costs context tokens you cannot recover.

## Search Workflow
1. Scan INDEX-MASTER.md fat index entries for keywords matching your task
2. Identify the 1-3 most relevant files from summaries alone
3. Open only those files
4. If you need broader context, use `project-brain/INIT.md` or `project-brain/specs/SPEC-001_coder-brain-architecture.md`

## Index Update Rule
Every time you create or modify a brain `.md` file, you **must** update its fat index entry in INDEX-MASTER.md. A fat index entry must answer: "Do I need to open this file?" It includes:
1. **What** the file contains (one sentence)
2. **Key decisions** made inside it
3. **Interface/contract** — inputs and outputs
4. **Open issues** — so future sessions don't chase a file expecting answers it lacks

## File Count
Keep the `total-files` comment in INDEX-MASTER.md accurate after any addition or removal.
