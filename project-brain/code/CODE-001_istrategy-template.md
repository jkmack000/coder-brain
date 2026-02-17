# CODE-001: IStrategy Template with Fill Slots
<!-- type: CODE -->
<!-- created: 2026-02-17 -->
<!-- tags: freqtrade, IStrategy, template, code-generation, strategy, python -->
<!-- links: LEARN-001, LEARN-007, RULE-001 -->

## Purpose
Template for generating Freqtrade IStrategy files. The coding agent fills only the marked slots — structure, imports, and boilerplate are fixed. This eliminates structural errors (the largest error class in LLM code generation).

## Template

```python
# --- GENERATED STRATEGY ---
# Task: {{TASK_ID}}
# Generated: {{TIMESTAMP}}

from freqtrade.strategy import IStrategy, IntParameter, DecimalParameter, BooleanParameter, CategoricalParameter
from pandas import DataFrame
import talib.abstract as ta
from freqtrade.vendor import qtpylib
# {{ADDITIONAL_IMPORTS}}  # FILL SLOT: Only from RULE-001 whitelist

import logging
logger = logging.getLogger(__name__)


class {{STRATEGY_NAME}}(IStrategy):
    """
    {{STRATEGY_DESCRIPTION}}

    Economic thesis: {{ECONOMIC_THESIS}}
    """

    # --- Required strategy attributes ---
    INTERFACE_VERSION = 3

    timeframe = '{{TIMEFRAME}}'  # FILL SLOT: e.g., '5m', '1h', '4h'

    # ROI table — exit after N minutes if profit >= X%
    minimal_roi = {
        {{ROI_TABLE}}  # FILL SLOT: e.g., "60": 0.01, "30": 0.02, "0": 0.04
    }

    # Stoploss
    stoploss = {{STOPLOSS}}  # FILL SLOT: negative ratio, e.g., -0.10

    # Trailing stoploss (optional)
    trailing_stop = {{TRAILING_STOP}}  # FILL SLOT: True/False
    # trailing_stop_positive = {{TRAILING_POSITIVE}}
    # trailing_stop_positive_offset = {{TRAILING_OFFSET}}
    # trailing_only_offset_is_reached = {{TRAILING_ONLY_OFFSET}}

    # Startup candle count — must be >= 2x-4x longest indicator period
    startup_candle_count: int = {{STARTUP_CANDLE_COUNT}}  # FILL SLOT

    # Process only new candles (recommended: True)
    process_only_new_candles = True

    # Order types
    order_types = {
        'entry': 'limit',
        'exit': 'limit',
        'stoploss': 'market',
        'stoploss_on_exchange': False,
    }

    # --- Optional: Hyperopt parameters ---
    # {{HYPEROPT_PARAMETERS}}  # FILL SLOT: IntParameter, DecimalParameter, etc.

    def informative_pairs(self):
        """Define additional pairs/timeframes needed by this strategy."""
        # {{INFORMATIVE_PAIRS}}  # FILL SLOT: return list of (pair, timeframe) tuples
        return []

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Calculate all technical indicators.
        - Use ta.* (Abstract API) for ta-lib indicators
        - Use qtpylib.* for bollinger bands, crossover detection
        - Assign each indicator to a dataframe column
        - Do NOT reference hyperopt parameters here
        """
        # {{INDICATORS}}  # FILL SLOT: All indicator calculations

        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Set entry signals. Columns: 'enter_long' (and optionally 'enter_short', 'enter_tag').
        - Use vectorized boolean conditions
        - Always include (dataframe['volume'] > 0) guard
        - Use qtpylib.crossed_above/crossed_below for crossover signals
        """
        dataframe.loc[
            (
                {{ENTRY_CONDITIONS}}  # FILL SLOT: Boolean conditions joined by &
                &
                (dataframe['volume'] > 0)  # Always required
            ),
            'enter_long'] = 1

        # {{ENTER_TAG}}  # FILL SLOT (optional): dataframe['enter_tag'] = 'reason'

        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Set exit signals. Columns: 'exit_long' (and optionally 'exit_short', 'exit_tag').
        """
        dataframe.loc[
            (
                {{EXIT_CONDITIONS}}  # FILL SLOT: Boolean conditions joined by &
                &
                (dataframe['volume'] > 0)
            ),
            'exit_long'] = 1

        return dataframe

    # --- Optional callbacks ---
    # Uncomment and fill as needed:

    # def custom_stoploss(self, pair: str, trade: 'Trade', current_time: datetime,
    #                     current_rate: float, current_profit: float,
    #                     after_fill: bool, **kwargs) -> float:
    #     """Return custom stoploss ratio. Return -1 to keep current stoploss."""
    #     {{CUSTOM_STOPLOSS}}
    #     return -1

    # def custom_exit(self, pair: str, trade: 'Trade', current_time: datetime,
    #                 current_rate: float, current_profit: float,
    #                 after_fill: bool, **kwargs) -> Optional[Union[str, bool]]:
    #     """Return string reason to exit, or None to keep position."""
    #     {{CUSTOM_EXIT}}
    #     return None
```

## Fill Slot Reference

| Slot | Required | Description | Example |
|------|----------|-------------|---------|
| `STRATEGY_NAME` | yes | PascalCase class name | `DonchianBreakout` |
| `STRATEGY_DESCRIPTION` | yes | One-line description | `Donchian channel breakout with RSI filter` |
| `ECONOMIC_THESIS` | yes | Why this should work | `Trend-following captures momentum after range breakout` |
| `TIMEFRAME` | yes | Candle timeframe | `'1h'` |
| `ROI_TABLE` | yes | Minutes → profit ratio | `"60": 0.01, "30": 0.02, "0": 0.04` |
| `STOPLOSS` | yes | Negative ratio | `-0.10` |
| `TRAILING_STOP` | yes | Boolean | `True` |
| `STARTUP_CANDLE_COUNT` | yes | Integer >= 2x longest indicator | `400` |
| `INDICATORS` | yes | All ta.* / qtpylib calculations | See LEARN-007 |
| `ENTRY_CONDITIONS` | yes | Boolean conditions with `&` | See examples below |
| `EXIT_CONDITIONS` | yes | Boolean conditions with `&` | See examples below |
| `ADDITIONAL_IMPORTS` | no | Extra imports from whitelist | `from technical.indicators import ichimoku` |
| `HYPEROPT_PARAMETERS` | no | Optimization parameters | `buy_rsi = IntParameter(20, 40, default=30)` |
| `INFORMATIVE_PAIRS` | no | Additional data needed | `return [("BTC/USDT", "1d")]` |

## Entry/Exit Condition Patterns

```python
# EMA crossover entry
(qtpylib.crossed_above(dataframe['ema_9'], dataframe['ema_21']))

# RSI oversold entry
(dataframe['rsi'] < 30)

# RSI crosses above threshold
(qtpylib.crossed_above(dataframe['rsi'], 30))

# Bollinger band bounce
(dataframe['close'] < dataframe['bb_lowerband'])

# ADX trend strength filter
(dataframe['adx'] > 25)

# MACD histogram positive
(dataframe['macdhist'] > 0)

# Candlestick pattern
(dataframe['cdl_hammer'] == 100)

# Price above moving average
(dataframe['close'] > dataframe['sma_200'])
```

## Usage Rules
1. NEVER modify template structure — only fill slots
2. All imports must pass RULE-001 whitelist check
3. Every strategy MUST have an economic thesis
4. startup_candle_count MUST be >= 2x longest indicator period
5. Volume > 0 guard is MANDATORY in entry/exit conditions
6. Hyperopt parameters CANNOT be used in populate_indicators()
7. All indicators computed in populate_indicators(), never in entry/exit trend

## Known Issues
- Template assumes long-only. Short strategies need `enter_short`/`exit_short` columns.
- Optional callbacks commented out — uncomment and fill as needed per task.
