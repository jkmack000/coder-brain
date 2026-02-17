# CODE-003: Sample Validated Strategy
<!-- type: CODE -->
<!-- created: 2026-02-17 -->
<!-- tags: freqtrade, strategy, example, validated, EMA-crossover, RSI, python -->
<!-- links: CODE-001, LEARN-001, LEARN-007, RULE-001 -->

## Purpose
Known-working Freqtrade strategy as a few-shot example for code generation. Passes all CODE-002 tests and the Freqtrade dry-run validation. Simple EMA crossover with RSI filter — the "hello world" of trading strategies.

## Strategy: EMA Crossover with RSI Filter

```python
"""
EMA Crossover with RSI Filter — Sample validated strategy.

Economic thesis: Trend-following via dual EMA crossover captures momentum shifts.
RSI filter avoids entering during overbought/oversold extremes where reversals
are more likely.

Validated: Passes all CODE-002 test patterns. Backtests without errors on
Binance ETH/USDT 1h data 2023-01-01 to 2024-01-01.
"""

from freqtrade.strategy import IStrategy, IntParameter
from pandas import DataFrame
import talib.abstract as ta
from freqtrade.vendor import qtpylib

import logging
logger = logging.getLogger(__name__)


class EMACrossoverRSI(IStrategy):
    """
    Simple EMA crossover strategy with RSI filter.

    Entry: Fast EMA crosses above slow EMA AND RSI < 70 (not overbought).
    Exit: Fast EMA crosses below slow EMA OR RSI > 80.

    Economic thesis: Dual EMA crossover captures medium-term momentum shifts.
    RSI filter reduces false entries during overbought conditions.
    """

    INTERFACE_VERSION = 3

    timeframe = '1h'

    minimal_roi = {
        "120": 0.0,    # Exit after 120 min at breakeven
        "60": 0.01,    # Exit after 60 min if profit >= 1%
        "30": 0.02,    # Exit after 30 min if profit >= 2%
        "0": 0.04      # Exit immediately if profit >= 4%
    }

    stoploss = -0.10  # 10% stoploss

    trailing_stop = True
    trailing_stop_positive = 0.02
    trailing_stop_positive_offset = 0.03
    trailing_only_offset_is_reached = True

    startup_candle_count: int = 200  # 4x EMA(50) = 200

    process_only_new_candles = True

    order_types = {
        'entry': 'limit',
        'exit': 'limit',
        'stoploss': 'market',
        'stoploss_on_exchange': False,
    }

    # Hyperopt parameters
    buy_rsi_max = IntParameter(50, 80, default=70, space='buy')
    sell_rsi_min = IntParameter(60, 90, default=80, space='sell')

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # Moving averages
        dataframe['ema_9'] = ta.EMA(dataframe, timeperiod=9)
        dataframe['ema_21'] = ta.EMA(dataframe, timeperiod=21)
        dataframe['ema_50'] = ta.EMA(dataframe, timeperiod=50)

        # RSI
        dataframe['rsi'] = ta.RSI(dataframe, timeperiod=14)

        # ADX for trend strength
        dataframe['adx'] = ta.ADX(dataframe, timeperiod=14)

        # Bollinger Bands (for reference / future use)
        bollinger = qtpylib.bollinger_bands(qtpylib.typical_price(dataframe), window=20, stds=2)
        dataframe['bb_lower'] = bollinger['lower']
        dataframe['bb_middle'] = bollinger['mid']
        dataframe['bb_upper'] = bollinger['upper']

        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (
                # EMA crossover: fast crosses above slow
                (qtpylib.crossed_above(dataframe['ema_9'], dataframe['ema_21']))
                &
                # Price above longer-term trend
                (dataframe['close'] > dataframe['ema_50'])
                &
                # RSI not overbought
                (dataframe['rsi'] < self.buy_rsi_max.value)
                &
                # Minimum trend strength
                (dataframe['adx'] > 20)
                &
                # Volume guard (mandatory)
                (dataframe['volume'] > 0)
            ),
            'enter_long'] = 1

        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (
                # EMA crossover: fast crosses below slow
                (qtpylib.crossed_below(dataframe['ema_9'], dataframe['ema_21']))
                |
                # RSI overbought
                (dataframe['rsi'] > self.sell_rsi_min.value)
            )
            &
            (dataframe['volume'] > 0),
            'exit_long'] = 1

        return dataframe
```

## Why This Strategy

1. **Simple and readable** — good few-shot example for LLM generation
2. **Uses core patterns** — EMA crossover, RSI filter, ADX trend strength, volume guard
3. **Demonstrates template slots** — all fill slots from CODE-001 are represented
4. **Includes hyperopt params** — shows parameter optimization interface
5. **Trailing stop Mode 4** — most recommended mode
6. **Correct startup_candle_count** — 200 covers EMA(50) with 4x margin

## Test Evidence

All CODE-002 tests pass:
- `test_strategy_attributes` — all required attributes present
- `test_populate_indicators` — runs without error, adds expected columns
- `test_populate_entry_trend` — signals are binary (0/1)
- `test_populate_exit_trend` — signals are binary (0/1)
- `test_dataframe_shape_preserved` — row count unchanged through pipeline
- `test_no_entry_on_zero_volume` — zero-volume candles have no entries
- `test_flat_market` — no crash on flat data

## Patterns Demonstrated

| Pattern | Example |
|---------|---------|
| EMA crossover | `qtpylib.crossed_above(df['ema_9'], df['ema_21'])` |
| RSI filter | `df['rsi'] < self.buy_rsi_max.value` |
| Trend strength gate | `df['adx'] > 20` |
| Trend direction filter | `df['close'] > df['ema_50']` |
| Volume guard | `df['volume'] > 0` |
| Hyperopt parameter | `IntParameter(50, 80, default=70, space='buy')` |
| Trailing stop Mode 4 | `trailing_only_offset_is_reached = True` |
| Multi-output indicator | `bollinger = qtpylib.bollinger_bands(...)` |

## Known Issues
- This is a demonstration strategy, not a profitable one. Do not use for live trading.
- Backtest results depend on pair, timerange, and market conditions.
- Missing: short signals (long-only), informative pairs, custom callbacks.
