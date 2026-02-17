# LEARN-004: Freqtrade Bot Lifecycle
<!-- type: LEARN -->
<!-- created: 2026-02-17 -->
<!-- tags: freqtrade, lifecycle, trading-loop, stoploss, trailing-stop, roi, callbacks, startup, shutdown -->
<!-- links: LEARN-001, LEARN-003 -->

## Purpose
Documents the Freqtrade bot startup sequence, trading loop mechanics, stoploss/ROI systems, callback order, and shutdown behavior. Critical for understanding when strategy code executes and how live differs from backtesting.

## Bot Startup Sequence

1. `freqtrade trade` command invoked
2. Config files merged, env vars applied, CLI args override
3. Configuration validated (syntax errors with line numbers)
4. Exchange connection established (ccxt sync + async)
5. Markets loaded from exchange
6. **`bot_start()` callback** — called once at startup
7. `initial_state` determines if trading begins (`"running"`) or waits for `/start` (`"stopped"`, default)
8. Main iteration loop begins

## Trading Loop

Runs every `process_throttle_secs` seconds (default **5s**):

1. Fetch open trades from DB
2. Calculate tradable pairs (pairlist evaluation)
3. Download OHLCV data (once per new candle if `process_only_new_candles=true`)
4. **`bot_loop_start()`** callback
5. **Per pair analysis:**
   - `populate_indicators()` — compute indicators
   - `populate_entry_trend()` — generate entry signals
   - `populate_exit_trend()` — generate exit signals
6. Update open order state from exchange → **`order_filled()`** callback
7. Check timeouts → **`check_entry_timeout()`**, **`check_exit_timeout()`**, **`adjust_order_price()`**
8. **Process exits** (priority order below)
9. Check position adjustments → **`adjust_trade_position()`**
10. Check available trade slots
11. **Process entries** → `custom_entry_price()` → `leverage()` → `custom_stake_amount()` → `confirm_trade_entry()`

## Exit Priority Order

When multiple conditions met simultaneously:
1. **Stoploss** (highest priority)
2. **ROI** (`minimal_roi` table)
3. **Exit signal** (from `populate_exit_trend()`)
4. **`custom_exit()`** callback
5. **`custom_stoploss()`** callback

## Stoploss Mechanics

### Basic Stoploss
- `stoploss`: negative ratio (e.g., `-0.10` = -10%). Includes fees.
- Buy at $100, stoploss=-0.10 → triggers sell at $90.

### Trailing Stoploss Modes

**Mode 1 — Basic trailing** (`trailing_stop=true` only):
Stoploss follows price up at configured distance, never moves down.
```python
stoploss = -0.10
trailing_stop = True
# Buy $100 → stoploss $90. Price $102 → stoploss $91.80. Never goes down.
```

**Mode 2 — Trailing with tighter positive** (`trailing_stop_positive` set):
Starts at `stoploss` distance. Once in profit, switches to tighter `trailing_stop_positive`.
```python
stoploss = -0.10
trailing_stop = True
trailing_stop_positive = 0.02
trailing_stop_positive_offset = 0.0
# Buy $100 → stoploss $90. Price $102 → switches to -2% = $99.96.
```

**Mode 3 — Trailing with offset** (recommended for locking profits):
```python
stoploss = -0.10
trailing_stop = True
trailing_stop_positive = 0.02
trailing_stop_positive_offset = 0.03
trailing_only_offset_is_reached = False
# Buy $100. Trails at -10% until +3% reached. Then trails at -2%.
# At $103.50 → stoploss $101.43 (profit locked).
```

**Mode 4 — Static until offset, then trail** (`trailing_only_offset_is_reached=true`):
```python
stoploss = -0.10
trailing_stop = True
trailing_stop_positive = 0.02
trailing_stop_positive_offset = 0.03
trailing_only_offset_is_reached = True
# Stoploss stays FIXED at $90 until +3% reached. Then starts trailing at -2%.
```

### Stoploss on Exchange

- Places stoploss order directly on exchange after entry fills.
- Protects against crashes (executes on exchange, no network overhead).
- `stoploss_on_exchange_interval`: seconds between updates (default 60).
- `stoploss_on_exchange_limit_ratio`: limit = stop_price * ratio (default 0.99).
- If placement fails → `emergency_exit` (market order).
- With trailing stop, bot cancels and replaces stoploss order as price rises.

### Stoploss and Leverage
Stoploss defines **risk on your capital**, not price movement. At 10x leverage, -10% stoploss triggers on 1% price move.

## ROI Table (`minimal_roi`)

```python
minimal_roi = {
    "40": 0.0,    # After 40 min: exit if profit >= 0%
    "30": 0.01,   # After 30 min: exit if profit >= 1%
    "20": 0.02,   # After 20 min: exit if profit >= 2%
    "0":  0.04    # Immediately: exit if profit >= 4%
}
```

- Keys: minutes (strings). Values: minimum profit ratio.
- Default if not set: `{"0": 10}` (effectively disabled).
- Special: `"<N>": -1` forces exit after N minutes regardless.
- `ignore_roi_if_entry_signal=true` prevents ROI exit if entry signal still active.

## Strategy Callbacks

| Callback | When | Purpose |
|----------|------|---------|
| `bot_start()` | Once at startup | One-time init |
| `bot_loop_start()` | Every iteration | Per-loop setup |
| `populate_indicators()` | Per pair, per new candle | Compute indicators |
| `populate_entry_trend()` | Per pair, per new candle | Set entry signals |
| `populate_exit_trend()` | Per pair, per new candle | Set exit signals |
| `order_filled()` | When order fills | React to fills |
| `check_entry_timeout()` | Each iteration | Custom entry timeout logic |
| `check_exit_timeout()` | Each iteration | Custom exit timeout logic |
| `adjust_order_price()` | Each iteration | Adjust open order prices |
| `custom_exit()` | Each iteration | Custom exit logic (return reason string or None) |
| `custom_stoploss()` | Each iteration | Dynamic stoploss (return new ratio) |
| `custom_exit_price()` | When exit triggers | Override exit price |
| `custom_entry_price()` | When entry triggers | Override entry price |
| `custom_stake_amount()` | Before entry | Override stake for this trade |
| `confirm_trade_entry()` | Before entry order | Approve/reject (return bool) |
| `confirm_trade_exit()` | Before exit order | Approve/reject (return bool) |
| `leverage()` | Before entry (margin/futures) | Return leverage float |
| `adjust_trade_position()` | Each iteration (DCA) | Return +buy/-sell/None |

## Backtesting vs Live: Critical Differences

| Aspect | Live | Backtesting |
|--------|------|-------------|
| `populate_*()` calls | Every ~5s or per new candle | **Once per pair** (entire dataset) |
| Callbacks (custom_exit, etc.) | Every iteration (~5s) | At most **once per candle** |
| `--timeframe-detail` | N/A | Callbacks run per detail candle |

**This frequency difference is the #1 source of backtest vs live mismatches.**

## Shutdown Behavior

- `cancel_open_orders_on_exit` (default false): cancels unfilled orders on stop/Ctrl+C.
- Does NOT close open positions.
- Open trades persist in DB, picked up on restart.

## Known Issues
- Changing stoploss on open trades requires `/reload_config`. Cannot change if trailing stoploss already adjusted.
- `process_only_new_candles=false` creates high system load (recalculates every 5s).
