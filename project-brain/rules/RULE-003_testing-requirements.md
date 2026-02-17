# RULE-003: Testing Requirements
<!-- type: RULE -->
<!-- created: 2026-02-17 -->
<!-- tags: testing, requirements, pytest, validation, strategy, guardrails, pipeline -->
<!-- links: CODE-002, CODE-001, LEARN-002 -->

## Purpose
Defines mandatory testing and validation requirements for all generated code. Every implementation task MUST produce code AND tests.

## Validation Pipeline

Every generated strategy goes through this 3-stage pipeline:

```
Stage 1: AST Parse       → Syntax valid? Structure correct?
Stage 2: Import Check     → Only allowed modules? (RULE-001)
Stage 3: Test / Dry-Run   → pytest passes? Freqtrade dry-run completes?
```

**On failure:** Extract specific error → feed back → regenerate. **Max 3 rounds.**

## Mandatory Tests (per strategy)

Every strategy MUST pass these tests (from CODE-002):

| # | Test | What it validates |
|---|------|-------------------|
| 1 | `test_strategy_attributes` | Required attributes exist (timeframe, stoploss, etc.) |
| 2 | `test_populate_indicators` | Indicators calculate without error |
| 3 | `test_populate_entry_trend` | Entry signals are binary (0/1) |
| 4 | `test_populate_exit_trend` | Exit signals are binary (0/1) |
| 5 | `test_dataframe_shape_preserved` | Row count unchanged through pipeline |
| 6 | `test_no_entry_on_zero_volume` | Volume > 0 guard works |
| 7 | `test_flat_market` | No crash on flat price data |

## Additional Tests (when applicable)

| Condition | Required Test |
|-----------|---------------|
| Uses informative pairs | Test that `informative_pairs()` returns valid tuples |
| Uses custom callbacks | Test each callback returns expected type |
| Uses hyperopt parameters | Test with default values AND edge values |
| Multiple timeframes | Test that merge_informative_pair produces expected columns |

## Test Execution

```bash
# Run strategy tests
pytest tests/test_<strategy_name>.py -v --tb=short

# Freqtrade dry-run validation (if Freqtrade installed)
freqtrade backtesting -c config.json -s <StrategyName> --timerange 20230101-20230201 --dry-run-wallet 1000
```

## Validation Rules

1. **No code without tests** — every implementation task produces both
2. **Tests run before delivery** — code is not "done" until tests pass
3. **Max 3 iteration rounds** — if tests still fail after 3 fix attempts, report as blocked
4. **Import whitelist enforced** — Stage 2 rejects any non-whitelisted import (RULE-001)
5. **AST parse first** — catches syntax errors before running expensive tests
6. **30-second timeout** — any single test that runs > 30s is a failure
7. **512MB memory limit** — strategies must not consume excessive memory

## What "Pass" Means

- All mandatory tests return green
- No import whitelist violations
- No AST parse errors
- Freqtrade backtesting completes without exceptions (if available)

## What "Fail" Means

- Any mandatory test fails
- Import whitelist violation detected
- AST parse error
- Freqtrade backtesting throws exception
- Test timeout (>30s) or memory limit exceeded

## Error Feedback Loop

When a test fails:
1. Extract the specific error message and traceback
2. Identify the root cause (wrong indicator call, missing column, bad condition syntax)
3. Fix the specific issue — do not regenerate the entire strategy
4. Re-run only the failing test first, then full suite
5. If 3 rounds of fixes don't resolve it, report as blocked with all error messages

## Known Issues
- Freqtrade dry-run requires installation + exchange data downloaded.
- Property-based tests (hypothesis) are optional — add when strategies are more complex.
- No live/dry-run comparison test yet — this is a future enhancement.
