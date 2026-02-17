# RULE-002: Code Style Conventions
<!-- type: RULE -->
<!-- created: 2026-02-17 -->
<!-- tags: style, conventions, python, naming, formatting, freqtrade, code-generation -->
<!-- links: CODE-001, LEARN-001 -->

## Purpose
Enforces consistent code style across all generated code. The coding agent MUST follow these conventions.

## Python Style

### General
- Python 3.10+ (match statements allowed, `X | Y` union types allowed)
- PEP 8 compliance (4 spaces, 79 char lines for code, 120 for comments)
- Type hints on all function signatures
- Docstrings on all public functions (Google style)

### Naming Conventions

| Element | Convention | Example |
|---------|-----------|---------|
| Strategy class | PascalCase | `DonchianBreakout` |
| Function/method | snake_case | `populate_indicators` |
| Variable | snake_case | `ema_short` |
| Constant | UPPER_SNAKE | `ALLOWED_IMPORTS` |
| DataFrame column | snake_case, descriptive | `rsi_14`, `ema_50`, `bb_upper` |
| Hyperopt parameter | snake_case with buy_/sell_ prefix | `buy_rsi_threshold` |
| Test function | `test_` prefix, descriptive | `test_populate_indicators_adds_rsi` |

### DataFrame Column Naming

Indicator columns MUST include the parameter that distinguishes them:

```python
# GOOD — clear which EMA period
dataframe['ema_9'] = ta.EMA(dataframe, timeperiod=9)
dataframe['ema_21'] = ta.EMA(dataframe, timeperiod=21)
dataframe['rsi_14'] = ta.RSI(dataframe, timeperiod=14)

# BAD — ambiguous
dataframe['ema'] = ta.EMA(dataframe, timeperiod=9)
dataframe['rsi'] = ta.RSI(dataframe, timeperiod=14)  # OK if only one RSI
```

Exception: When only one instance of an indicator is used, the bare name is acceptable (e.g., `dataframe['rsi']` if there's only one RSI).

### Import Order

```python
# 1. Freqtrade framework
from freqtrade.strategy import IStrategy, IntParameter, DecimalParameter
from pandas import DataFrame

# 2. Indicator libraries
import talib.abstract as ta
from freqtrade.vendor import qtpylib
from technical.indicators import ichimoku  # if needed

# 3. Python stdlib
import logging
from datetime import datetime
from typing import Optional

# 4. Standard alias
logger = logging.getLogger(__name__)
```

### Strategy File Structure

Always in this order:
1. Module docstring (with economic thesis)
2. Imports (ordered as above)
3. Logger
4. Class definition
5. Class docstring
6. Class attributes (INTERFACE_VERSION, timeframe, minimal_roi, stoploss, trailing_stop, startup_candle_count, order_types)
7. Hyperopt parameters
8. `informative_pairs()` (if needed)
9. `populate_indicators()`
10. `populate_entry_trend()`
11. `populate_exit_trend()`
12. Optional callbacks (custom_stoploss, custom_exit, etc.)

### Signal Conditions

```python
# GOOD — each condition on its own line, clear logical structure
dataframe.loc[
    (
        (qtpylib.crossed_above(dataframe['ema_9'], dataframe['ema_21']))
        &
        (dataframe['rsi'] < 70)
        &
        (dataframe['adx'] > 20)
        &
        (dataframe['volume'] > 0)
    ),
    'enter_long'] = 1

# BAD — all on one line
dataframe.loc[(qtpylib.crossed_above(dataframe['ema_9'], dataframe['ema_21'])) & (dataframe['rsi'] < 70) & (dataframe['volume'] > 0), 'enter_long'] = 1
```

### Comments

- No obvious comments (`# Calculate RSI` before `ta.RSI()` — skip it)
- Comment the WHY, not the WHAT
- Economic thesis in class docstring is mandatory
- Comment non-obvious parameter choices:
  ```python
  # ADX > 25 filters out ranging markets where crossover signals are unreliable
  (dataframe['adx'] > 25)
  ```

## Test File Style

- One test file per strategy: `test_<strategy_name>.py`
- Test functions are self-documenting: `test_entry_signal_requires_volume`
- Use fixtures from CODE-002 conftest.py
- AAA pattern: Arrange, Act, Assert (one blank line between sections)
- No unnecessary assertions — test one thing per test

## Known Issues
- PEP 8 line length (79) may be too restrictive for complex DataFrame conditions. Allow 120 for signal conditions.
- Column naming convention (include period) adds verbosity but prevents bugs when multiple indicator periods are used.
