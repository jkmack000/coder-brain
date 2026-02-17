# CODE-002: Test Scaffolding
<!-- type: CODE -->
<!-- created: 2026-02-17 -->
<!-- tags: testing, pytest, conftest, fixtures, strategy-tests, freqtrade, python -->
<!-- links: LEARN-001, CODE-001, RULE-003 -->

## Purpose
Reusable test scaffolding for validating generated Freqtrade strategies. Includes conftest.py with fixtures, strategy test patterns, and property-based tests.

## conftest.py

```python
"""
Shared test fixtures for Freqtrade strategy testing.
"""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, PropertyMock
from pathlib import Path


@pytest.fixture
def ohlcv_dataframe():
    """Generate a realistic OHLCV DataFrame for testing.

    Returns 500 rows of synthetic candle data with realistic price movement.
    """
    np.random.seed(42)
    n = 500
    dates = pd.date_range(start='2023-01-01', periods=n, freq='1h', tz=timezone.utc)

    # Generate realistic price series (random walk with drift)
    returns = np.random.normal(0.0001, 0.01, n)
    close = 100 * np.exp(np.cumsum(returns))

    # Generate OHLCV from close
    high = close * (1 + np.abs(np.random.normal(0, 0.005, n)))
    low = close * (1 - np.abs(np.random.normal(0, 0.005, n)))
    open_ = close * (1 + np.random.normal(0, 0.003, n))
    volume = np.random.lognormal(10, 1, n)

    df = pd.DataFrame({
        'date': dates,
        'open': open_,
        'high': high,
        'low': low,
        'close': close,
        'volume': volume,
    })

    # Ensure OHLC consistency
    df['high'] = df[['open', 'high', 'close']].max(axis=1)
    df['low'] = df[['open', 'low', 'close']].min(axis=1)

    return df


@pytest.fixture
def flat_dataframe():
    """DataFrame with flat prices (no movement). Tests edge cases."""
    n = 200
    dates = pd.date_range(start='2023-01-01', periods=n, freq='1h', tz=timezone.utc)

    return pd.DataFrame({
        'date': dates,
        'open': [100.0] * n,
        'high': [100.5] * n,
        'low': [99.5] * n,
        'close': [100.0] * n,
        'volume': [1000.0] * n,
    })


@pytest.fixture
def zero_volume_dataframe(ohlcv_dataframe):
    """DataFrame with some zero-volume candles."""
    df = ohlcv_dataframe.copy()
    # Set 10% of candles to zero volume
    zero_idx = np.random.choice(len(df), size=len(df) // 10, replace=False)
    df.loc[zero_idx, 'volume'] = 0
    return df


@pytest.fixture
def mock_metadata():
    """Standard metadata dict passed to strategy methods."""
    return {'pair': 'ETH/USDT', 'stake_currency': 'USDT'}


@pytest.fixture
def mock_dataprovider():
    """Mock DataProvider for informative pair tests."""
    dp = MagicMock()
    dp.get_pair_dataframe = MagicMock(return_value=pd.DataFrame())
    dp.current_whitelist = MagicMock(return_value=['ETH/USDT', 'BTC/USDT'])
    return dp
```

## Strategy Test Patterns

### Test: Strategy loads and has required attributes
```python
def test_strategy_attributes(strategy_class):
    """Verify strategy has all required IStrategy attributes."""
    strategy = strategy_class({})

    assert hasattr(strategy, 'timeframe')
    assert hasattr(strategy, 'minimal_roi')
    assert hasattr(strategy, 'stoploss')
    assert hasattr(strategy, 'startup_candle_count')

    assert isinstance(strategy.minimal_roi, dict)
    assert strategy.stoploss < 0  # Must be negative
    assert strategy.startup_candle_count >= 0
    assert strategy.timeframe in ['1m', '3m', '5m', '15m', '30m', '1h', '2h', '4h', '6h', '8h', '12h', '1d']
```

### Test: populate_indicators runs without error
```python
def test_populate_indicators(strategy_class, ohlcv_dataframe, mock_metadata):
    """Verify indicators are calculated without error."""
    strategy = strategy_class({})
    result = strategy.populate_indicators(ohlcv_dataframe.copy(), mock_metadata)

    assert isinstance(result, pd.DataFrame)
    assert len(result) == len(ohlcv_dataframe)
    assert 'close' in result.columns  # Original columns preserved
```

### Test: populate_entry_trend produces valid signals
```python
def test_populate_entry_trend(strategy_class, ohlcv_dataframe, mock_metadata):
    """Verify entry signals are binary and column exists."""
    strategy = strategy_class({})
    df = strategy.populate_indicators(ohlcv_dataframe.copy(), mock_metadata)
    result = strategy.populate_entry_trend(df, mock_metadata)

    assert 'enter_long' in result.columns
    # Signals must be 0, 1, or NaN
    valid_values = result['enter_long'].dropna().unique()
    assert all(v in [0, 1] for v in valid_values)
```

### Test: populate_exit_trend produces valid signals
```python
def test_populate_exit_trend(strategy_class, ohlcv_dataframe, mock_metadata):
    """Verify exit signals are binary and column exists."""
    strategy = strategy_class({})
    df = strategy.populate_indicators(ohlcv_dataframe.copy(), mock_metadata)
    df = strategy.populate_entry_trend(df, mock_metadata)
    result = strategy.populate_exit_trend(df, mock_metadata)

    assert 'exit_long' in result.columns
    valid_values = result['exit_long'].dropna().unique()
    assert all(v in [0, 1] for v in valid_values)
```

### Test: DataFrame shape preserved
```python
def test_dataframe_shape_preserved(strategy_class, ohlcv_dataframe, mock_metadata):
    """Verify strategy methods don't add or remove rows."""
    strategy = strategy_class({})
    original_len = len(ohlcv_dataframe)

    df = strategy.populate_indicators(ohlcv_dataframe.copy(), mock_metadata)
    assert len(df) == original_len

    df = strategy.populate_entry_trend(df, mock_metadata)
    assert len(df) == original_len

    df = strategy.populate_exit_trend(df, mock_metadata)
    assert len(df) == original_len
```

### Test: No entry signals on zero volume
```python
def test_no_entry_on_zero_volume(strategy_class, zero_volume_dataframe, mock_metadata):
    """Verify volume > 0 guard prevents entries on zero-volume candles."""
    strategy = strategy_class({})
    df = strategy.populate_indicators(zero_volume_dataframe.copy(), mock_metadata)
    df = strategy.populate_entry_trend(df, mock_metadata)

    zero_vol_entries = df.loc[df['volume'] == 0, 'enter_long']
    assert (zero_vol_entries.fillna(0) == 0).all(), "Entry signal found on zero-volume candle"
```

### Test: Handles flat market
```python
def test_flat_market(strategy_class, flat_dataframe, mock_metadata):
    """Verify strategy doesn't crash on flat price data."""
    strategy = strategy_class({})
    df = strategy.populate_indicators(flat_dataframe.copy(), mock_metadata)
    df = strategy.populate_entry_trend(df, mock_metadata)
    df = strategy.populate_exit_trend(df, mock_metadata)

    assert len(df) == len(flat_dataframe)
```

### Test: startup_candle_count is sufficient
```python
def test_startup_candle_count(strategy_class, ohlcv_dataframe, mock_metadata):
    """Verify startup_candle_count covers all indicator lookback periods."""
    strategy = strategy_class({})
    df = strategy.populate_indicators(ohlcv_dataframe.copy(), mock_metadata)

    # Check that no indicator columns have NaN beyond startup_candle_count
    indicator_cols = [c for c in df.columns if c not in ['date', 'open', 'high', 'low', 'close', 'volume']]
    for col in indicator_cols:
        non_nan_start = df[col].first_valid_index()
        if non_nan_start is not None:
            assert non_nan_start < strategy.startup_candle_count, \
                f"Indicator '{col}' has NaN at index {non_nan_start}, but startup_candle_count is {strategy.startup_candle_count}"
```

## Property-Based Tests (optional, for deeper validation)

```python
import hypothesis
from hypothesis import given, strategies as st

@given(st.floats(min_value=50, max_value=200))
def test_stoploss_negative(strategy_class, price):
    """Stoploss must always be negative."""
    strategy = strategy_class({})
    assert strategy.stoploss < 0

@given(st.integers(min_value=100, max_value=1000))
def test_dataframe_length_invariant(strategy_class, n, mock_metadata):
    """populate_indicators must preserve DataFrame length regardless of input size."""
    np.random.seed(42)
    dates = pd.date_range(start='2023-01-01', periods=n, freq='1h', tz=timezone.utc)
    df = pd.DataFrame({
        'date': dates,
        'open': np.random.uniform(90, 110, n),
        'high': np.random.uniform(100, 120, n),
        'low': np.random.uniform(80, 100, n),
        'close': np.random.uniform(90, 110, n),
        'volume': np.random.uniform(100, 10000, n),
    })
    df['high'] = df[['open', 'high', 'close']].max(axis=1)
    df['low'] = df[['open', 'low', 'close']].min(axis=1)

    strategy = strategy_class({})
    result = strategy.populate_indicators(df, mock_metadata)
    assert len(result) == n
```

## Usage Notes
- Replace `strategy_class` with a pytest fixture that imports the specific strategy
- Run with: `pytest tests/ -v --tb=short`
- For Freqtrade dry-run validation, use `freqtrade backtesting -s StrategyName --timerange 20230101-20230201`

## Known Issues
- Hypothesis tests add ~10s per test. Use sparingly.
- Mock DataProvider doesn't simulate real informative pair data — separate integration test needed.
- ohlcv_dataframe fixture uses seed 42 — deterministic but may not cover all edge cases.
