# INDEX-MASTER — Coder Brain
<!-- type: INDEX -->
<!-- updated: 2026-02-17 -->
<!-- project: Coder Brain -->
<!-- total-files: 14 -->
<!-- capabilities: code-generation, strategy-implementation, testing, validation, refactoring -->
<!-- input-types: implement, test, fix, refactor -->
<!-- output-types: RESULT, LEARN-candidate -->
<!-- token-budget: 1500 -->
<!-- domain: freqtrade, ccxt, ta-lib, vectorbt, pytest, python -->
<!-- Load this file at the start of every Claude Code session. -->

## How to Use This Index
1. Read this file first in every session.
2. Scan entries below to find what you need.
3. Use `brain.py search "query"` for keyword search OUTSIDE context when possible.

---

## Sub-Indexes
_None yet._

---

## SPEC Files

### SPEC-001
- **Type:** SPEC
- **File:** specs/SPEC-001_coder-brain-architecture.md
- **Tags:** architecture, coder-brain, prover, coding-agent, python, freqtrade, code-generation, validation
- **Links:** LEARN-001, LEARN-002, CODE-001, CODE-002, CODE-003, RULE-001, RULE-002, RULE-003
- **Backlinks:** LEARN-001, LEARN-002
- **Summary:** Architecture spec for the Coder brain — a specialist Python coding agent in the Prover multi-brain system. Defines: position in agent chain (receives CONTEXT-PACK from orchestrator, produces RESULT with validation evidence), three-tier knowledge hierarchy (brain files > Context7 > GitHub), complete Phase 1 file inventory (14 files: 7 LEARNs, 3 CODEs, 3 RULEs, 1 SPEC), write pipeline (brain search → Context7 → few-shot → SCoT → template-fill/full-gen → tests), 3-stage validation pipeline (AST → imports → pytest/dry-run, max 3 rounds), security model (strict whitelist for strategies, relaxed for non-strategy, 30s/512MB limits), inter-brain CONTEXT-PACK/RESULT protocol with YAML format, and 3-phase ingestion roadmap (Phase 1 complete: Freqtrade seed; Phase 2 next: CCXT, VectorBT, Optuna, pytest advanced; Phase 3: error patterns from production).
- **Key decisions:** Template-fill for IStrategy, full generation for non-strategy. Knowledge-first over guess-and-check. Max 3 iteration rounds. Whitelist-only imports.
- **Interface:** Receives CONTEXT-PACK (task_type, acceptance criteria). Returns RESULT (files, validation, discoveries).
- **Known issues:** 6 open questions (inter-brain protocol details, CCXT async/sync, short selling, multi-TF, VectorBT template, exchange scope). Phase 2 not started. ta-lib Windows install problematic.

---

## CODE Files

### CODE-001
- **Type:** CODE
- **File:** code/CODE-001_istrategy-template.md
- **Tags:** freqtrade, IStrategy, template, code-generation, strategy, python
- **Links:** LEARN-001, LEARN-007, RULE-001
- **Backlinks:** CODE-002, CODE-003, RULE-002, RULE-003
- **Summary:** IStrategy template with fill slots for code generation. Fixed structure (imports, class, attributes, order_types) with 12 marked fill slots (STRATEGY_NAME, TIMEFRAME, ROI_TABLE, STOPLOSS, TRAILING_STOP, STARTUP_CANDLE_COUNT, INDICATORS, ENTRY_CONDITIONS, EXIT_CONDITIONS, HYPEROPT_PARAMETERS, INFORMATIVE_PAIRS, ADDITIONAL_IMPORTS). Includes fill slot reference table with required/optional and examples, entry/exit condition pattern library (EMA crossover, RSI filter, ADX gate, BB bounce, MACD histogram, candlestick patterns), and 7 usage rules (never modify structure, whitelist imports, economic thesis required, volume guard mandatory).
- **Key decisions:** Template-fill only — agent fills slots, never modifies structure. Volume > 0 guard mandatory. Economic thesis mandatory.
- **Interface:** Input: fill slot values from task spec. Output: complete IStrategy .py file.
- **Known issues:** Long-only template. Short strategies need enter_short/exit_short columns.

### CODE-002
- **Type:** CODE
- **File:** code/CODE-002_test-scaffolding.md
- **Tags:** testing, pytest, conftest, fixtures, strategy-tests, freqtrade, python
- **Links:** LEARN-001, CODE-001, RULE-003
- **Backlinks:** RULE-003, CODE-003
- **Summary:** Reusable test scaffolding for strategy validation. conftest.py with 5 fixtures (ohlcv_dataframe 500 rows seed 42, flat_dataframe, zero_volume_dataframe, mock_metadata, mock_dataprovider). 8 test patterns: strategy attributes, populate_indicators runs, entry signals binary, exit signals binary, DataFrame shape preserved, no entry on zero volume, flat market handling, startup_candle_count sufficiency. Optional property-based tests with hypothesis (stoploss negative, DataFrame length invariant). Usage: replace strategy_class fixture, run pytest -v.
- **Key decisions:** Seed 42 for deterministic tests. 500 rows covers most indicator warmup periods. Property tests optional (add 10s per test).
- **Interface:** Input: strategy class. Output: test results (pass/fail per pattern).
- **Known issues:** Mock DataProvider doesn't simulate real informative data. Hypothesis adds latency.

### CODE-003
- **Type:** CODE
- **File:** code/CODE-003_sample-validated-strategy.md
- **Tags:** freqtrade, strategy, example, validated, EMA-crossover, RSI, python
- **Links:** CODE-001, LEARN-001, LEARN-007, RULE-001
- **Backlinks:** _(none)_
- **Summary:** Known-working EMACrossoverRSI strategy as few-shot example. Entry: fast EMA(9) crosses above slow EMA(21) AND price > EMA(50) AND RSI < 70 AND ADX > 20 AND volume > 0. Exit: EMA crossover down OR RSI > 80. Includes trailing stop Mode 4 (static until +3% offset, then trail at -2%), hyperopt parameters (buy_rsi_max, sell_rsi_min), Bollinger Bands computed for reference. Passes all 7 CODE-002 mandatory tests. Demonstrates 8 patterns: EMA crossover, RSI filter, trend strength gate, trend direction filter, volume guard, hyperopt parameter, trailing stop, multi-output indicator.
- **Key decisions:** Demonstration only — not profitable. Simple enough for few-shot prompting. Mode 4 trailing as recommended default.
- **Interface:** N/A (example). Used as few-shot input for code generation.
- **Known issues:** Long-only. No informative pairs. No custom callbacks.

---

## RULE Files

### RULE-001
- **Type:** RULE
- **File:** rules/RULE-001_import-whitelist.md
- **Tags:** security, imports, whitelist, validation, strategy, python, guardrails
- **Links:** LEARN-002, CODE-001
- **Backlinks:** CODE-001, CODE-003
- **Summary:** Import whitelist for generated code — the primary security boundary. Two tiers: STRICT (strategy files) allows only safe stdlib subset + numpy/pandas + talib + freqtrade + ccxt + pytest; RELAXED (non-strategy) additionally allows pathlib, json, csv, os, yaml, vectorbt, optuna, hypothesis. BLOCKED always: network (requests/urllib), code execution (exec/eval), serialization (pickle), system access (subprocess). Includes AST-based validation function (validate_imports). 5 rules: whitelist-never-blacklist, strategies strict, non-strategy relaxed, test imports only in test files, when in doubt reject.
- **Key decisions:** Whitelist-only. Strategy files cannot make network calls or write files. ccxt allowed in strategies (read-only) but flagged for monitoring.
- **Interface:** Input: source code string + is_strategy bool. Output: list of violations (empty = pass).
- **Known issues:** pandas-ta module name not listed. ccxt in strategies technically risky. freqtrade.persistence allows DB access.

### RULE-002
- **Type:** RULE
- **File:** rules/RULE-002_code-style-conventions.md
- **Tags:** style, conventions, python, naming, formatting, freqtrade, code-generation
- **Links:** CODE-001, LEARN-001
- **Backlinks:** _(none)_
- **Summary:** Code style rules for all generated code. Python 3.10+, PEP 8, type hints on all signatures, Google-style docstrings. Naming: PascalCase classes, snake_case functions/variables/columns, UPPER_SNAKE constants, buy_/sell_ prefix for hyperopt params. DataFrame columns must include distinguishing parameter (ema_9 not ema). Import order: freqtrade → indicators → stdlib → logger. Strategy file structure order: docstring → imports → class → attributes → hyperopt → informative_pairs → populate_indicators → entry_trend → exit_trend → callbacks. Signal conditions: one condition per line with & operator. Comments: WHY not WHAT, economic thesis mandatory in class docstring.
- **Key decisions:** Column naming includes period (ema_9 not ema). 120 char allowed for signal conditions (exception to PEP 8 79).
- **Interface:** N/A (behavioral rule). Consumed by code generation pipeline.
- **Known issues:** PEP 8 line length may be too restrictive for complex conditions.

### RULE-003
- **Type:** RULE
- **File:** rules/RULE-003_testing-requirements.md
- **Tags:** testing, requirements, pytest, validation, strategy, guardrails, pipeline
- **Links:** CODE-002, CODE-001, LEARN-002
- **Backlinks:** _(none)_
- **Summary:** Mandatory testing and validation requirements. 3-stage pipeline: AST parse → import check (RULE-001) → pytest/dry-run. 7 mandatory tests per strategy (from CODE-002). Max 3 iteration rounds on failure. Error feedback loop: extract error → identify cause → fix specific issue → re-run. 30-second timeout per test. 512MB memory limit. Additional tests required when using informative pairs, custom callbacks, hyperopt parameters, or multiple timeframes.
- **Key decisions:** Every task produces code AND tests. Max 3 fix rounds. 30s timeout, 512MB memory. AST parse before expensive tests.
- **Interface:** Input: generated code. Output: pass/fail with error details.
- **Known issues:** Freqtrade dry-run requires installation. Property tests optional. No live comparison test yet.

---

## LEARN Files

### LEARN-001
- **Type:** LEARN
- **File:** learnings/LEARN-001_freqtrade-istrategy-technical-reference.md
- **Tags:** freqtrade, IStrategy, trading, python, callbacks, hyperopt, signals, indicators
- **Links:** SPEC-001
- **Backlinks:** LEARN-002
- **Summary:** Complete technical reference for Freqtrade's IStrategy interface. Covers: 3 required methods (populate_indicators/entry_trend/exit_trend) with exact signatures, DataFrame OHLCV columns, 15+ optional callback methods with full signatures (custom_stoploss, custom_exit, adjust_trade_position, leverage, etc.), parameter optimization interface (IntParameter/DecimalParameter/BooleanParameter/CategoricalParameter), signal column conventions, trailing stop mechanics, ROI table format, indicator libraries (TA-Lib, technical, pandas-ta), complete signal pattern example, and 10 code generation constraints.
- **Key decisions:** Template-fill for IStrategy (fill only populate method bodies); hyperopt parameters cannot be used in populate_indicators; always include volume > 0 guard.
- **Interface:** N/A (reference). Consumed by code generation pipeline.
- **Known issues:** TA-Lib problematic on Windows. Freqtrade crypto-focused. startup_candle_count must be ≥200.

### LEARN-002
- **Type:** LEARN
- **File:** learnings/LEARN-002_llm-code-generation-patterns.md
- **Tags:** code-generation, LLM, validation, security, sandbox, prompting, few-shot, SCoT, iteration
- **Links:** SPEC-001, LEARN-001
- **Backlinks:** _(none)_
- **Summary:** Quantitative research synthesis on LLM code generation for trading strategies. Prompting: SCoT +13.79% Pass@1, few-shot ~80% over zero-shot, prompt format varies 40%. Iteration: 3-5 rounds optimal, GPT-4o-mini 53%→75%, Gemini-flash 57%→89%. Validation: AST hallucination detection, Bandit security linting, smolagents LocalPythonExecutor (best fit for strategy validation), 4-tier sandbox hierarchy. Cross-project finding: LLM API hallucination is the consistent failure mode — every successful project required a validation layer. NexusTrade JSON-out pattern (24K users). Template-based generation recommended (eliminates structural errors).
- **Key decisions:** Knowledge-first beats guess-and-check; template-fill eliminates largest error classes; whitelist imports never blacklist; smolagents as validation model; max 3-5 iterations.
- **Interface:** N/A (research). Informs write + validation pipeline.
- **Known issues:** Academic benchmarks may differ from real-world. smolagents HuggingFace-specific. All APIs point-in-time Feb 2026.

### LEARN-003
- **Type:** LEARN
- **File:** learnings/LEARN-003_freqtrade-bot-configuration.md
- **Tags:** freqtrade, configuration, config-json, exchange, dry-run, stake, pairlist, fees, order-types
- **Links:** LEARN-001, LEARN-004
- **Backlinks:** LEARN-004
- **Summary:** Complete reference for Freqtrade's config.json structure. Covers: config loading and precedence (CLI > env vars > config > strategy), required parameters (max_open_trades, stake_currency, stake_amount, dry_run, minimal_roi, stoploss), exchange setup (ccxt_config, pair naming conventions, websocket), trading modes (spot/margin/futures with margin_mode), dry-run vs live differences (separate DBs, dry_run_wallet as float or dict), stake amount management (dynamic "unlimited" splitting, tradable_balance_ratio, available_capital), order types and pricing configuration (price_side "same"/"other", order book usage), and 9 documented gotchas (env var override, add_config_files precedence, Strategy Override one-way).
- **Key decisions:** None — reference material. Config always overrides strategy (one-way). Market orders need price_side "other" for realistic backtesting.
- **Interface:** N/A (reference). Consumed by config generation tasks.
- **Known issues:** Coingecko rate limiting on some IPs. stoploss_on_exchange with wide stoploss may fail exchange limits.

### LEARN-004
- **Type:** LEARN
- **File:** learnings/LEARN-004_freqtrade-bot-lifecycle.md
- **Tags:** freqtrade, lifecycle, trading-loop, stoploss, trailing-stop, roi, callbacks, startup, shutdown
- **Links:** LEARN-001, LEARN-003
- **Backlinks:** _(none)_
- **Summary:** Documents Freqtrade bot startup sequence (8 steps), main trading loop (11 steps running every 5s), exit priority order (stoploss > ROI > exit signal > custom_exit > custom_stoploss), 4 trailing stoploss modes with examples (basic trailing, positive trailing, offset trailing, static-until-offset), stoploss on exchange mechanics (interval, limit ratio, emergency exit), ROI table format and special cases, complete callback table (18 callbacks with when/purpose), and critical backtesting vs live differences (populate_* called once per pair in backtest vs every iteration in live — #1 source of performance mismatch).
- **Key decisions:** None — reference material. Mode 3 trailing (offset) recommended for locking profits.
- **Interface:** N/A (reference). Consumed by strategy generation and testing tasks.
- **Known issues:** Cannot change trailing stoploss on open trades if already adjusted. process_only_new_candles=false creates high load.

### LEARN-005
- **Type:** LEARN
- **File:** learnings/LEARN-005_freqtrade-data-handling.md
- **Tags:** freqtrade, data, download, timeframes, pairlist, informative-pairs, merge, startup-candle-count, lookahead
- **Links:** LEARN-001, LEARN-006
- **Backlinks:** LEARN-006
- **Summary:** Reference for Freqtrade data pipeline. Covers: download-data command (incremental downloads, pairs regex, timeframe options), 4 supported formats (json/jsongz/feather/parquet — feather is default, hdf5 removed), pair list config (StaticPairList vs VolumePairList, chaining), informative pairs (informative_pairs() method, dp.get_pair_dataframe(), merge_informative_pair() mechanics — timestamp alignment, forward-fill, column renaming with TF suffix), data directory structure (underscore naming), startup_candle_count (why needed, multi-TF calculation formula: indicator_period * TF_ratio, recursive-analysis validation), and lookahead bias prevention (shift(1), vectorized ops only, detection commands).
- **Key decisions:** None — reference. Use StaticPairList for reproducible backtests. startup_candle_count = 2x-4x longest indicator period.
- **Interface:** N/A (reference). Consumed by data pipeline and strategy generation tasks.
- **Known issues:** VolumePairList not reproducible for backtesting. Exchange candle limits in live may differ from backtest.

### LEARN-006
- **Type:** LEARN
- **File:** learnings/LEARN-006_freqtrade-backtesting-cli.md
- **Tags:** freqtrade, backtesting, cli, timerange, results, metrics, export, pitfalls
- **Links:** LEARN-001, LEARN-005
- **Backlinks:** _(none)_
- **Summary:** Complete backtesting CLI reference. Covers: all key parameters (--strategy, --strategy-list, --timerange, --timeframe-detail, --export, --fee, --cache, --breakdown), timerange format (YYYYMMDD-YYYYMMDD, open-ended), --timeframe-detail for intra-candle simulation (exits/callbacks at detail TF), result metrics (profit factor, SQN, Sortino, Sharpe, Calmar, expectancy, drawdown), result interpretation guidelines (good signs: PF>1.5, SQN>2.0; red flags: >80% win rate with few trades), export and analysis workflow, 7 backtesting assumptions/limitations (no slippage, no order book, flat fees, full dataset at once), and 7 common pitfalls (lookahead bias, insufficient startup candles, overfitting, VolumePairList, rejected signals).
- **Key decisions:** None — reference. Always run lookahead-analysis and recursive-analysis before going live.
- **Interface:** N/A (reference). Consumed by backtesting tasks.
- **Known issues:** Results may differ between Freqtrade versions. Cache auto-disabled for open-ended timeranges.

### LEARN-007
- **Type:** LEARN
- **File:** learnings/LEARN-007_talib-indicator-reference.md
- **Tags:** ta-lib, indicators, technical-analysis, freqtrade, qtpylib, technical-library, python
- **Links:** LEARN-001
- **Backlinks:** _(none)_
- **Summary:** Complete ta-lib indicator reference for Freqtrade strategy generation. Covers: Abstract API vs Function API (Abstract preferred — auto-selects price inputs), Freqtrade column assignment pattern (single-output direct assign, multi-output unpack), 8 overlap studies (SMA/EMA/DEMA/TEMA/WMA/BBANDS/SAR/HT_TRENDLINE with signatures/defaults), 12 momentum indicators (RSI/MACD/STOCH/STOCHRSI/CCI/ADX/PLUS_DI/MINUS_DI/WILLR/MOM/ROC/MFI), 3 volume indicators (AD/ADOSC/OBV), 3 volatility indicators (ATR/NATR/TRANGE), top 10 candlestick patterns (CDL* functions returning integers 100/-100/0), qtpylib helpers (bollinger_bands, typical_price, heikinashi, crossed_above/below — critical for signals), `technical` library indicators (ichimoku, VWAP, hull MA, SSL channel), and 6 gotchas (NaN propagation, startup_candle_count 2x-4x rule, integer CDL returns, Abstract API auto-selection, STOCHRSI range, performance — never row-by-row).
- **Key decisions:** None — reference. Always use Abstract API in strategies. Compute ALL indicators in populate_indicators(), never in populate_entry/exit_trend().
- **Interface:** N/A (reference). Primary indicator lookup for code generation.
- **Known issues:** ta-lib Windows installation needs pre-built binaries. BBANDS default timeperiod=5 is unusually short (use 20). SAR whipsaws in sideways markets.

---

## LOG Files
_None yet._
