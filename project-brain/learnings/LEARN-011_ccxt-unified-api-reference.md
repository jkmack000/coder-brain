# LEARN-011: CCXT Unified API Reference
<!-- type: LEARN -->
<!-- created: 2026-02-18 -->
<!-- tags: ccxt, exchange-api, trading, unified-api, freqtrade, python, market-data, orders, error-handling, async -->
<!-- links: LEARN-001, LEARN-003, SPEC-001 -->

## Context
CCXT is the exchange abstraction layer used by Freqtrade. This reference covers everything a coding agent needs: unified API signatures, market structure, error handling, async patterns, order lifecycle, and exchange quirks. Current: CCXT v4.x (Feb 2026).

## 1. Exchange Instantiation

### Sync
```python
import ccxt

exchange = ccxt.binance({
    'apiKey': 'YOUR_API_KEY',
    'secret': 'YOUR_SECRET_KEY',
    'password': 'YOUR_PASSPHRASE',   # Some exchanges (e.g., OKX)
    'enableRateLimit': True,         # ALWAYS set True in production
    'rateLimit': 200,                # ms between requests
    'timeout': 30000,                # Request timeout ms (default: 10000)
    'options': {
        'adjustForTimeDifference': True,   # Binance clock drift
        'defaultType': 'spot',             # 'spot', 'margin', 'future', 'swap'
        'defaultMarginMode': 'isolated',
    },
})
```

### Async
```python
import ccxt.async_support as ccxt_async

exchange = ccxt_async.binance({'apiKey': 'KEY', 'secret': 'SECRET', 'enableRateLimit': True})
try:
    ticker = await exchange.fetch_ticker('BTC/USDT')
finally:
    await exchange.close()  # CRITICAL: prevents resource leaks
```

### Sandbox / Testnet
```python
exchange.set_sandbox_mode(True)
# Binance testnet moved to https://demo-api.binance.com in 2025
```

### Loading Markets (Required)
```python
markets = exchange.load_markets()  # Do once at startup
```

## 2. Market Structure

### Symbol Format

| Market Type | Format | Example |
|-------------|--------|---------|
| Spot | `BASE/QUOTE` | `BTC/USDT` |
| Linear perpetual | `BASE/QUOTE:SETTLE` | `BTC/USDT:USDT` |
| Inverse perpetual | `BASE/QUOTE:SETTLE` | `BTC/USD:BTC` |
| Linear future | `BASE/QUOTE:SETTLE-YYMMDD` | `BTC/USDT:USDT-250328` |
| Option | `BASE/QUOTE:SETTLE-YYMMDD-STRIKE-C/P` | `BTC/USDT:USDT-250328-50000-C` |

**Do NOT parse symbol strings.** Use market properties instead.

### Market Object Key Fields
```python
market = exchange.markets['BTC/USDT']
market['type']       # 'spot', 'margin', 'swap', 'future', 'option'
market['base']       # 'BTC'
market['quote']      # 'USDT'
market['active']     # True/False
market['contract']   # True if derivative
market['linear']     # True = settled in quote
market['inverse']    # True = settled in base
market['precision']  # {'amount': 0.001, 'price': 0.01}
market['limits']     # {'amount': {'min': 0.00001, 'max': 9000.0}, ...}
market['maker']      # 0.001 (maker fee rate)
market['taker']      # 0.001 (taker fee rate)
```

**Precision vs Limits:** Independent concepts. Precision `0.01` does NOT mean min amount is `0.01`.

### Formatting Values for Orders
```python
amount = exchange.amount_to_precision('BTC/USDT', 0.123456789)
price = exchange.price_to_precision('BTC/USDT', 42000.123456)
```

## 3. Public API Methods

### fetchTicker
```python
ticker = exchange.fetch_ticker('BTC/USDT')
# Returns: symbol, timestamp, high, low, bid, ask, open, close, last,
#          change, percentage, baseVolume, quoteVolume
```

### fetchOrderBook
```python
orderbook = exchange.fetch_order_book('BTC/USDT', limit=20)
# Returns: bids [[price, amount], ...], asks [[price, amount], ...]
```

### fetchOHLCV
```python
ohlcv = exchange.fetch_ohlcv(
    symbol='BTC/USDT',
    timeframe='1h',
    since=None,        # Start timestamp in ms
    limit=None,        # Max candles (exchange-specific, usually 500-1500)
)
# Returns: [[timestamp, open, high, low, close, volume], ...]
```

### Timeframe Strings
`'1m'`, `'3m'`, `'5m'`, `'15m'`, `'30m'`, `'1h'`, `'2h'`, `'4h'`, `'6h'`, `'12h'`, `'1d'`, `'1w'`, `'1M'` (capital M for month)

Check available: `exchange.timeframes`

### OHLCV Pagination for Historical Data
```python
def fetch_all_ohlcv(exchange, symbol, timeframe, since, limit=1000):
    all_candles = []
    timeframe_ms = exchange.parse_timeframe(timeframe) * 1000
    while True:
        candles = exchange.fetch_ohlcv(symbol, timeframe, since=since, limit=limit)
        if not candles:
            break
        all_candles.extend(candles)
        since = candles[-1][0] + timeframe_ms
        if len(candles) < limit:
            break
    return all_candles
```

### Timestamp Helpers
```python
ts = exchange.parse8601('2024-01-01T00:00:00Z')   # ISO8601 -> ms
dt = exchange.iso8601(ts)                           # ms -> ISO8601
seconds = exchange.parse_timeframe('1h')            # timeframe -> seconds
```

## 4. Private API Methods

### fetchBalance
```python
balance = exchange.fetch_balance()
# balance['BTC']['free'], balance['BTC']['used'], balance['BTC']['total']
# For derivatives: params={'type': 'swap'}
```

### createOrder
```python
order = exchange.create_order(symbol, type, side, amount, price=None, params={})

# Market buy
exchange.create_order('BTC/USDT', 'market', 'buy', 0.001)

# Limit buy
exchange.create_order('BTC/USDT', 'limit', 'buy', 0.001, 45000.0)

# Stop-loss
exchange.create_order('BTC/USDT', 'market', 'sell', 0.001, None, {
    'triggerPrice': 44500.0,
})

# Take-profit
exchange.create_order('BTC/USDT', 'limit', 'sell', 0.001, 55000.0, {
    'takeProfitPrice': 55000.0,
})

# SL + TP simultaneously
exchange.create_order('BTC/USDT', 'limit', 'sell', 0.001, 55000.0, {
    'stopLossPrice': 44000.0,
    'takeProfitPrice': 55000.0,
})
```

### Derivatives
```python
exchange.set_leverage(10, 'BTC/USDT:USDT')
exchange.set_margin_mode('isolated', 'BTC/USDT:USDT')
exchange.create_order('BTC/USDT:USDT', 'market', 'buy', 0.01)
# Close: params={'reduceOnly': True}
```

### Order Status Lifecycle
`open` → `closed` (filled) | `canceled` | `expired`

**Caution:** Some exchanges report canceled orders as 'closed'. Check `filled` vs `amount`.

### Order Management
```python
exchange.cancel_order(id, symbol)
exchange.fetch_order(id, symbol)
exchange.fetch_open_orders(symbol)
exchange.fetch_closed_orders(symbol)
exchange.fetch_my_trades(symbol)
```

## 5. Async vs Sync

| Pattern | Use Case |
|---------|----------|
| **Sync** (`ccxt.binance`) | Simple scripts, Freqtrade strategies (FT handles async internally) |
| **Async** (`ccxt.async_support.binance`) | Multi-exchange data fetching, high-throughput pipelines |

### Multi-Exchange Async
```python
async def fetch_multiple_tickers():
    exchange = ccxt_async.binance({'enableRateLimit': True})
    try:
        await exchange.load_markets()
        tickers = await asyncio.gather(
            exchange.fetch_ticker('BTC/USDT'),
            exchange.fetch_ticker('ETH/USDT'),
        )
        return tickers
    finally:
        await exchange.close()
```

### Async Pitfalls
1. Forgetting `await exchange.close()` — resource leaks
2. Recreating instances per request — rate limiter resets
3. Mixing sync and async — separate classes, never mix

## 6. Error Handling

### Exception Hierarchy (Key Branches)
```
BaseError
├── ExchangeError
│   ├── AuthenticationError / PermissionDenied
│   ├── InsufficientFunds
│   ├── InvalidOrder / OrderNotFound
│   ├── BadRequest / BadSymbol
│   └── NotSupported
├── NetworkError
│   ├── DDoSProtection / RateLimitExceeded
│   ├── ExchangeNotAvailable
│   └── RequestTimeout
└── BadResponse / NullResponse
```

### Retry Pattern
```python
def safe_api_call(exchange, method, *args, max_retries=3, **kwargs):
    for attempt in range(max_retries):
        try:
            return getattr(exchange, method)(*args, **kwargs)
        except ccxt.NetworkError:
            if attempt == max_retries - 1:
                raise
            time.sleep(2 ** attempt)
        except ccxt.RateLimitExceeded:
            time.sleep(30 + 10 * attempt)
        except ccxt.ExchangeError:
            raise  # Do NOT retry application errors
```

### Retryability Quick Reference
| Exception | Retryable? |
|-----------|-----------|
| `NetworkError`, `RequestTimeout` | Yes (backoff) |
| `RateLimitExceeded` | Yes (30s+ backoff) |
| `ExchangeNotAvailable` | Yes (long backoff) |
| `AuthenticationError`, `InsufficientFunds`, `InvalidOrder`, `BadSymbol` | No |

**Critical:** CCXT internal `maxRetriesOnFailure` retries ALL exceptions including app errors. Implement your own retry logic.

## 7. Exchange-Specific Quirks

| Feature | Binance | Bybit | OKX | Kraken |
|---------|---------|-------|-----|--------|
| Auth | key+secret | key+secret | key+secret+password | key+secret |
| Rate limit | 1200/min | 120/min | 60/2s | 15/s |
| Max OHLCV/req | 1500 | 1000 | 300 | 720 |
| Futures symbol | `BTC/USDT:USDT` | `BTC/USDT:USDT` | `BTC/USDT:USDT` | N/A |
| Testnet | Yes | Yes | Yes (demo) | No |

**Binance:** Use `adjustForTimeDifference: True`. Testnet URL changed 2025.
**Bybit:** Balance includes extra `debt` key. createOrder returns cost not amount.
**OKX:** Requires passphrase. Set position mode via `set_position_mode()`.

## 8. CCXT + Freqtrade Integration

### Freqtrade Handles (NOT strategy author's concern)
Connection, auth, reconnection, rate limiting, OHLCV fetching, order execution, position management, error handling/retries.

### Strategy Authors Need to Know
- DataFrame columns from CCXT: `open`, `high`, `low`, `close`, `volume`, `date`
- Signal columns: `enter_long`, `enter_short`, `exit_long`, `exit_short` (set to 1)
- Timeframe must be valid CCXT string: `timeframe = '5m'`
- Pair format: `BTC/USDT` (spot) or `BTC/USDT:USDT` (futures)
- **Never call CCXT directly** — use `self.dp` (DataProvider)

### Exchange Config
```json
{
    "exchange": {
        "name": "binance",
        "key": "KEY",
        "secret": "SECRET",
        "ccxt_config": {"enableRateLimit": true, "options": {"defaultType": "spot"}}
    }
}
```

## 9. Common Recipes

```python
# OHLCV to pandas
df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms')

# All active spot symbols
spot = [s for s, m in exchange.markets.items() if m['spot'] and m['active']]

# All USDT perpetual swaps
swaps = [s for s, m in exchange.markets.items()
         if m['swap'] and m['active'] and m['quote'] == 'USDT' and m['linear']]

# Check feature support
if exchange.has['fetchOHLCV']:
    candles = exchange.fetch_ohlcv('BTC/USDT', '1h')
```

## 10. Key Gotchas Summary
1. Always `load_markets()` first
2. Always `enableRateLimit: True`
3. Never recreate exchange instances in a loop
4. Close async exchanges with `await exchange.close()`
5. Symbol format differs by market type
6. Precision != limits
7. Some createOrder fields may be None — use fetchOrder for complete state
8. Do not parse symbol strings — use market properties
9. Implement own retry logic (CCXT internal retry is broken)
10. Freqtrade strategies never call CCXT directly — use DataProvider

## Known Issues
- CCXT v4.x point-in-time (Feb 2026). Fee info "experimental/unstable".
- Binance testnet URLs changed 2025.
- `paginate` option in fetchOHLCV is experimental.
- Bybit and OKX frequently update APIs, requiring CCXT version bumps.
