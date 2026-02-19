# INDEX-MASTER — Coder Brain
<!-- type: INDEX -->
<!-- updated: 2026-02-19 -->
<!-- project: Coder Brain -->
<!-- total-files: 19 -->
<!-- capabilities: code-generation, strategy-implementation, testing, validation, refactoring -->
<!-- input-types: implement, test, fix, refactor -->
<!-- output-types: RESULT, LEARN-candidate -->
<!-- token-budget: 1500 -->
<!-- domain: freqtrade, ccxt, ta-lib, vectorbt, pytest, python -->
<!-- format: compressed-v1 (LEARN-046) -->
<!-- entry: ID|tags|→outlinks|←inlinks|summary|d:decisions|i:interface|!issues -->
<!-- abbrev: L=LEARN S=SPEC C=CODE R=RULE G=LOG →=links ←=backlinks ∅=none d:=decisions i:=interface !=issues -->

## How to Use This Index
1. Read this file first in every session.
2. Scan entries below to find what you need.
3. Use `brain.py search "query"` for keyword search OUTSIDE context when possible.

---

## Sub-Indexes
_None yet._

---

## SPEC Files

S001|architecture,coder-brain,prover,coding-agent,python,freqtrade,code-generation,validation|→L001,L002,C001,C002,C003,R001,R002,R003|←L001,L002,L008,L009,L010,L011|Architecture spec for the Coder brain — specialist Python coding agent in Prover multi-brain system. Position in agent chain (receives CONTEXT-PACK, produces RESULT with validation evidence), three-tier knowledge hierarchy (brain>Context7>GitHub), Phase 1 file inventory (14 files), write pipeline (brain search→Context7→few-shot→SCoT→template-fill/full-gen→tests), 3-stage validation (AST→imports→pytest, max 3 rounds), security model (strict whitelist strategies, relaxed non-strategy, 30s/512MB), inter-brain CONTEXT-PACK/RESULT protocol (YAML), 3-phase ingestion roadmap.|d:template-fill for IStrategy, full-gen for non-strategy; knowledge-first>guess-and-check; max 3 iterations; whitelist-only imports|i:receives CONTEXT-PACK (task_type, acceptance criteria). Returns RESULT (files, validation, discoveries)|!6 open Qs (protocol details, CCXT async/sync, short selling, multi-TF, VectorBT template, exchange scope). Phase 2 not started. ta-lib Windows problematic.

---

## CODE Files

C001|freqtrade,IStrategy,template,code-generation,strategy,python|→L001,L007,R001|←C002,C003,R001,R002,R003,S001|IStrategy template with 12 fill slots (STRATEGY_NAME, TIMEFRAME, ROI_TABLE, STOPLOSS, TRAILING_STOP, STARTUP_CANDLE_COUNT, INDICATORS, ENTRY_CONDITIONS, EXIT_CONDITIONS, HYPEROPT_PARAMETERS, INFORMATIVE_PAIRS, ADDITIONAL_IMPORTS). Fill slot reference table, entry/exit condition pattern library (EMA crossover, RSI filter, ADX gate, BB bounce, MACD histogram, candlestick), 7 usage rules.|d:template-fill only — agent fills slots, never modifies structure; volume>0 mandatory; economic thesis mandatory|i:input: fill slot values from task spec. Output: complete IStrategy .py file|!long-only template. Short strategies need enter_short/exit_short.

C002|testing,pytest,conftest,fixtures,strategy-tests,freqtrade,python|→L001,C001,R003|←L010,R003,S001|Reusable test scaffolding. conftest.py: 5 fixtures (ohlcv_dataframe 500 rows seed 42, flat_dataframe, zero_volume_dataframe, mock_metadata, mock_dataprovider). 8 test patterns: attributes, populate_indicators, entry/exit signals binary, shape preserved, no entry zero volume, flat market, startup_candle_count. Optional hypothesis property tests.|d:seed 42 deterministic; 500 rows covers most warmup; property tests optional (+10s)|i:input: strategy class. Output: pass/fail per pattern|!mock DataProvider doesn't simulate real informative data. Hypothesis adds latency.

C003|freqtrade,strategy,example,validated,EMA-crossover,RSI,python|→C001,L001,L007,R001|←S001|Known-working EMACrossoverRSI as few-shot example. Entry: EMA(9) crosses above EMA(21) AND price>EMA(50) AND RSI<70 AND ADX>20 AND volume>0. Exit: EMA crossover down OR RSI>80. Trailing stop Mode 4, hyperopt params, passes all 7 CODE-002 tests. Demonstrates 8 patterns.|d:demonstration only — not profitable; simple enough for few-shot; Mode 4 trailing as default|i:N/A (example). Used as few-shot input for code generation|!long-only. No informative pairs. No custom callbacks.

---

## RULE Files

R001|security,imports,whitelist,validation,strategy,python,guardrails|→L002,C001|←C001,C003,S001|Import whitelist — primary security boundary. STRICT (strategies): safe stdlib+numpy/pandas+talib+freqtrade+ccxt+pytest. RELAXED (non-strategy): +pathlib,json,csv,os,yaml,vectorbt,optuna,hypothesis. BLOCKED always: network, exec/eval, pickle, subprocess. AST-based validate_imports function. 5 rules.|d:whitelist-only; strategies no network/write; ccxt allowed but monitored|i:input: source code+is_strategy bool. Output: violations list (empty=pass)|!pandas-ta not listed. ccxt in strategies risky. freqtrade.persistence allows DB.

R002|style,conventions,python,naming,formatting,freqtrade,code-generation|→C001,L001|←S001|Code style for generated code. Python 3.10+, PEP 8, type hints, Google docstrings. Naming: PascalCase classes, snake_case funcs/vars/columns, UPPER_SNAKE constants, buy_/sell_ hyperopt prefix. DataFrame columns include period (ema_9 not ema). Import order: freqtrade→indicators→stdlib→logger. Signal conditions: one per line with &. Comments: WHY not WHAT, economic thesis in docstring.|d:column naming includes period; 120 char for signal conditions (PEP 8 exception)|!PEP 8 line length may be too restrictive for complex conditions.

R003|testing,requirements,pytest,validation,strategy,guardrails,pipeline|→C002,C001,L002|←C002,L008,L009,L010,S001|Mandatory validation: 3-stage pipeline (AST parse→import check R001→pytest/dry-run). 7 mandatory tests per strategy (CODE-002). Max 3 iteration rounds. Error feedback loop. 30s timeout, 512MB memory. Additional tests for informative pairs, custom callbacks, hyperopt, multi-TF.|d:every task produces code AND tests; max 3 fix rounds; 30s/512MB; AST before expensive tests|i:input: generated code. Output: pass/fail with error details|!freqtrade dry-run requires installation. Property tests optional. No live comparison.

---

## LEARN Files

L001|freqtrade,IStrategy,trading,python,callbacks,hyperopt,signals,indicators|→S001|←C001,C002,C003,L002,L003,L004,L005,L006,L007,L008,L009,L011,R002,S001 (14←hub)|Complete IStrategy technical reference. 3 required methods (populate_indicators/entry_trend/exit_trend), DataFrame OHLCV columns, 15+ optional callbacks (custom_stoploss, custom_exit, adjust_trade_position, leverage, etc.), parameter optimization (Int/Decimal/Bool/CategoricalParameter), signal conventions, trailing stop mechanics, ROI table, indicator libraries (TA-Lib, technical, pandas-ta), 10 code generation constraints.|d:template-fill for IStrategy; hyperopt params cannot be in populate_indicators; always volume>0 guard|!ta-lib Windows problematic. Freqtrade crypto-focused. startup_candle_count≥200.

L002|code-generation,LLM,validation,security,sandbox,prompting,few-shot,SCoT,iteration|→S001,L001|←R001,R003,S001|Quantitative research on LLM code generation for trading. SCoT +13.79% Pass@1, few-shot ~80% over zero-shot, prompt format varies 40%. Iteration 3-5 rounds optimal. Validation: AST hallucination detection, Bandit linting, smolagents LocalPythonExecutor. Cross-project: LLM API hallucination is consistent failure — every project needed validation layer. Template-based generation recommended.|d:knowledge-first>guess-and-check; template-fill eliminates largest error classes; whitelist>blacklist; max 3-5 iterations|!academic benchmarks may differ. smolagents HuggingFace-specific. Feb 2026 point-in-time.

L003|freqtrade,configuration,config-json,exchange,dry-run,stake,pairlist,fees,order-types|→L001,L004|←L004,L011|Complete config.json reference. Loading precedence (CLI>env>config>strategy), required params, exchange setup (ccxt_config, pairs, websocket), trading modes (spot/margin/futures), dry-run vs live, stake management (dynamic "unlimited", tradable_balance_ratio), order types/pricing (price_side same/other), 9 gotchas.|d:none — reference. Config overrides strategy (one-way). Market orders need price_side "other" for backtesting|!coingecko rate limiting. stoploss_on_exchange may fail exchange limits.

L004|freqtrade,lifecycle,trading-loop,stoploss,trailing-stop,roi,callbacks,startup,shutdown|→L001,L003|←L003|Bot startup (8 steps), main loop (11 steps/5s), exit priority (stoploss>ROI>exit signal>custom_exit>custom_stoploss), 4 trailing modes with examples, stoploss on exchange mechanics, ROI table, 18 callbacks table, critical: populate_* called once/pair in backtest vs every iteration live (#1 performance mismatch).|d:none — reference. Mode 3 trailing (offset) recommended|!cannot change trailing on open trades if already adjusted. process_only_new_candles=false high load.

L005|freqtrade,data,download,timeframes,pairlist,informative-pairs,merge,startup-candle-count,lookahead|→L001,L006|←L006|Data pipeline reference. download-data command, 4 formats (json/jsongz/feather/parquet — feather default), pair list config (Static vs Volume, chaining), informative pairs (method, dp.get_pair_dataframe, merge_informative_pair mechanics), startup_candle_count (multi-TF formula: indicator_period×TF_ratio), lookahead bias prevention (shift(1), vectorized only, detection commands).|d:none — reference. StaticPairList for reproducible backtests. startup_candle_count=2x-4x longest indicator|!VolumePairList not reproducible. Exchange candle limits may differ live.

L006|freqtrade,backtesting,cli,timerange,results,metrics,export,pitfalls|→L001,L005|←L005,L009|Complete backtesting CLI reference. Parameters (--strategy, --timerange, --timeframe-detail, --export, --fee), result metrics (PF, SQN, Sortino, Sharpe, Calmar, expectancy, drawdown), interpretation (good: PF>1.5, SQN>2.0; red flags: >80% win rate few trades), 7 assumptions/limitations, 7 pitfalls (lookahead, startup candles, overfitting).|d:none — reference. Always run lookahead-analysis and recursive-analysis before live|!results may differ between FT versions. Cache auto-disabled open-ended timeranges.

L007|ta-lib,indicators,technical-analysis,freqtrade,qtpylib,technical-library,python|→L001|←C001,C003|Complete ta-lib indicator reference. Abstract vs Function API (Abstract preferred). 8 overlap (SMA/EMA/DEMA/TEMA/WMA/BBANDS/SAR/HT_TRENDLINE), 12 momentum (RSI/MACD/STOCH/STOCHRSI/CCI/ADX/PLUS_DI/MINUS_DI/WILLR/MOM/ROC/MFI), 3 volume, 3 volatility, top 10 candlestick patterns, qtpylib helpers (crossed_above/below critical), technical library (ichimoku/VWAP/hull/SSL), 6 gotchas.|d:none — reference. Always Abstract API. ALL indicators in populate_indicators(), never entry/exit_trend|!ta-lib Windows needs pre-built binaries. BBANDS default 5 (use 20). SAR whipsaws sideways.

L008|vectorbt,backtesting,vectorized,trading,indicators,portfolio,parameter-optimization,signal-generation,prover|→L001,S001,R003|←∅|VectorBT reference for two-phase pipeline (VectorBT screening→Freqtrade validation). Signal generation, Portfolio.from_signals() (size_type/direction/stops/fees), built-in indicators, IndicatorFactory, run_combs() (4851 combos from 99 windows), results analysis (stats/trades/Sharpe/heatmaps), data handling (YFData/CCXTData), VectorBT→Freqtrade signal conversion, Numba tips, PRO vs open-source.|d:open-source sufficient Phase 1; signal conversion manual; CPCV needs external lib|!no automated signal-to-FT converter. CPCV not native. PRO scope unclear.

L009|optuna,hyperparameter,optimization,bayesian,TPE,pruning,freqtrade,trading|→L001,L006,S001,R003|←∅|Complete Optuna reference. Core concepts, Trial suggest API, 8 samplers (TPE default, CmaEs continuous, NSGAIII=FT default, Auto), 6 pruners (MedianPruner recommended), storage (SQLite/PostgreSQL/JournalFile), 10 plot types, FT hyperopt integration (CLI, loss functions, standalone vs built-in table), best practices (10x params trials), 6 pitfalls.|d:FT hyperopt for quick sweeps, standalone Optuna for pruning/walk-forward; TPESampler with seed|!FT hyperopt no pruning. Walk-forward needs custom objective.

L010|pytest,testing,fixtures,parametrize,mocking,hypothesis,property-testing,benchmark,dataframe|→C002,R003,S001|←∅|Advanced pytest extending CODE-002. Fixtures (5 scopes, autouse, factories), parametrize (stacking, indirect, marks), mocking (monkeypatch vs MagicMock comparison), markers (skip/xfail, custom), conftest hierarchy, Hypothesis (@given, hypothesis.extra.pandas for OHLCV), pytest-benchmark (pedantic mode), DataFrame testing (schema, approx, NaN propagation).|d:monkeypatch for simple, unittest.mock for call tracking; Hypothesis +~10s/DataFrame test|!Hypothesis+benchmark don't compose. hypothesis.extra.pandas no OHLC constraints.

L011|ccxt,exchange-api,trading,unified-api,freqtrade,python,market-data,orders,error-handling,async|→L001,L003,S001|←∅|Comprehensive CCXT reference. Exchange instantiation (sync/async, sandbox), market structure (symbol format, precision vs limits), public API (fetchTicker/OrderBook/OHLCV, pagination, timestamps), private API (balance, createOrder market/limit/stop/TP/SL, derivatives, order management), async vs sync (3 pitfalls), error handling (exception hierarchy, retry with backoff, retryability table), exchange quirks (Binance/Bybit/OKX/Kraken table), FT integration, 10 gotchas.|d:sync for FT strategies; implement own retry (CCXT internal broken); triggerPrice/stopLossPrice/takeProfitPrice unified|!CCXT v4.x Feb 2026. Fee info "experimental". Binance testnet URLs changed 2025.

---

## LOG Files

G002|timeline,decisions,sessions,changelog|→S001|←S001|Chronological project timeline. Append-only log of all sessions, key actions, files created/modified, decisions made.|i:append-only, use entry format template|!none

---

## Open Questions

| # | Question | Source | Status |
|---|----------|--------|--------|
| 1 | What is the exact inter-brain CONTEXT-PACK/RESULT protocol format? | SPEC-001 | Open |
| 2 | Should CCXT calls in strategies be async or sync? FT handles async internally — strategy authors should use sync, but edge cases exist. | SPEC-001, LEARN-011 | Open |
| 3 | How should short selling strategies be templated? Current CODE-001 is long-only. Need enter_short/exit_short columns. | SPEC-001, CODE-001 | Open |
| 4 | What is the multi-timeframe strategy template pattern? Need informative_pairs() + merge_informative_pair() integration. | SPEC-001, LEARN-005 | Open |
| 5 | Should there be a VectorBT screening template like the IStrategy template? | SPEC-001, LEARN-008 | Open |
| 6 | What exchanges are in scope? Current knowledge covers Binance/Bybit/OKX/Kraken but scope not defined. | SPEC-001, LEARN-011 | Open |
| 7 | Is pandas-ta a valid alternative to ta-lib? Not in import whitelist but commonly used. | RULE-001, LEARN-007 | Open |
| 8 | How should freqtrade.persistence DB access be handled in the security model? Currently allowed but risky. | RULE-001 | Open |

---

## Tensions

| # | Tension | Files | Status |
|---|---------|-------|--------|
| 1 | LEARN-004 recommends Mode 3 trailing (offset) but CODE-003 demonstrates Mode 4 (static-until-offset). Both valid but inconsistent as "recommended default." | LEARN-004, CODE-003 | Monitor |
| 2 | RULE-001 allows ccxt in STRICT mode (strategies) but flags it as risky. LEARN-011 documents full API including write operations. Strategy authors could call createOrder() through ccxt. | RULE-001, LEARN-011 | Monitor |

---

## Clusters

### freqtrade-core
Core Freqtrade framework knowledge — IStrategy interface, bot lifecycle, configuration, data handling.
- LEARN-001, LEARN-003, LEARN-004, LEARN-005, LEARN-006, LEARN-007

### code-generation
Strategy generation pipeline — templates, style, validation, few-shot examples.
- CODE-001, CODE-002, CODE-003, LEARN-002, RULE-001, RULE-002, RULE-003

### optimization
Parameter tuning, backtesting, and screening tools.
- LEARN-006, LEARN-008, LEARN-009

### testing
Test scaffolding, pytest patterns, validation pipeline.
- CODE-002, LEARN-010, RULE-003

### external-apis
Exchange connectivity and external library references.
- LEARN-011, LEARN-008

### architecture
System design and brain structure.
- SPEC-001, LOG-002
