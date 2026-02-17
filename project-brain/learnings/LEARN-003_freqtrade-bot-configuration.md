# LEARN-003: Freqtrade Bot Configuration
<!-- type: LEARN -->
<!-- created: 2026-02-17 -->
<!-- tags: freqtrade, configuration, config-json, exchange, dry-run, stake, pairlist, fees, order-types -->
<!-- links: LEARN-001, LEARN-004 -->

## Purpose
Complete reference for Freqtrade's config.json structure, exchange setup, trading modes, dry-run vs live, stake management, fee handling, and order configuration. Enables the coding agent to generate valid configuration files and understand parameter interactions.

## config.json Structure

- Default file: `config.json` in working directory. Override with `-c/--config`.
- Supports `//` and `/* */` comments, trailing commas.
- Generate fresh: `freqtrade new-config --config user_data/config.json`
- JSON schema: `"$schema": "https://schema.freqtrade.io/schema.json"` for editor autocomplete.
- Multiple configs via `add_config_files` array or multiple `--config` CLI args (last wins on collision).
- Validate: `freqtrade show-config`

### Configuration Precedence (highest to lowest)
1. CLI arguments
2. Environment variables (`FREQTRADE__` prefix, `__` as level separator)
3. Configuration files (last specified wins)
4. Strategy values (Strategy Override params — config ALWAYS overrides strategy)

### Environment Variables
```bash
export FREQTRADE__STAKE_AMOUNT=200                     # → stake_amount: 200
export FREQTRADE__EXCHANGE__KEY=<key>                  # → exchange.key
export FREQTRADE__EXCHANGE__PAIR_WHITELIST='["BTC/USDT", "ETH/USDT"]'  # JSON lists
```

## Required Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `max_open_trades` | int or -1 | Concurrent open trades. -1 = unlimited. Strategy Override. |
| `stake_currency` | string | Quote currency (e.g., "USDT"). |
| `stake_amount` | float or `"unlimited"` | Amount per trade. `"unlimited"` = dynamic split. |
| `dry_run` | bool | `true` = simulation (default). `false` = live. |
| `minimal_roi` | dict | ROI table. Strategy Override. |
| `stoploss` | float | Negative ratio (e.g., -0.10). Strategy Override. |
| `unfilledtimeout.entry` | int | Minutes before unfilled entry cancelled. Strategy Override. |
| `unfilledtimeout.exit` | int | Minutes before unfilled exit cancelled. Strategy Override. |

## Exchange Setup

```json
{
  "exchange": {
    "name": "binance",
    "key": "<api_key>",
    "secret": "<api_secret>",
    "password": "",
    "pair_whitelist": ["ETH/USDT", "BTC/USDT"],
    "pair_blacklist": ["BNB/USDT"],
    "ccxt_config": {},
    "ccxt_sync_config": {},
    "ccxt_async_config": {},
    "enable_ws": true,
    "markets_refresh_interval": 60
  }
}
```

**Pair naming (ccxt standard):**
- Spot: `BASE/QUOTE` (e.g., `ETH/USDT`)
- Futures: `BASE/QUOTE:SETTLE` (e.g., `ETH/USDT:USDT`)
- Wildcards supported: `".*/USDT"` matches all USDT pairs

## Trading Modes

| Parameter | Default | Values |
|-----------|---------|--------|
| `trading_mode` | `"spot"` | `"spot"`, `"margin"`, `"futures"` |
| `margin_mode` | none | `"isolated"`, `"cross"` (required for margin/futures) |
| `liquidation_buffer` | 0.05 | Safety ratio between liquidation and stoploss |

## Dry-Run vs Live

**Dry-run (`dry_run: true`):**
- No real orders. Read-only exchange operations.
- Wallet: `dry_run_wallet` (default 1000). Can be float or dict: `{"BTC": 0.01, "USDT": 1000}`
- DB: `tradesv3.dryrun.sqlite`
- Market orders fill with max 5% slippage simulation.
- API keys not required.

**Live (`dry_run: false`):**
- Real orders. API keys required.
- DB: `tradesv3.sqlite` (separate from dry-run!)
- Keep secrets in separate config file.

## Stake Amount and Balance

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `stake_amount` | float/`"unlimited"` | required | Static or dynamic per-trade amount |
| `tradable_balance_ratio` | float 0.1-1.0 | 0.99 | Fraction of balance bot may use |
| `available_capital` | float | none | Starting capital (multi-bot). Replaces `tradable_balance_ratio` |

**Dynamic formula:** `balance / (max_open_trades - current_open_trades)`

**Minimum trade:** Exchange min * (1 + `amount_reserve_percent`) / (1 - abs(`stoploss`))

## Order Types Configuration

```python
order_types = {
    "entry": "limit",
    "exit": "limit",
    "emergency_exit": "market",
    "force_entry": "market",
    "force_exit": "market",
    "stoploss": "market",
    "stoploss_on_exchange": False,
    "stoploss_on_exchange_interval": 60,
    "stoploss_on_exchange_limit_ratio": 0.99
}
```

## Pricing Configuration

```json
{
  "entry_pricing": {
    "price_side": "same",
    "use_order_book": true,
    "order_book_top": 1
  },
  "exit_pricing": {
    "price_side": "same",
    "use_order_book": true,
    "order_book_top": 1
  }
}
```

**Pricing side (long):** `"same"` entry = bid (maker), `"other"` entry = ask (taker, faster fill). Reversed for short.

**For market orders:** Set `price_side: "other"` on both for realistic fills.

## Other Important Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `process_only_new_candles` | true | Recalculate only on new candles. Strategy Override. |
| `timeframe` | strategy | "1m", "5m", "15m", "1h", etc. Strategy Override. |
| `initial_state` | "stopped" | "running", "paused", "stopped" |
| `use_exit_signal` | true | Use strategy exit signals. Strategy Override. |
| `position_adjustment_enable` | false | Allow DCA. Strategy Override. |
| `dataformat_ohlcv` | "feather" | Storage format |
| `reduce_df_footprint` | false | Recast to float32 to save RAM |

## Gotchas

1. **Env vars override config silently** — `FREQTRADE__` prefix vars logged at startup.
2. **`add_config_files` parent wins** — opposite of multiple `--config` where last wins.
3. **Separate databases** for dry-run and live — reusing taints statistics.
4. **`"unlimited"` with default wallet** — set a sensible `dry_run_wallet`.
5. **Position adjustment with unlimited** — must implement `custom_stake_amount()` returning 25-50%.
6. **Market orders need `price_side: "other"`** for realistic backtesting.
7. **Strategy Override is one-way** — config always overrides strategy values, never reversed.
8. **`order_types` must be complete in config** — partial override fails.
9. **Fees applied twice** — entry + exit when overriding via `fee` parameter.

## Known Issues
- Coingecko rate limiting on some IPs (only affects fiat display, not trading).
- `stoploss_on_exchange` with very wide stoploss may fail exchange limits.
