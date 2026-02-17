# LEARN-007: ta-lib Indicator Reference
<!-- type: LEARN -->
<!-- created: 2026-02-17 -->
<!-- tags: ta-lib, indicators, technical-analysis, freqtrade, qtpylib, technical-library, python -->
<!-- links: LEARN-001 -->

## Purpose
Complete technical reference for ta-lib indicators used in Freqtrade strategy generation. Covers function signatures, defaults, return types, Freqtrade usage patterns, qtpylib helpers, the `technical` library, and common gotchas.

## API Styles

### Function API
Pass raw numpy arrays:
```python
import talib
output = talib.SMA(dataframe['close'].values, timeperiod=25)
```

### Abstract API (preferred in Freqtrade)
Pass DataFrame directly — auto-selects correct price inputs:
```python
import talib.abstract as ta
dataframe['rsi'] = ta.RSI(dataframe, timeperiod=14)        # uses 'close'
dataframe['sma_open'] = ta.SMA(dataframe, timeperiod=25, price='open')  # override
```

**Always use Abstract API in Freqtrade strategies** — it auto-selects high/low/close/volume as needed per function.

## Freqtrade Column Assignment Pattern

```python
import talib.abstract as ta
from freqtrade.vendor import qtpylib

def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
    # Single-output: assign directly
    dataframe['rsi'] = ta.RSI(dataframe, timeperiod=14)
    dataframe['adx'] = ta.ADX(dataframe, timeperiod=14)

    # Multi-output: unpack into separate columns
    macd = ta.MACD(dataframe, fastperiod=12, slowperiod=26, signalperiod=9)
    dataframe['macd'] = macd['macd']
    dataframe['macdsignal'] = macd['macdsignal']
    dataframe['macdhist'] = macd['macdhist']

    bollinger = qtpylib.bollinger_bands(qtpylib.typical_price(dataframe), window=20, stds=2)
    dataframe['bb_lowerband'] = bollinger['lower']
    dataframe['bb_middleband'] = bollinger['mid']
    dataframe['bb_upperband'] = bollinger['upper']

    return dataframe
```

---

## 1. Overlap Studies

| Function | Signature | Defaults | Returns | Inputs |
|----------|-----------|----------|---------|--------|
| **SMA** | `SMA(close, timeperiod)` | timeperiod=30 | single real | close |
| **EMA** | `EMA(close, timeperiod)` | timeperiod=30 | single real | close |
| **DEMA** | `DEMA(close, timeperiod)` | timeperiod=30 | single real | close |
| **TEMA** | `TEMA(close, timeperiod)` | timeperiod=30 | single real | close |
| **WMA** | `WMA(close, timeperiod)` | timeperiod=30 | single real | close |
| **BBANDS** | `BBANDS(close, timeperiod, nbdevup, nbdevdn, matype)` | timeperiod=5, nbdevup=2.0, nbdevdn=2.0, matype=0 | 3: upperband, middleband, lowerband | close |
| **SAR** | `SAR(high, low, acceleration, maximum)` | acceleration=0.02, maximum=0.2 | single real | high, low |
| **HT_TRENDLINE** | `HT_TRENDLINE(close)` | none | single real | close |

**matype values:** 0=SMA, 1=EMA, 2=WMA, 3=DEMA, 4=TEMA, 5=TRIMA, 6=KAMA, 7=MAMA, 8=T3

---

## 2. Momentum Indicators

| Function | Signature | Defaults | Returns | Inputs |
|----------|-----------|----------|---------|--------|
| **RSI** | `RSI(close, timeperiod)` | timeperiod=14 | single (0-100) | close |
| **MACD** | `MACD(close, fastperiod, slowperiod, signalperiod)` | 12, 26, 9 | 3: macd, macdsignal, macdhist | close |
| **STOCH** | `STOCH(high, low, close, fastk_period, slowk_period, slowk_matype, slowd_period, slowd_matype)` | 5, 3, 0, 3, 0 | 2: slowk, slowd | high, low, close |
| **STOCHRSI** | `STOCHRSI(close, timeperiod, fastk_period, fastd_period, fastd_matype)` | 14, 5, 3, 0 | 2: fastk, fastd | close |
| **CCI** | `CCI(high, low, close, timeperiod)` | timeperiod=14 | single real | high, low, close |
| **ADX** | `ADX(high, low, close, timeperiod)` | timeperiod=14 | single (0-100) | high, low, close |
| **PLUS_DI** | `PLUS_DI(high, low, close, timeperiod)` | timeperiod=14 | single real | high, low, close |
| **MINUS_DI** | `MINUS_DI(high, low, close, timeperiod)` | timeperiod=14 | single real | high, low, close |
| **WILLR** | `WILLR(high, low, close, timeperiod)` | timeperiod=14 | single (-100 to 0) | high, low, close |
| **MOM** | `MOM(close, timeperiod)` | timeperiod=10 | single real | close |
| **ROC** | `ROC(close, timeperiod)` | timeperiod=10 | single (percentage) | close |
| **MFI** | `MFI(high, low, close, volume, timeperiod)` | timeperiod=14 | single (0-100) | high, low, close, volume |

---

## 3. Volume Indicators

| Function | Signature | Defaults | Returns | Inputs |
|----------|-----------|----------|---------|--------|
| **AD** | `AD(high, low, close, volume)` | none | single (cumulative) | high, low, close, volume |
| **ADOSC** | `ADOSC(high, low, close, volume, fastperiod, slowperiod)` | 3, 10 | single real | high, low, close, volume |
| **OBV** | `OBV(close, volume)` | none | single (cumulative) | close, volume |

---

## 4. Volatility Indicators

| Function | Signature | Defaults | Returns | Inputs |
|----------|-----------|----------|---------|--------|
| **ATR** | `ATR(high, low, close, timeperiod)` | timeperiod=14 | single real | high, low, close |
| **NATR** | `NATR(high, low, close, timeperiod)` | timeperiod=14 | single (normalized %) | high, low, close |
| **TRANGE** | `TRANGE(high, low, close)` | none | single real | high, low, close |

---

## 5. Pattern Recognition (CDL* Functions)

All take `(open, high, low, close)`. Return **integer** arrays: 100 (bullish), -100 (bearish), 0 (none), rarely 80/-80.

**Top 10 patterns:**

| Function | Pattern | Type |
|----------|---------|------|
| `CDLHAMMER` | Hammer | Single, bullish reversal |
| `CDLINVERTEDHAMMER` | Inverted Hammer | Single, bullish reversal |
| `CDLENGULFING` | Engulfing | Two candle, +100 bullish / -100 bearish |
| `CDLMORNINGSTAR` | Morning Star | Three candle, bullish reversal |
| `CDLEVENINGSTAR` | Evening Star | Three candle, bearish reversal |
| `CDL3WHITESOLDIERS` | Three White Soldiers | Three candle, bullish |
| `CDL3BLACKCROWS` | Three Black Crows | Three candle, bearish |
| `CDLDOJI` | Doji | Single, indecision |
| `CDLHARAMI` | Harami | Two candle, reversal |
| `CDLSHOOTINGSTAR` | Shooting Star | Single, bearish reversal |

```python
dataframe['cdl_hammer'] = ta.CDLHAMMER(dataframe)
# In entry conditions: (dataframe['cdl_hammer'] == 100)
# In exit conditions: (dataframe['cdl_engulfing'] < 0)
```

61+ candlestick patterns total in ta-lib.

---

## 6. qtpylib Indicators (Freqtrade bundled)

`from freqtrade.vendor import qtpylib`

| Function | Returns |
|----------|---------|
| `qtpylib.bollinger_bands(series, window=20, stds=2)` | DataFrame: 'upper', 'mid', 'lower' |
| `qtpylib.typical_price(dataframe)` | Series: (H+L+C)/3 |
| `qtpylib.weighted_close(dataframe)` | Series: (H+L+C+C)/4 |
| `qtpylib.heikinashi(dataframe)` | DataFrame: ha_open, ha_high, ha_low, ha_close |
| `qtpylib.crossed_above(s1, s2)` | Boolean Series |
| `qtpylib.crossed_below(s1, s2)` | Boolean Series |

**`crossed_above` / `crossed_below` are critical for entry/exit signals:**
```python
# Entry: EMA crossover
(qtpylib.crossed_above(dataframe['ema_9'], dataframe['ema_21']))
# Entry: RSI crosses above oversold
(qtpylib.crossed_above(dataframe['rsi'], 30))
```

---

## 7. `technical` Library Indicators

`from technical.indicators import ...` — companion library for indicators not in ta-lib.

Key indicators: **ichimoku** (full cloud), **VWAP**, **williams_fractal**, **pivots_points**, **cmf** (Chaikin Money Flow), **hull_moving_average**, **ssl_channel**, **RMI** (Relative Momentum Index).

---

## Common Gotchas

### NaN Handling
- ta-lib produces NaN for initial lookback period (e.g., SMA(30) → 29 NaN values)
- C library can propagate NaN unexpectedly — one NaN input may propagate to end of output
- Always `.fillna(0)` or `.fillna(False)` in buy/sell conditions where needed

### startup_candle_count
- Must be >= maximum lookback period of any indicator
- **Rule of thumb: 2x-4x the longest indicator period** (EMA has infinite impulse response — EMA(100) needs ~400 startup candles for stable values)
- Startup candles are fetched but excluded from backtest/live signals
- Example: `startup_candle_count: int = 400` for EMA(100)

### Integer vs Float Returns
- Most indicators return float64
- CDL* patterns return integers (100, -100, 0)
- Compare CDL* with `== 100`, not `> 0.5`

### Abstract API Auto-Selection
- RSI/SMA/EMA default to 'close' (override with `price='open'`)
- STOCH/ATR/CCI auto-use high/low/close
- MFI/AD/ADOSC auto-use high/low/close/volume
- DataFrame columns MUST be lowercase ('close' not 'Close') or Abstract API fails

### STOCHRSI Range
- ta-lib Python returns 0-100 (some implementations return 0-1) — always verify range

### Performance
- Compute ALL indicators in `populate_indicators()`, never in `populate_entry_trend()`
- NEVER call ta-lib row-by-row in a loop — vectorized C operations only
- One call per indicator per full dataframe is the correct pattern

## Known Issues
- ta-lib installation problematic on Windows (needs pre-built binaries)
- BBANDS default timeperiod=5 is unusually short — most strategies use 20
- SAR can whipsaw in sideways markets — often combined with trend filter (ADX)
