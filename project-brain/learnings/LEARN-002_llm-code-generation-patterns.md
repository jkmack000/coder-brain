# LEARN-002 — LLM Code Generation Patterns for Trading Strategies
<!-- type: LEARN -->
<!-- tags: code-generation, LLM, validation, security, sandbox, prompting, few-shot, SCoT, iteration -->
<!-- created: 2026-02-17 -->
<!-- source: Web research across 27+ academic papers and open-source projects -->
<!-- links: SPEC-001, LEARN-001 -->

## Purpose

Quantitative research synthesis on LLM code generation patterns, validation toolchains, and security sandboxing — specifically for AI-generated trading strategies. Informs the write and validation pipeline.

## Prompting Patterns (Quantitative)

### SCoT — Structured Chain-of-Thought (ACM TOSEM 2024)
Replace natural-language reasoning with **programming structures** (sequential, branch, loop) as intermediate reasoning. LLM outlines strategy logic as pseudocode with explicit control flow, then generates implementation. **+13.79% Pass@1** over standard CoT.

### Skeleton-of-Thought (ICLR 2024)
Two-phase: generate function signatures/docstrings first, then implement each body. Decomposes complex generation into manageable chunks. SoT-R variant adds a router to decide when skeleton approach helps.

### Few-Shot Impact
2-3 examples of complete working strategies improve accuracy by **~80% over zero-shot**. Diminishing returns after 2-3 examples — additional examples consume tokens without proportional quality gains.

### Prompt Format Sensitivity
GPT-3.5-turbo code generation **varies up to 40%** based solely on prompt format (Markdown vs JSON vs YAML vs plaintext). Structural formatting matters as much as wording.

### Recommended Prompting Stack
1. System prompt establishing LLM as framework expert
2. 2-3 few-shot examples of complete working strategies
3. SCoT-style reasoning: outline as pseudocode first, then implement
4. Structured output format (template or JSON) to constrain shape

## Iterative Refinement (Quantitative)

### LLMLOOP (ICSME 2025)
Five sequential feedback loops: compilation → static analysis → test execution → mutation testing → coverage. **pass@1: 71% → 80.85%** (+9.2pp). **pass@10: baseline → 90.24%** (+14pp).

### Self-Refine (NeurIPS 2023)
Three-step cycle: generate → self-critique → refine. Google Research (2025): **cuts code errors by 30%**.

### Code Repair as Exploration-Exploitation (NeurIPS 2024)
Early iterations: **higher temperature** (explore diverse fixes). Later iterations: **lower temperature** (exploit best approach).

### Iteration Limits
**3-5 iterations** is the practical sweet spot. Beyond 5, LLMs oscillate between fixes or introduce new bugs. Model-specific:
- GPT-4o-mini: 53.62% → **75.38%** (+21.76pp)
- Gemini-2.0-flash: 57.33% → **89.33%** (+32pp)

## Validation Toolchain

### AST Hallucination Detection (Jan 2026)
Detects: deprecated functions, non-existent parameters, phantom API calls. Correction via **structural trimming** — AST parser prunes hallucinated segments.

### Security Analysis Tools
- **Bandit**: Python security linter with built-in dangerous import blacklists
- **IRIS** (arXiv 2405.17238): Hybrid traditional static analysis + LLM reasoning for vulnerability detection
- **LLM-CSEC finding**: Even with explicit "secure code" prompting, median LLM generation contains multiple high-severity vulnerabilities

### smolagents LocalPythonExecutor
**Most directly applicable model** for trading strategy validation (HuggingFace). AST-walking interpreter — never calls `exec()`. Imports disabled by default (explicit whitelist required). Submodule access control (`random._os` exploit path blocked). Operation count limits prevent infinite loops. Open-source at `huggingface/smolagents/local_python_executor.py`.

### 4-Tier Sandbox Hierarchy
| Tier | Technology | Isolation | Trading Use |
|------|-----------|-----------|-------------|
| 1 | RestrictedPython | Process-level | Insufficient alone — bypassable |
| 2 | smolagents LocalPythonExecutor | AST interpreter | **Best fit for strategy validation** |
| 3 | gVisor / Docker | Kernel-level | Full backtest execution |
| 4 | Firecracker MicroVMs | Hardware-level | Production live trading |

### Recommended Iteration Pipeline
```
Stage 1: Generate (fill template)
Stage 2: AST-parse (syntax, forbidden imports) → fail? regenerate
Stage 3: Static analysis (Bandit + custom rules) → fail? regenerate
Stage 4: Dry-run (10 candles) → fail? regenerate
Stage 5: Full backtest → fail? regenerate
Limits:  Max 3 iterations per stage, 5 total attempts
```

### Import Security
**Whitelist approach, never blacklist.** Minimum dangerous blocklist: `os`, `subprocess`, `socket`, `sys`, `shutil`, `importlib`, `ctypes`, `multiprocessing`, `threading`, `signal`, `code`, `compile`, `exec`, `eval`, `__import__`, `pickle`. Also block submodule traversal (`random._os`). Block network: `urllib`, `requests`, `http`, `httpx`, `aiohttp`.

## Cross-Project Finding: LLM API Hallucination

**The consistent failure mode across all projects is LLM hallucination of framework APIs.** LLMs generate calls to non-existent methods, use deprecated APIs, and misunderstand parameter signatures. **Every successful project required a validation/gatekeeper layer.** No project achieved reliability by prompting alone.

This is the empirical justification for the knowledge-first architecture: pre-ingested framework knowledge eliminates the largest error class.

## NexusTrade: JSON-Out Pattern
Production system (24,000+ users). LLM produces structured JSON specification; Rust-based engine executes it. **LLM never generates executable code.** Eliminates all code safety concerns — output is data, not code. Extreme version of template-based generation.

## Open-Source Strategy Generation Projects

| Project | Framework | Key Pattern |
|---------|-----------|-------------|
| ai-quant-code-generator | Alpaca + Backtrader | NL to code, framework-constrained prompting |
| backtrader_copilot | Backtrader | System prompt as Backtrader expert |
| ai-trader | Backtrader + MCP | Config-driven, Claude MCP integration |
| TradingAgents | Multi-agent | Structured LLM debates for strategy selection |
| EMNLP 2025 paper | Custom | 3-stage: alpha generation → multi-agent eval → dynamic weights. **53.17% return on SSE50** |

## Template-Based Generation (Recommended)

Provide skeleton with marked slots; LLM fills only variable parts:
- Template provides: class skeleton, imports, method stubs, data feed, backtest runner
- LLM fills: `populate_indicators` body, entry/exit trend bodies, hyperparameter values
- **Eliminates**: missing imports, structural errors, lifecycle bugs
- **Remaining errors**: logic bugs in filled sections only

## Known Issues

- SCoT numbers are from academic benchmarks — real-world improvement may differ
- smolagents is HuggingFace-specific — may need adaptation for standalone use
- NexusTrade JSON-out eliminates code flexibility (can't express arbitrary logic)
- EMNLP 2025 paper's 53.17% return is a single backtest period — not validated via CPCV
- All framework APIs evolve — analysis is point-in-time Feb 2026
