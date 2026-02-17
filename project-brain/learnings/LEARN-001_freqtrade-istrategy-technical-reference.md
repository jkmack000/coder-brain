# LEARN-001 — Freqtrade IStrategy Technical Reference
<!-- type: LEARN -->
<!-- tags: freqtrade, IStrategy, trading, python, callbacks, hyperopt, signals, indicators -->
<!-- created: 2026-02-17 -->
<!-- source: Web research across 12+ Freqtrade documentation pages (freqtrade.io) -->
<!-- links: SPEC-001 -->

## Purpose

Complete technical reference for Freqtrade's IStrategy interface — the target abstraction for AI-generated trading strategies. This is the primary reference for code generation.

## Required Methods

Every strategy subclasses `IStrategy` and implements three methods. All receive `(self, dataframe: DataFrame, metadata: dict) -> DataFrame`.

### `populate_indicators`
Add technical indicator columns. Called once per pair. Must not modify OHLCV columns (`open`, `high`, `low`, `close`, `volume`).

### `populate_entry_trend`
Set `enter_long` to `1` where entry conditions are met. For shorts: `enter_short`. Optional: `enter_tag` for labeling.

### `populate_exit_trend`
Set `exit_long` to `1` where exit conditions are met. For shorts: `exit_short`. Optional: `exit_tag`.

**Critical**: Signals fire on the **next candle open** after the signal candle closes.

## DataFrame Columns

Core OHLCV: `date` (datetime), `open`, `high`, `low`, `close`, `volume` (all float).
`metadata['pair']` returns pair string like `"XRP/BTC"` (spot) or `"XRP/BTC:BTC"` (futures).

Signal columns added by strategy: `enter_long`, `enter_short`, `exit_long`, `exit_short` (int 0/1), `enter_tag`, `exit_tag` (str, optional).

## Required Class Attributes

```python
INTERFACE_VERSION = 3          # Current version, always set explicitly
minimal_roi = {"60": 0.01, "30": 0.02, "0": 0.04}  # keys = minutes (strings), values = profit ratio
stoploss = -0.10               # Negative ratio: -0.10 = 10% loss
timeframe = '5m'               # '1m','5m','15m','1h','4h','1d', etc.
```

## Optional Attributes

```python
trailing_stop = False
trailing_stop_positive = 0.02
trailing_stop_positive_offset = 0.03
trailing_only_offset_is_reached = True
startup_candle_count = 200
can_short = False
process_only_new_candles = True
position_adjustment_enable = False
use_custom_stoploss = False
order_types = {"entry": "limit", "exit": "limit", "stoploss": "market", "stoploss_on_exchange": False}
order_time_in_force = {"entry": "GTC", "exit": "GTC"}
```

## Optional Callback Methods (15+)

All callbacks are optional — implement only those needed.

| Callback | Signature Key Params | Purpose |
|----------|---------------------|---------|
| `bot_start` | `**kwargs` | One-time init when bot starts |
| `bot_loop_start` | `current_time` | Every throttling iteration |
| `custom_stoploss` | `pair, trade, current_time, current_rate, current_profit` | Dynamic stoploss (requires `use_custom_stoploss=True`). Return ratio relative to current_rate. Can only tighten, never loosen. |
| `custom_exit` | `pair, trade, current_time, current_rate, current_profit` | Return string (exit reason) to trigger exit, None to skip |
| `custom_entry_price` | `pair, trade, current_time, proposed_rate, entry_tag, side` | Return custom entry price |
| `custom_exit_price` | `pair, trade, current_time, proposed_rate, current_profit, exit_tag` | Return custom exit price |
| `custom_stake_amount` | `pair, current_time, current_rate, proposed_stake, min_stake, max_stake, leverage, entry_tag, side` | Custom position size |
| `confirm_trade_entry` | `pair, order_type, amount, rate, time_in_force, current_time, entry_tag, side` | Return True to confirm, False to abort |
| `confirm_trade_exit` | `pair, trade, order_type, amount, rate, time_in_force, exit_reason, current_time` | Return True to confirm exit |
| `check_entry_timeout` | `pair, trade, order, current_time` | Return True to cancel unfilled entry |
| `check_exit_timeout` | `pair, trade, order, current_time` | Return True to cancel unfilled exit |
| `adjust_trade_position` | `trade, current_time, current_rate, current_profit, min_stake, max_stake` | DCA: positive to increase, negative to decrease. Requires `position_adjustment_enable=True` |
| `leverage` | `pair, current_time, current_rate, proposed_leverage, max_leverage, entry_tag, side` | Return leverage 1.0 to max. Futures only. |
| `informative_pairs` | _(no params)_ | Return list of `(pair, timeframe)` tuples for additional data |

## Parameter Optimization Interface (Hyperopt)

```python
from freqtrade.strategy import IntParameter, DecimalParameter, BooleanParameter, CategoricalParameter

buy_rsi = IntParameter(10, 40, default=30, space="buy", optimize=True)
buy_adx = DecimalParameter(20.0, 40.0, decimals=1, default=30.1, space="buy")
buy_enabled = BooleanParameter(default=True, space="buy")
buy_trigger = CategoricalParameter(["bb_lower", "macd_cross"], default="bb_lower", space="buy")
```

- `space`: `"buy"`, `"sell"`, `"protection"`, `"roi"`, `"stoploss"`, `"trades"`
- `optimize`: True (default) to include in hyperopt, False for fixed value
- Access via `.value` property: `self.buy_rsi.value`
- **Critical constraint**: Parameters cannot be used in `populate_indicators` — only in entry/exit trend methods (indicators calculated once, reused across hyperopt epochs)

## Indicator Libraries

- **TA-Lib**: `import talib.abstract as ta` — RSI, MACD, BBANDS, ADX, EMA, SMA, CCI, MFI, SAR, etc.
- **technical** (Freqtrade companion): ichimoku, cmf, plus `qtpylib` helpers for `crossed_above`/`crossed_below`, Heikin Ashi
- **pandas-ta**: `import pandas_ta as pta` — alternative indicator library

## Signal Pattern

```python
dataframe.loc[
    (
        (dataframe['rsi'] < self.buy_rsi.value) &
        (dataframe['ema_fast'] > dataframe['ema_slow']) &
        (dataframe['volume'] > 0)  # Always include volume guard
    ),
    ['enter_long', 'enter_tag']
] = (1, 'rsi_ema_cross')
```

## Code Generation Constraints

1. `INTERFACE_VERSION = 3` — always set explicitly
2. Never modify OHLCV columns
3. Always return the dataframe from all populate methods
4. Signals fire on next candle open (not signal candle)
5. Always include `volume > 0` guard in signal conditions
6. Hyperopt parameters only in entry/exit trend methods, never in populate_indicators
7. `stoploss` must be negative (loss ratio)
8. `minimal_roi` keys are strings (minutes since trade open)
9. `custom_stoploss` can only tighten, never loosen
10. Short trading requires `can_short = True` + futures/margin mode

## Known Issues

- TA-Lib is problematic to install on Windows (C dependency)
- Freqtrade is crypto-focused — equity/futures may need different framework
- `startup_candle_count` must be large enough for all indicators to stabilize (200 is safe default)
- Informative pairs increase data download time proportionally
