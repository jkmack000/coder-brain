# LEARN-010: pytest Advanced Patterns Reference
<!-- type: LEARN -->
<!-- created: 2026-02-18 -->
<!-- tags: pytest, testing, fixtures, parametrize, mocking, hypothesis, property-testing, benchmark, dataframe -->
<!-- links: CODE-002, RULE-003, SPEC-001 -->

## Context
Advanced pytest patterns for the Coder brain's testing pipeline. Extends CODE-002 (basic test scaffolding) with fixtures, parametrize, mocking, property-based testing, and DataFrame-specific patterns.

## 1. Fixtures

### Scope
```python
import pytest

@pytest.fixture(scope="function")   # DEFAULT — per test
def db_connection():
    conn = create_connection()
    yield conn
    conn.close()

@pytest.fixture(scope="module")     # shared within a .py file
@pytest.fixture(scope="session")    # shared across entire test run
```

### Autouse
```python
@pytest.fixture(autouse=True)
def reset_database(db):
    db.rollback()
    yield
    db.rollback()
```

### Parametrized Fixtures
```python
@pytest.fixture(params=["sqlite", "postgresql", "mysql"])
def db_engine(request):
    engine = create_engine(request.param)
    yield engine
    engine.dispose()

# Every test requesting db_engine runs 3 times
def test_query(db_engine):
    assert db_engine.execute("SELECT 1")
```

### Fixture Factories
```python
@pytest.fixture
def make_trade():
    """Factory fixture — returns a callable that creates Trade objects."""
    created = []
    def _make_trade(symbol="BTC/USDT", amount=1.0, side="buy", **kwargs):
        trade = Trade(symbol=symbol, amount=amount, side=side, **kwargs)
        created.append(trade)
        return trade
    yield _make_trade
    for t in created:
        t.cleanup()

def test_multiple_trades(make_trade):
    t1 = make_trade("ETH/USDT", amount=2.0)
    t2 = make_trade("BTC/USDT", amount=0.5, side="sell")
    assert t1.symbol != t2.symbol
```

## 2. Parametrize

### Basic Syntax
```python
@pytest.mark.parametrize("input,expected", [
    (1, 2),
    (2, 4),
    (3, 6),
])
def test_double(input, expected):
    assert input * 2 == expected
```

### With IDs
```python
@pytest.mark.parametrize("x,y,expected", [
    pytest.param(2, 3, 5, id="positive"),
    pytest.param(-1, 1, 0, id="zero-sum"),
    pytest.param(0, 0, 0, id="zeros"),
])
def test_add(x, y, expected):
    assert x + y == expected
```

### Stacking for Combinations
```python
@pytest.mark.parametrize("x", [1, 2])
@pytest.mark.parametrize("y", [10, 20])
def test_product(x, y):
    # Runs 4 tests: (1,10), (1,20), (2,10), (2,20)
    assert x * y > 0
```

### Indirect Parametrize (Pass to Fixture)
```python
@pytest.fixture
def db(request):
    return create_engine(request.param)

@pytest.mark.parametrize("db", ["sqlite", "postgresql"], indirect=True)
def test_query(db):
    assert db.execute("SELECT 1")
```

## 3. Mocking

### monkeypatch (pytest built-in)
```python
def test_api_call(monkeypatch):
    monkeypatch.setattr("mymodule.requests.get", lambda url: MockResponse(200))
    monkeypatch.setenv("API_KEY", "test-key-123")
    monkeypatch.delattr("mymodule.dangerous_function")
    monkeypatch.setitem(config, "debug", True)
```

### unittest.mock
```python
from unittest.mock import MagicMock, patch

# MagicMock
mock_api = MagicMock()
mock_api.get_price.return_value = 50000.0
mock_api.get_price("BTC")  # returns 50000.0
mock_api.get_price.assert_called_once_with("BTC")

# spec — restricts mock to real object's interface
mock_api = MagicMock(spec=ExchangeAPI)
mock_api.nonexistent_method()  # raises AttributeError

# side_effect — dynamic returns or exceptions
mock_api.get_price.side_effect = [50000, 51000, ConnectionError("timeout")]

# side_effect as function
mock_api.get_price.side_effect = lambda sym: {"BTC": 50000, "ETH": 3000}[sym]

# patch as decorator
@patch("mymodule.ExchangeAPI")
def test_trading(MockAPI):
    MockAPI.return_value.get_price.return_value = 50000
    result = my_trading_function()
    assert result.action == "buy"
```

### When to Use Which
| Feature | monkeypatch | unittest.mock |
|---------|------------|---------------|
| Call tracking | No | Yes (assert_called_*, call_count) |
| Return values | Manual | `.return_value`, `.side_effect` |
| Spec enforcement | No | Yes (`spec=RealClass`) |
| Env vars | `setenv` / `delenv` | No |
| Best for | Simple replacements, env/config | Complex mocking with verification |

## 4. Markers

### Built-in
```python
@pytest.mark.skip(reason="Not implemented yet")
@pytest.mark.skipif(sys.platform == "win32", reason="Unix only")
@pytest.mark.xfail(reason="Known bug #123", strict=True)
```

### Custom Markers
Register in `pyproject.toml`:
```toml
[tool.pytest.ini_options]
markers = [
    "slow: marks tests as slow",
    "integration: integration tests",
    "backtest: backtesting tests",
]
```

### Filtering
```bash
pytest -m "slow"              # only slow tests
pytest -m "not slow"          # skip slow tests
pytest -m "integration and not backtest"
```

## 5. Conftest Patterns

### Hierarchy
```
tests/
  conftest.py          # session-scoped fixtures, shared utilities
  unit/
    conftest.py        # unit-test-specific fixtures
  integration/
    conftest.py        # DB connections, etc.
```

Fixtures search **upward** through conftest hierarchy.

### Plugin Hooks
```python
# conftest.py
def pytest_addoption(parser):
    parser.addoption("--exchange", default="binance", help="Exchange to test against")

@pytest.fixture
def exchange(request):
    return request.config.getoption("--exchange")
```

## 6. Property-Based Testing with Hypothesis

### Basic Usage
```python
from hypothesis import given, settings, example, assume
from hypothesis import strategies as st

@given(st.integers(), st.integers())
def test_addition_commutative(a, b):
    assert a + b == b + a

@given(st.floats(min_value=-1e6, max_value=1e6, allow_nan=False, allow_infinity=False))
def test_abs_non_negative(x):
    assert abs(x) >= 0
```

### Core Strategies
```python
st.integers(min_value=0, max_value=100)
st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False)
st.booleans()
st.lists(st.integers(), min_size=1, max_size=20)
st.sampled_from(["BTC", "ETH", "SOL"])
st.one_of(st.integers(), st.text())
```

### DataFrames (hypothesis.extra.pandas)
```python
from hypothesis.extra.pandas import column, data_frames, range_indexes

ohlcv_strategy = data_frames(
    index=range_indexes(min_size=10, max_size=100),
    columns=[
        column("open", dtype=float, elements=st.floats(1.0, 100000.0, allow_nan=False)),
        column("high", dtype=float, elements=st.floats(1.0, 100000.0, allow_nan=False)),
        column("low", dtype=float, elements=st.floats(1.0, 100000.0, allow_nan=False)),
        column("close", dtype=float, elements=st.floats(1.0, 100000.0, allow_nan=False)),
        column("volume", dtype=float, elements=st.floats(0.0, 1e9, allow_nan=False)),
    ],
)

@given(ohlcv_strategy)
def test_indicator_no_crash(df):
    assume((df["high"] >= df["low"]).all())
    result = calculate_indicator(df)
    assert len(result) == len(df)
```

### Settings
```python
@settings(max_examples=500, deadline=5000)
@example(a=0, b=0)  # always test this specific case
@given(st.integers(), st.integers())
def test_with_settings(a, b):
    assert a + b == b + a
```

## 7. Performance Testing (pytest-benchmark)

```python
def test_strategy_performance(benchmark):
    result = benchmark(calculate_signals, dataframe)
    assert result is not None

# Pedantic mode
def test_precise_benchmark(benchmark):
    def setup():
        return (load_large_dataframe(),), {}
    result = benchmark.pedantic(calculate_signals, setup=setup, rounds=100, warmup_rounds=5)
```

```bash
pytest --benchmark-min-rounds=10
pytest --benchmark-disable          # skip benchmarks
pytest --benchmark-save=baseline    # save results
pytest --benchmark-compare=baseline # compare
```

## 8. Testing Patterns for Data Pipelines

### DataFrame Assertions
```python
def test_ohlcv_schema(ohlcv_df):
    required = ["open", "high", "low", "close", "volume"]
    assert all(col in ohlcv_df.columns for col in required)
    assert ohlcv_df["open"].dtype == np.float64
    assert not ohlcv_df.duplicated().any()
    assert (ohlcv_df["high"] >= ohlcv_df["low"]).all()
```

### pytest.approx for Floating-Point
```python
assert 0.1 + 0.2 == pytest.approx(0.3)
assert result == pytest.approx(expected, rel=1e-3)   # relative
assert result == pytest.approx(expected, abs=1e-6)    # absolute
assert [1.0, float("nan")] == pytest.approx([1.0, float("nan")], nan_ok=True)
# Default tolerances: rel=1e-6, abs=1e-12
```

### DataFrame Comparison
```python
pd.testing.assert_frame_equal(result[["ema_12"]], expected[["ema_12"]], atol=1e-6)

# Or column-by-column
assert result["ema_12"].tolist() == pytest.approx(expected["ema_12"].tolist(), rel=1e-5, nan_ok=True)
```

### NaN Handling
```python
def test_nan_propagation(sample_df):
    result = calculate_sma(sample_df, period=20)
    assert result["sma_20"][:19].isna().all()   # First 19 = NaN
    assert result["sma_20"][19:].notna().all()   # Rest = valid
```

### Fixture Pattern for DataFrames
```python
@pytest.fixture
def sample_ohlcv():
    return pd.DataFrame({
        "open":   [100.0, 101.0, 99.0, 102.0, 98.0],
        "high":   [102.0, 103.0, 101.0, 104.0, 100.0],
        "low":    [99.0, 100.0, 98.0, 101.0, 97.0],
        "close":  [101.0, 99.0, 100.0, 103.0, 99.0],
        "volume": [1000, 1200, 800, 1500, 900],
    }, index=pd.date_range("2024-01-01", periods=5, freq="1h"))
```

## Known Issues
- Hypothesis adds ~10s per test with DataFrame strategies
- pytest-benchmark and Hypothesis don't compose well (benchmark measures Hypothesis overhead)
- `hypothesis.extra.pandas` doesn't enforce OHLC constraints (high >= low) — use `assume()`
