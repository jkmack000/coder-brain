# LEARN-008: VectorBT Backtesting Engine — Comprehensive Reference
<!-- type: LEARN -->
<!-- created: 2026-02-18 -->
<!-- tags: vectorbt, backtesting, vectorized, trading, indicators, portfolio, parameter-optimization, signal-generation, prover -->
<!-- links: LEARN-001, SPEC-001, RULE-003 -->

## Context
VectorBT is the Phase 1 screening engine in the Prover two-phase pipeline (VectorBT screening → Freqtrade validation). This reference covers the open-source version (MIT, github.com/polakowo/vectorbt).

- **PyPI:** `pip install vectorbt`
- **Python:** >=3.10 (supports 3.10-3.13 as of Jan 2026)
- **Performance:** Fills 1,000,000 orders in 70-100ms on Apple M1

## 1. Vectorized vs Event-Driven

| Aspect | VectorBT (Vectorized) | Freqtrade (Event-Driven) |
|--------|----------------------|--------------------------|
| Speed | ~1000x faster for parameter sweeps | Slower per-run, models realistic execution |
| Fidelity | Bar-level granularity, simplified execution | Realistic order types, partial fills, slippage |
| Use case | Screening, parameter optimization, rapid prototyping | Final validation, live trading, complex execution |
| Scaling | Thousands of param combos in seconds | One strategy at a time (or hyperopt) |
| Live trading | Limited (PRO has some support) | Full live trading with exchange integration |
| Strategy format | Boolean signal arrays | IStrategy class with DataFrame methods |

### Two-Phase Pipeline (per SPEC-001)
**Phase 1 — VectorBT Screening:** Test 10,000+ parameter combos in seconds, identify promising regions via heatmaps, filter by Sharpe/drawdown, discard unprofitable strategies quickly.

**Phase 2 — Freqtrade Validation:** Take top N candidates, validate with realistic execution (fees, slippage, partial fills), run CPCV cross-validation (PBO < 0.5 hard gate), deploy to paper/live.

## 2. Signal Generation

### Basic Entry/Exit from Indicator Crossovers
```python
import vectorbt as vbt
import numpy as np

price = vbt.YFData.download("AAPL", period="2y").get("Close")

fast_ma = vbt.MA.run(price, window=10)
slow_ma = vbt.MA.run(price, window=50)

entries = fast_ma.ma_crossed_above(slow_ma)   # Boolean Series
exits = fast_ma.ma_crossed_below(slow_ma)     # Boolean Series
```

### Combining Multiple Signals
```python
rsi = vbt.RSI.run(price, window=14)
entries = fast_ma.ma_crossed_above(slow_ma) & (rsi.rsi < 30)
exits = fast_ma.ma_crossed_below(slow_ma) | (rsi.rsi > 70)
```

### Signal Chaining (Chain Mode)
VectorBT's "chain" mode enforces strict alternation: once you enter, ignore all entry signals until an exit fires, then ignore exit signals until an entry fires. Prevents signal overlap.

### SignalFactory for Custom Signal Generators
```python
from vectorbt.signals.factory import SignalFactory
from numba import njit

@njit
def wait_choice_nb(from_i, to_i, col, n, temp_idx_arr):
    temp_idx_arr[0] = from_i + n
    if temp_idx_arr[0] < to_i:
        return temp_idx_arr[:1]
    return temp_idx_arr[:0]

MySignals = SignalFactory(
    mode='chain',
    param_names=['n']
).from_choice_func(
    exit_choice_func=wait_choice_nb,
    exit_settings=dict(
        pass_params=['n'],
        pass_kwargs=['temp_idx_arr']
    )
)
```

## 3. Portfolio Simulation

### Portfolio.from_signals() — Primary Method
```python
pf = vbt.Portfolio.from_signals(
    close=price,           # Price data (Series or DataFrame)
    entries=entries,        # Boolean entry signals
    exits=exits,           # Boolean exit signals
    init_cash=100_000,     # Initial capital (default: 100)
    size=np.inf,           # Position size (np.inf = all-in)
    size_type='amount',    # 'amount', 'value', 'percent', 'targetpercent'
    fees=0.001,            # Trading fees as decimal (0.1%)
    slippage=0.001,        # Slippage as decimal (0.1%)
    freq='1D',             # Data frequency
    direction='longonly',  # 'longonly', 'shortonly', 'both'
    sl_stop=0.02,          # Stop loss (2% of entry price)
    tp_stop=0.05,          # Take profit (5% of entry price)
    min_size=1,            # Minimum order size
    size_granularity=1,    # Size rounding granularity
)
```

**size_type options:** `'amount'` (fixed units), `'value'` (fixed dollar), `'percent'` (% of cash), `'targetpercent'` (rebalancing)

**direction options:** `'longonly'`, `'shortonly'`, `'both'`

**Stop orders:** `sl_stop` (stop loss fraction), `tp_stop` (take profit fraction), `ts_stop` (trailing stop fraction)

### Other Portfolio Creation Methods
```python
# From explicit orders
pf = vbt.Portfolio.from_orders(close=price, size=order_sizes, fees=0.001, init_cash=100_000)

# From custom order function (max flexibility, Numba-compiled)
pf = vbt.Portfolio.from_order_func(close=price, order_func_nb=my_func, init_cash=100_000)
```

## 4. Indicator API

### Built-in Indicators

| Indicator | Class | Key Params | Outputs |
|-----------|-------|------------|---------|
| Moving Average | `vbt.MA` | `close, window, ewm` | `.ma` |
| RSI | `vbt.RSI` | `close, window` | `.rsi` |
| Bollinger Bands | `vbt.BBANDS` | `close, window, ewm, alpha` | `.upper`, `.middle`, `.lower`, `.bandwidth`, `.percent_b` |
| MACD | `vbt.MACD` | `close, fast_window, slow_window, signal_window` | `.macd`, `.signal`, `.hist` |
| ATR | `vbt.ATR` | `high, low, close, window` | `.atr` |
| Stochastic | `vbt.STOCH` | `high, low, close, k_window, d_window` | `.percent_k`, `.percent_d` |
| OBV | `vbt.OBV` | `close, volume` | `.obv` |

### Running with Parameter Arrays
```python
# Single parameter
ma = vbt.MA.run(price, window=20)

# Multiple parameters (returns multi-column output)
ma = vbt.MA.run(price, window=[10, 20, 50])

# Combinations (for crossover strategies)
fast_ma, slow_ma = vbt.MA.run_combs(
    close=price,
    window=np.arange(2, 101),  # 99 windows
    r=2,                        # 2-combinations
    short_names=['fast', 'slow']
)
# Generates C(99,2) = 4851 unique fast/slow pairs
```

### Custom Indicators via IndicatorFactory
```python
from numba import njit

@njit
def custom_apply_func(close, fast_window, slow_window):
    fast = np.empty_like(close)
    slow = np.empty_like(close)
    # ... compute SMAs with Numba ...
    return fast - slow

MyIndicator = vbt.IndicatorFactory(
    class_name='MyIndicator',
    short_name='myind',
    input_names=['close'],
    param_names=['fast_window', 'slow_window'],
    output_names=['spread']
).from_apply_func(
    custom_apply_func,
    fast_window=10,
    slow_window=20,
)

# With parameter arrays
result = MyIndicator.run(
    price,
    fast_window=np.arange(5, 30),
    slow_window=np.arange(20, 60),
    param_product=True    # Test ALL combinations
)
```

## 5. Results Analysis

### Portfolio Statistics
```python
print(pf.stats())  # Full summary

# Individual metrics
pf.total_return()
pf.sharpe_ratio()
pf.max_drawdown()
pf.sortino_ratio()
pf.calmar_ratio()

# Trade analysis
pf.trades.records_readable  # DataFrame of all trades
pf.trades.count()
pf.trades.win_rate()
pf.trades.profit_factor()
pf.trades.expectancy()
```

### Visualization (Plotly)
```python
pf.plot().show()  # Full portfolio plot

pf.total_return().vbt.heatmap(
    x_level='fast_window',
    y_level='slow_window',
    symmetric=True,
    trace_kwargs=dict(colorbar=dict(title='Total return', tickformat='%'))
)
```

## 6. Parameter Optimization

### Grid Search with Parameter Arrays
```python
windows = np.arange(5, 101)
fast_ma, slow_ma = vbt.MA.run_combs(
    close=price, window=windows, r=2, short_names=['fast', 'slow']
)

entries = fast_ma.ma_crossed_above(slow_ma)
exits = fast_ma.ma_crossed_below(slow_ma)

pf = vbt.Portfolio.from_signals(price, entries, exits, init_cash=10_000, fees=0.001)

# Find best parameters
best_idx = pf.sharpe_ratio().idxmax()
print(f"Best params: {best_idx}")
print(f"Best Sharpe: {pf.sharpe_ratio().max():.2f}")
```

## 7. Data Handling

```python
# Yahoo Finance
data = vbt.YFData.download("AAPL", period="2y", interval="1d")
data = vbt.YFData.download(["AAPL", "MSFT", "GOOG"], start="2023-01-01", end="2025-01-01")

# CCXT (Crypto)
data = vbt.CCXTData.download("BTC/USDT", exchange="binance", start="2 hours ago", timeframe="1m")

# Custom data — just pass pandas Series/DataFrame directly
pf = vbt.Portfolio.from_signals(df["close"], entries, exits)
```

## 8. VectorBT-to-Freqtrade Conversion

Signal semantic mapping:
- VectorBT: Boolean arrays (True/False at each bar)
- Freqtrade: DataFrame column values (1 in `enter_long` column)

Extract winning parameter values from VectorBT, code them into IStrategy template fill slots. This is a manual process — no automated converter exists.

## 9. Performance Tips

1. Use `param_product=True` or `run_combs()` — avoid Python loops over parameters
2. `@njit` decorator for custom indicators — enables Numba JIT
3. Most Numba functions support `parallel=True` for multi-core
4. Avoid pandas inside Numba — work with raw NumPy arrays
5. Only stack columns if data fits in RAM
6. `run_combs()` auto-filters invalid combos (fast >= slow)

## 10. PRO vs Open Source

| Feature | Open Source (Free) | PRO ($20/month) |
|---------|-------------------|-----------------|
| Core backtesting | Yes | Yes + enhanced |
| Built-in indicators | MA, RSI, BBANDS, MACD, ATR, STOCH, OBV, etc. | All OSS + more |
| Parameter optimization | Grid search, run_combs | + conditional params, random, Bayesian |
| Parallelization | Basic Numba parallel | ThreadPool, ProcessPool, Dask, Ray |
| Chunking | Manual | Automatic |
| Portfolio optimization | No | PyPortfolioOpt, Riskfolio-Lib |
| Leverage | Limited | Full (lazy/eager modes) |
| Multi-timeframe | Manual resampling | Native |

**Recommendation:** Open-source sufficient for Phase 1 screening. Consider PRO only if parameter sweeps exceed RAM or portfolio-level optimization needed.

## Known Issues
- CPCV likely requires external library (not native to VectorBT)
- PRO live trading scope unclear (behind paywall)
- No automated signal-to-Freqtrade converter exists — Coder brain capability to build
