# SPEC-001: Coder Brain Architecture
<!-- type: SPEC -->
<!-- created: 2026-02-17 -->
<!-- tags: architecture, coder-brain, prover, coding-agent, python, freqtrade, code-generation, validation -->
<!-- links: LEARN-001, LEARN-002, CODE-001, CODE-002, CODE-003, RULE-001, RULE-002, RULE-003 -->

## Context

The Coder brain is a specialist Python coding agent in the Prover multi-brain system (see agentic-brain SPEC-001/SPEC-002 for full system architecture). It receives implementation plans from upstream Architect/Planner agents and produces working, tested code for the trading infrastructure stack.

## Decision

### Position in Agent Chain

```
User
 └─▸ Orchestrator
      ├─▸ Architect Agent  → System architecture, component interfaces
      ├─▸ Planner Agent    → Breaks designs into tasks with acceptance criteria
      ├─▸ Coder Agent      → Writes, tests, validates code (THIS BRAIN)
      ├─▸ Donchian Brain   → Trading thesis, strategy parameters
      └─▸ Frontend Brain   → Visualization, HMI
```

**Receives:** CONTEXT-PACK with task_type (implement|test|fix|refactor), acceptance criteria, file paths, function signatures.
**Produces:** RESULT with files written, validation evidence, discovered knowledge.
**Does NOT:** Make architectural decisions, devise trading logic, choose approaches.

### Knowledge Hierarchy

1. **Brain files** (first source) — project conventions, validated patterns, gotchas
2. **Context7 MCP** (current API reference) — auto-updated every 10-15 days
3. **GitHub MCP/CLI** (source-level fallback)

### Brain File Inventory (Phase 1 — Seed)

| File | Type | Content |
|------|------|---------|
| LEARN-001 | Reference | Freqtrade IStrategy interface — methods, callbacks, hyperopt |
| LEARN-002 | Research | LLM code generation patterns — prompting, iteration, validation |
| LEARN-003 | Reference | Freqtrade bot configuration — config.json, exchange, dry-run |
| LEARN-004 | Reference | Freqtrade bot lifecycle — loop, stoploss, ROI, callbacks |
| LEARN-005 | Reference | Freqtrade data handling — download, merge, lookahead prevention |
| LEARN-006 | Reference | Freqtrade backtesting CLI — commands, metrics, pitfalls |
| LEARN-007 | Reference | ta-lib indicators — signatures, defaults, qtpylib, gotchas |
| CODE-001 | Template | IStrategy template with 12 fill slots |
| CODE-002 | Template | Test scaffolding — conftest.py, 8 test patterns |
| CODE-003 | Example | Validated EMACrossoverRSI strategy (few-shot) |
| RULE-001 | Guardrail | Import whitelist (strict + relaxed tiers) |
| RULE-002 | Convention | Code style — naming, structure, formatting |
| RULE-003 | Guardrail | Testing requirements — 3-stage pipeline, 7 mandatory tests |

### Write Pipeline

```
1. Brain search      → Find relevant patterns, gotchas, templates
2. Context7 query    → Get current API signatures if brain doesn't cover it
3. Few-shot load     → Pull CODE-003 or similar validated example
4. SCoT reasoning    → Think in code structures, not prose (+13.79% Pass@1)
5. Template-fill     → For IStrategy: fill CODE-001 slots
   Full generation   → For non-strategy code
6. Produce tests     → Using CODE-002 patterns alongside implementation
```

### Validation Pipeline

```
Stage 1: AST Parse       → Syntax valid? Structure correct?
Stage 2: Import Check     → RULE-001 whitelist (strict for strategies)
Stage 3: Test / Dry-Run   → pytest (CODE-002 patterns) + Freqtrade backtesting
```

On failure: extract error → fix specific issue → retry. **Max 3 rounds.**

### Security Model

| Context | Policy | Rationale |
|---------|--------|-----------|
| Strategy files | STRICT whitelist (RULE-001) | No network, no filesystem, no exec, no pickle |
| Non-strategy files | RELAXED whitelist | Filesystem OK, network only via ccxt |
| All generated code | 30s timeout, 512MB memory | Resource limits prevent runaway execution |
| Imports | Whitelist-never-blacklist | Unknown = rejected |

### Inter-Brain Protocol

**Input: CONTEXT-PACK**
```yaml
task_id: "coder-042"
source: orchestrator
target: coder
task_type: implement | test | fix | refactor
plan_ref: "architect-plan-017"
acceptance_criteria:
  - "Strategy generates entry/exit signals"
  - "All 7 mandatory tests pass"
  - "Import whitelist clean"
token_budget: 750
```

**Output: RESULT**
```yaml
task_id: "coder-042"
source: coder
status: complete | partial | blocked
confidence: high | medium | low
validation: passed | failed
stages_passed: [ast, imports, tests, dry_run]
files_written:
  - "strategies/donchian_breakout.py"
  - "tests/test_donchian_breakout.py"
discoveries: []
token_budget: 1500
```

### Ingestion Roadmap

**Phase 1 (COMPLETE):** Freqtrade seed — IStrategy, config, lifecycle, data, backtesting, ta-lib, templates, tests, rules.

**Phase 2 (Next):**
- CCXT unified API patterns (async/sync, exchange quirks, error handling)
- VectorBT vectorized backtesting API
- Optuna hyperparameter optimization + Freqtrade hyperopt integration
- pytest advanced patterns (parametrize, mocking exchange calls)

**Phase 3 (Accumulate):**
- Error pattern library (grows from production use)
- Validated code snippets (grows from successful generations)
- Exchange-specific gotchas (grows from live testing)

## Open Questions

1. Architect/Planner → Coder communication: exact CONTEXT-PACK fields for each task_type?
2. CCXT async vs sync — which pattern for data pipelines?
3. Short selling support — when to add enter_short/exit_short to template?
4. Multi-timeframe data alignment — how to handle in template?
5. VectorBT validation template design?
6. CCXT exchange scope — which exchanges first?

## Known Issues
- Freqtrade dry-run validation requires Freqtrade installation + exchange data.
- ta-lib Windows installation problematic (needs pre-built binaries).
- CODE-003 example is long-only. Short strategy template needed for futures.
- Phase 2 ingestion not yet started.
