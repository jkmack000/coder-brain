# RULE-001: Import Whitelist
<!-- type: RULE -->
<!-- created: 2026-02-17 -->
<!-- tags: security, imports, whitelist, validation, strategy, python, guardrails -->
<!-- links: LEARN-002, CODE-001 -->

## Purpose
Defines the allowed imports for generated code. Whitelist-only approach — any import not listed here MUST be rejected. This is the primary security boundary for AI-generated strategy code.

## Strategy Files (STRICT)

Only these imports are allowed in IStrategy files:

```python
STRATEGY_ALLOWED_IMPORTS = {
    # Python stdlib (safe subset)
    "datetime",
    "typing",
    "dataclasses",
    "enum",
    "math",
    "functools",
    "collections",
    "itertools",
    "decimal",
    "logging",

    # Data manipulation
    "numpy",
    "pandas",

    # Technical indicators
    "talib",
    "talib.abstract",
    "technical",
    "technical.indicators",

    # Freqtrade
    "freqtrade.strategy",
    "freqtrade.vendor.qtpylib.indicators",
    "freqtrade.persistence",

    # Exchange (read-only usage in strategies)
    "ccxt",

    # Testing (only in test files, not in strategy files deployed to production)
    "pytest",
    "unittest.mock",
}
```

## BLOCKED in Strategy Files (never allow)

| Category | Modules | Why |
|----------|---------|-----|
| Network | `requests`, `urllib`, `http`, `socket`, `aiohttp` | No network calls from strategies |
| Filesystem write | `shutil`, `tempfile` | No file creation/deletion |
| Code execution | `exec`, `eval`, `compile`, `ast` | No dynamic code execution |
| Serialization | `pickle`, `shelve`, `marshal` | Deserialization attacks |
| System access | `subprocess`, `os.system`, `ctypes`, `sys` | No shell commands |
| Import manipulation | `importlib`, `__import__` | No dynamic imports |

## Non-Strategy Files (RELAXED)

Data pipeline scripts, test utilities, and infrastructure code may additionally use:

```python
NON_STRATEGY_ADDITIONAL = {
    # Filesystem (read + write)
    "pathlib",
    "json",
    "csv",
    "os",
    "os.path",
    "shutil",
    "glob",
    "io",

    # Data formats
    "yaml",
    "toml",

    # Logging
    "logging",

    # Testing
    "pytest",
    "unittest",
    "unittest.mock",
    "hypothesis",

    # Data pipeline
    "ccxt",
    "vectorbt",
    "optuna",

    # Freqtrade utilities
    "freqtrade.data",
    "freqtrade.configuration",
    "freqtrade.resolvers",
}
```

## Still BLOCKED in Non-Strategy Files

| Category | Modules | Why |
|----------|---------|-----|
| Network (direct) | `requests`, `urllib`, `http`, `socket` | Use ccxt for exchange access |
| Code execution | `exec`, `eval`, `compile` | Never |
| Serialization | `pickle`, `marshal` | Never |
| System commands | `subprocess`, `os.system` | Never |

## Validation Implementation

```python
import ast

def validate_imports(source_code: str, is_strategy: bool = True) -> list[str]:
    """Check all imports against whitelist. Returns list of violations."""
    allowed = STRATEGY_ALLOWED_IMPORTS if is_strategy else (STRATEGY_ALLOWED_IMPORTS | NON_STRATEGY_ADDITIONAL)
    violations = []

    tree = ast.parse(source_code)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name not in allowed:
                    violations.append(f"Blocked import: {alias.name}")
        elif isinstance(node, ast.ImportFrom):
            if node.module and node.module not in allowed:
                # Check if parent module is allowed
                parts = node.module.split('.')
                parent_allowed = any(
                    '.'.join(parts[:i+1]) in allowed
                    for i in range(len(parts))
                )
                if not parent_allowed:
                    violations.append(f"Blocked import: from {node.module}")

    return violations
```

## Rules

1. **Whitelist, never blacklist** — unknown imports are rejected by default
2. **Strategy files are strict** — no network, no filesystem, no exec, no pickle
3. **Non-strategy files are relaxed** — filesystem allowed, network only via ccxt
4. **Test imports only in test files** — pytest/hypothesis not in production strategy code
5. **When in doubt, reject** — user can explicitly approve if needed

## Known Issues
- `pandas-ta` not explicitly listed (uses `pandas_ta` module name). Add if needed.
- `ccxt` in strategy files is technically risky (could make API calls). Monitor usage — may restrict to non-strategy only.
- `freqtrade.persistence` allows DB access from strategies — intended for `Trade` object queries in callbacks.
