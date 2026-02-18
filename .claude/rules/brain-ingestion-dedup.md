# Brain Ingestion Dedup

## Before Depositing New Knowledge
Before writing any new brain file from source material:
1. Scan INDEX-MASTER.md fat index entries
2. Compare each candidate piece of knowledge against existing entries
3. Only deposit what is **genuinely new**: a new fact, a contradiction to existing knowledge, a different parameter with evidence, or a new limitation

## Dedup Outcomes
- **New knowledge** → Create a new file + fat index entry
- **Enrichment of existing file** → Update the existing file + its fat index entry
- **Duplicate/restatement** → Skip it (note it was reviewed if relevant)
- **Contradiction** → Deposit it and flag the conflict in both files' "Known issues"

## File Numbering
Use the next sequential number for the file type (e.g., if LEARN-018 exists, the next LEARN is LEARN-019). Never reuse or skip numbers.

## After Depositing
- Update INDEX-MASTER.md with a fat index entry for every new file
- Update the `total-files` count in INDEX-MASTER.md
- Append a timeline entry to LOG-002 if this is a significant deposit
