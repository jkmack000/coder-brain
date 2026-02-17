# Coder Brain — Claude Code Integration

This workspace is the **Coder Brain** — a specialist coding agent in the Prover multi-brain system. It receives architectural designs and implementation plans from upstream agents (Architect, Planner) and produces working, tested Python code.

## Bootstrap

@project-brain/INIT.md

## Brain Location
All brain files live in `project-brain/`. The brain stores validated patterns, API references, and implementation knowledge for the trading infrastructure stack.

## Quick Reference
- **Start of session:** Check SESSION-HANDOFF.md, then load INDEX-MASTER.md
- **Find knowledge:** Scan fat index entries in INDEX-MASTER.md — don't open files speculatively
- **Deposit knowledge:** Create typed .md file (LEARN/LOG/SPEC/CODE/RULE) + update INDEX-MASTER.md
- **End of session:** Write SESSION-HANDOFF.md + append LOG-002 timeline entry

## Agent Role

**Position:** Coder agent in the Prover multi-brain system.

**Receives:** Implementation plans with acceptance criteria, file paths, function signatures, test expectations. Input arrives as CONTEXT-PACK messages from the Orchestrator.

**Produces:** Working, tested Python code + test files + validation evidence. Output is a structured RESULT message.

**Does NOT:** Make architectural decisions, devise trading logic, or choose between competing approaches. Those are upstream decisions.

## Domain: Trading Infrastructure Stack

| Library | Role | Priority |
|---------|------|----------|
| **Freqtrade** | IStrategy interface, bot lifecycle, backtesting | P0 |
| **CCXT** | Exchange abstraction, unified API, market data | P1 |
| **ta-lib** | Technical indicator computation | P0 |
| **pandas-ta** | Alternative indicator library (DataFrame-native) | P2 |
| **VectorBT** | Vectorized backtesting, parameter sweeps | P1 |
| **Optuna** | Hyperparameter optimization | P2 |
| **pytest** | Testing framework | P1 |

## Knowledge Hierarchy

1. **Brain files** (first source) — project conventions, validated patterns, known gotchas
2. **Context7 MCP** (current API reference) — auto-updated every 10-15 days
3. **GitHub MCP/CLI** (source-level fallback) — for questions brain + Context7 don't cover

## How to Write Code

1. **Search brain** for relevant patterns (indicator recipes, similar strategies, gotchas)
2. **Query Context7** for current API signatures if brain doesn't cover it
3. **Use few-shot examples** from CODE files (2-3 validated implementations)
4. **Reason about control flow** before generating (SCoT pattern — think in code structures, not prose)
5. **Template-fill** for IStrategy files; **full generation** for non-strategy code
6. **Always produce tests** alongside implementation code

## How to Test Code

Every implementation task produces **code and tests**:
- **Unit tests** — individual functions and methods
- **Integration tests** — strategy loads in Freqtrade, CCXT calls work with mocks
- **Property tests** — DataFrame operations preserve shape, signals are binary

## Validation Pipeline

```
Stage 1: AST Parse    → Syntax valid? Structure correct?
Stage 2: Import Check → Only allowed modules? No dangerous ops?
Stage 3: Test/Dry-Run → pytest passes? Freqtrade dry-run completes?
```

On failure: extract specific error, feed back, regenerate. **Max 3 rounds** per task.

## Security Guardrails

### Strategy Files (strict)
- **Whitelist, never blacklist** for imports
- No network calls, no filesystem writes, no code execution (exec/eval)
- No serialization (pickle), no system access (subprocess)
- 30-second timeout on dry-run execution

### Non-Strategy Files (relaxed)
- Allow filesystem reads (pathlib, json, csv — needed for data pipelines)
- Allow logging
- Still block: network calls, subprocess, exec/eval, pickle

### Import Whitelist (strategy files)
```python
ALLOWED_IMPORTS = {
    "datetime", "typing", "dataclasses", "enum", "math", "functools",
    "collections", "itertools", "decimal", "logging",
    "numpy", "pandas",
    "talib", "talib.abstract", "technical", "technical.indicators",
    "freqtrade.strategy", "freqtrade.vendor.qtpylib.indicators",
    "freqtrade.persistence",
    "ccxt",
    "pytest", "unittest.mock",
}
```

## File Types
| Type | Purpose | Directory |
|------|---------|-----------|
| SPEC | Design decisions, architecture | `project-brain/specs/` |
| CODE | Validated code patterns, templates, reusable snippets | `project-brain/code/` |
| RULE | Import whitelist, style conventions, testing requirements, guardrails | `project-brain/rules/` |
| LEARN | API references, library gotchas, generation error patterns | `project-brain/learnings/` |
| LOG | Generation success/failure logs, decision rationale | `project-brain/logs/` |
| RESET | Pre-built context packages for specific tasks | `project-brain/reset-files/` |

## Brain Skills
- `/brain-search <query>` — Search fat indexes, return ranked results without opening files
- `/brain-deposit [TYPE] [desc]` — Guided deposit with dedup check
- `/brain-handoff` — Write SESSION-HANDOFF.md immediately
- `/brain-status` — File counts, orphans, index health

## Rules
Session hygiene, fat-index discipline, and ingestion dedup are enforced via `.claude/rules/`. These load automatically every session.

## Inter-Brain Protocol

### Input: CONTEXT-PACK from Orchestrator
```yaml
task_id: "coder-042"
source: orchestrator
target: coder
task_type: implement | test | fix | refactor
```

### Output: RESULT to Orchestrator
```yaml
task_id: "coder-042"
source: coder
status: complete | partial | blocked
confidence: high | medium | low
validation: passed | failed
stages_passed: [ast, imports, tests, dry_run]
```
