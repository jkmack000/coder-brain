# LEARN-005: Freqtrade Data Handling
<!-- type: LEARN -->
<!-- created: 2026-02-17 -->
<!-- tags: freqtrade, data, download, timeframes, pairlist, informative-pairs, merge, startup-candle-count, lookahead -->
<!-- links: LEARN-001, LEARN-006 -->

## Purpose
Reference for Freqtrade's data download system, storage formats, timeframe handling, informative pair merging, and data alignment gotchas. Critical for avoiding lookahead bias and ensuring correct multi-timeframe strategies.

## Downloading Historical Data

```bash
freqtrade download-data [options]
```

### Key Parameters
| Parameter | Description |
|-----------|-------------|
| `--exchange <name>` | Exchange (mandatory if no config) |
| `--pairs <p1> <p2>` | Pairs to download. Regex: `".*/USDT"` |
| `--pairs-file <file>` | Load pairs from file |
| `--timeframes <tf1> <tf2>` | Timeframes (default: `1m 5m`) |
| `--days <N>` | Last N days (default: 30) |
| `--timerange YYYYMMDD-YYYYMMDD` | Absolute date range |
| `--prepend` | Download earlier data (with `--timerange` end-date) |
| `--data-format-ohlcv {json,jsongz,feather,parquet}` | Storage format |
| `--trading-mode {spot,futures}` | Trading mode |

**Incremental downloads:** Without `--days`/`--timerange`, auto-calculates missing range and downloads from latest available to now.

```bash
# Last 30 days default
freqtrade download-data -c config.json

# Specific pairs, timeframes, 90 days
freqtrade download-data --exchange binance --pairs ETH/USDT BTC/USDT --timeframes 5m 1h 4h --days 90

# All USDT pairs
freqtrade download-data --exchange binance --pairs ".*/USDT" --timeframes 1h --days 60
```

## Data Formats

| Format | Extension | Notes |
|--------|-----------|-------|
| `json` | `.json` | Human-readable, largest |
| `jsongz` | `.json.gz` | Gzipped JSON |
| `feather` | `.feather` | **Default.** Best performance/size. Apache Arrow. |
| `parquet` | `.parquet` | Good for analytical workloads, columnar |

**Note:** `hdf5` removed in current stable. Only json/jsongz/feather/parquet supported.

**Convert between formats:**
```bash
freqtrade convert-data --format-from json --format-to feather -c config.json
```

## Timeframes

Exchange-dependent. Binance: `1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 8h, 12h, 1d, 3d, 1w, 1M`.

```bash
freqtrade list-timeframes --exchange binance
```

## Pair List Configuration

**StaticPairList (default):** Uses config whitelist/blacklist.
```json
{
  "pairlists": [{"method": "StaticPairList"}],
  "exchange": {
    "pair_whitelist": ["ETH/USDT", "BTC/USDT"],
    "pair_blacklist": ["BNB/USDT"]
  }
}
```

**VolumePairList (dynamic):** Top pairs by volume.
```json
{
  "pairlists": [{
    "method": "VolumePairList",
    "number_assets": 20,
    "sort_key": "quoteVolume",
    "refresh_period": 1800
  }]
}
```

**Important:** VolumePairList uses live data — for reproducible backtests, use StaticPairList.

Pairlist chaining: multiple handlers in sequence (first generates, rest filter/sort).

## Informative Pairs and Additional Timeframes

### Defining informative pairs
```python
def informative_pairs(self):
    return [
        ("ETH/USDT", "5m"),
        ("BTC/USDT", "15m"),
        ("BTC/USDT", "1d"),
    ]
```

### Fetching and merging in populate_indicators
```python
def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
    # Get informative data via DataProvider
    informative = self.dp.get_pair_dataframe(pair="BTC/USDT", timeframe="1d")
    informative['sma_20'] = ta.SMA(informative, timeperiod=20)

    # Merge into main dataframe
    dataframe = merge_informative_pair(
        dataframe, informative, self.timeframe, "1d", ffill=True
    )
    return dataframe
```

## merge_informative_pair()

```python
merge_informative_pair(dataframe, informative, timeframe, inf_timeframe, ffill=True, append_timeframe=True)
```

**What it does:**
1. Aligns timestamps between timeframes
2. Merges on `date` column
3. Forward-fills so every faster-TF candle has slower-TF values
4. Renames columns with suffix: `close_1d`, `sma_20_1d`, etc.

**Critical:** `ffill=True` required — without it, most rows are NaN. The merge handles lookahead correctly (higher TF data only available after period closes).

## Data Directory Structure

```
user_data/
  data/
    <exchange_name>/
      ETH_USDT-5m.feather
      BTC_USDT-1h.feather
  backtest_results/
  strategies/
```

Pair names use underscores in filenames: `ETH/USDT` → `ETH_USDT`.

## startup_candle_count

```python
class MyStrategy(IStrategy):
    startup_candle_count: int = 200
```

**Why it matters:**
- Indicators need historical data to warm up (SMA-200 needs 200 candles)
- Without enough startup candles, values are **unstable, not just NaN** — they compute but incorrectly
- Backtesting: strips first `startup_candle_count` candles from results
- Live: requests extra candles from exchange on startup

**Multi-timeframe calculation:** In main-TF candle units. Strategy on 5m using 1h informative with SMA-50 needs at least `50 * 12 = 600` five-minute candles.

**Validation:** `freqtrade recursive-analysis` — 0% variance means count is adequate.

## Lookahead Bias — The #1 Backtesting Trap

Freqtrade passes the **entire dataframe** to `populate_*()` at once in backtesting. If code references future data, it "sees the future."

**Causes:**
- Using `iloc[-1]` or non-shifted columns
- For-loops through rows
- Any non-vectorized operation that touches future indices

**Prevention:**
- Use `df.shift(1)` to reference previous candles
- Use vectorized operations only
- Run detection tools:
  ```bash
  freqtrade lookahead-analysis -c config.json -s MyStrategy
  freqtrade recursive-analysis -c config.json -s MyStrategy
  ```

**Data alignment issues:**
- `merge_informative_pair` handles lookahead correctly for higher TFs
- Different exchanges may have slightly different timestamps — validate merged data
- Exchange candle limits in live (500-1000) vs full dataset in backtesting can cause differences

## Known Issues
- `hdf5` format removed — old docs may reference it.
- VolumePairList not reproducible for backtesting.
- Exchange data limits in live may differ from backtest dataset sizes.
