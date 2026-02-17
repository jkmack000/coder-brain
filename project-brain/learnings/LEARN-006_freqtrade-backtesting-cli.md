# LEARN-006: Freqtrade Backtesting CLI
<!-- type: LEARN -->
<!-- created: 2026-02-17 -->
<!-- tags: freqtrade, backtesting, cli, timerange, results, metrics, export, pitfalls -->
<!-- links: LEARN-001, LEARN-005 -->

## Purpose
Complete reference for Freqtrade's backtesting command, parameters, result interpretation, and common pitfalls. Enables the coding agent to run and interpret backtests correctly.

## Core Command

```bash
freqtrade backtesting [options]
```

## Key Parameters

| Parameter | Description |
|-----------|-------------|
| `-c / --config <path>` | Config file |
| `-s / --strategy <name>` | Strategy class name |
| `--strategy-list <s1> <s2>` | Compare multiple strategies |
| `--timeframe <tf>` | Override strategy timeframe |
| `--timerange <range>` | Date range |
| `--datadir <path>` | Data directory |
| `--export {trades,signals}` | Export results (default: trades) |
| `--fee <float>` | Override fee ratio (applied entry + exit) |
| `--eps` | Enable position stacking (buy same pair multiple times) |
| `--dmmp` | Disable max_open_trades limit |
| `--timeframe-detail <tf>` | Lower TF for intra-candle simulation |
| `--cache {none,day}` | Result caching (`none` = fresh run) |
| `--breakdown {day,week,month}` | Profit breakdown by period |
| `--dry-run-wallet <amount>` | Override starting balance |

## --timerange Format

`YYYYMMDD-YYYYMMDD` (start inclusive, end exclusive):

```bash
--timerange 20230101-20240101    # Full range
--timerange 20230101-            # From date to end of data
--timerange -20240101            # From start of data to date
```

## --strategy-list Usage

```bash
freqtrade backtesting --strategy-list SMAcross RSIstrat BollingerBands -c config.json --timerange 20230101-20240101
```
Results shown side-by-side. Each strategy must be in strategy directory.

## --timeframe-detail

```bash
freqtrade backtesting -s MyStrategy --timeframe 1h --timeframe-detail 5m
```

- Strategy analysis uses main timeframe
- Entries placed at main TF candle boundaries
- **Exits and callbacks** evaluated at detail TF
- Must have detail TF data downloaded
- Simulates more realistic intra-candle movements

## Result Output: Key Metrics

### Per-Pair Table
| Column | Meaning |
|--------|---------|
| Pair | Trading pair |
| Trades | Completed trade count |
| Avg Profit % | Average per-trade profit |
| Tot Profit % | Total as % of starting balance |
| Abs Profit | Absolute in stake currency |
| Win/Draw/Loss | Outcome counts |

### Summary Metrics

| Metric | Description |
|--------|-------------|
| Total profit % | Return on starting balance |
| CAGR % | Compound annual growth rate |
| Sortino | Risk-adjusted (downside deviation) |
| Sharpe | Risk-adjusted (total volatility) |
| Calmar | Return / max drawdown |
| SQN | System Quality Number |
| Profit factor | Gross profit / gross loss |
| Expectancy (Ratio) | Average expected profit per trade |
| Max % underwater | Worst drawdown as % of peak |
| Absolute drawdown | Max drawdown in stake currency |
| Drawdown duration | How long worst drawdown lasted |
| Rejected entry signals | Signals skipped due to max_open_trades |

## Interpreting Results

**Good signs:**
- Profit factor > 1.5
- Positive expectancy ratio
- SQN > 2.0
- Reasonable trade count (too few = unreliable stats)
- Drawdown duration << total period

**Red flags:**
- Win rate >80% with few trades → overfitting or lookahead bias
- Unrealistic Sharpe/Sortino → "too good to be true"
- Large gap between avg win and avg loss size
- Very long avg trade duration (capital locked)
- High rejected signals count → results change drastically with different max_open_trades

## Export and Analysis

```bash
# Export trades
freqtrade backtesting -s MyStrategy --export trades

# Analyze
freqtrade backtesting-analysis -c config.json --export-filename user_data/backtest_results/backtest-result.json

# Time-period breakdown
freqtrade backtesting -s MyStrategy --breakdown month
```

Exported to `user_data/backtest_results/`. Can load in Jupyter via `load_backtest_data()`.

## Backtesting Assumptions and Limitations

1. **Candle-level granularity** — without `--timeframe-detail`, trades at open/close prices. Wick simulation imperfect.
2. **No slippage** — orders fill at exact prices. Real markets have slippage.
3. **No order book** — market impact not modeled.
4. **Full dataset at once** — entire timerange passed to `populate_*()` → root cause of lookahead bias.
5. **Flat fee rate** — real exchange tiers vary by volume.
6. **Caching** — results cached 1 day by default for identical strategy+config. Use `--cache none` for fresh.
7. **Past != future** — always validate with dry-run before live.

## Common Pitfalls

1. **Lookahead bias** — Using `iloc[-1]` or non-shifted references. Always `df.shift()`. Detect with:
   ```bash
   freqtrade lookahead-analysis -c config.json -s MyStrategy
   freqtrade recursive-analysis -c config.json -s MyStrategy
   ```

2. **Insufficient startup_candle_count** — indicators produce bad early values. Use `recursive-analysis` to verify.

3. **Overfitting to timerange** — use walk-forward (train on one period, test on next).

4. **Ignoring rejected signals** — high count means max_open_trades limited entries significantly.

5. **Data quality** — missing candles, exchange downtime, delisted pairs skew results.

6. **VolumePairList in backtesting** — uses live data, not reproducible. Use StaticPairList.

7. **Not validating with dry-run** — significant differences indicate bias or data issues.

## Multi-Timeframe Considerations

- All timeframes (main + informative) must be downloaded beforehand
- `startup_candle_count` is in main-TF units — account for higher TF warmup
- `--timeframe-detail` requires detail TF data
- Informative pairs from `informative_pairs()` auto-loaded if data available

## Known Issues
- `--cache day` auto-disabled for open-ended timeranges.
- Results may differ between Freqtrade versions due to internal changes.
