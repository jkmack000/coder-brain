# LEARN-009: Optuna Hyperparameter Optimization Reference
<!-- type: LEARN -->
<!-- created: 2026-02-18 -->
<!-- tags: optuna, hyperparameter, optimization, bayesian, TPE, pruning, freqtrade, trading -->
<!-- links: LEARN-001, LEARN-006, SPEC-001, RULE-003 -->

## Context
Optuna is the optimization engine behind Freqtrade's hyperopt. This reference covers standalone usage (more control than Freqtrade CLI) and Freqtrade integration. Current version: v4.7.0+.

## 1. Core Concepts

### Study, Trial, Objective
```python
import optuna

def objective(trial: optuna.Trial) -> float:
    ema_short = trial.suggest_int("ema_short", 5, 50)
    ema_long = trial.suggest_int("ema_long", 50, 200)
    stop_loss = trial.suggest_float("stop_loss", 0.01, 0.10, step=0.005)
    profit = run_backtest(ema_short, ema_long, stop_loss)
    return profit

# Single-objective
study = optuna.create_study(
    study_name="trading_strategy_v1",
    direction="maximize",              # or "minimize"
    storage="sqlite:///optuna.db",     # optional persistence
    load_if_exists=True,               # resume previous study
    sampler=optuna.samplers.TPESampler(seed=42),
    pruner=optuna.pruners.MedianPruner(),
)

# Multi-objective
study = optuna.create_study(
    directions=["maximize", "minimize"],  # e.g., [profit, drawdown]
)
study.set_metric_names(["profit_factor", "max_drawdown"])
```

### study.optimize() Signature
```python
study.optimize(
    func,                    # objective function
    n_trials=None,           # max trials (None = unlimited)
    timeout=None,            # max seconds
    n_jobs=1,                # parallel trials (-1 = all CPUs)
    callbacks=None,          # list of callables(Study, FrozenTrial)
    gc_after_trial=False,
    show_progress_bar=False,
    catch=(Exception,),      # exception types to catch (trial marked FAIL)
)
```

### Accessing Results
```python
# Single-objective
best = study.best_trial
print(best.value)           # best objective value
print(best.params)          # dict of best params

# Multi-objective (Pareto front)
for trial in study.best_trials:
    print(trial.values, trial.params)

# All trials as DataFrame
df = study.trials_dataframe()
```

## 2. Trial Suggest API

### suggest_int
```python
trial.suggest_int(name, low, high, *, step=1, log=False) -> int

n_layers = trial.suggest_int("n_layers", 1, 5)
n_units = trial.suggest_int("n_units", 16, 256, step=16)       # 16, 32, 48...
n_channels = trial.suggest_int("n_channels", 32, 512, log=True) # log-scale
```

### suggest_float
```python
trial.suggest_float(name, low, high, *, step=None, log=False) -> float

lr = trial.suggest_float("lr", 1e-5, 1e-1, log=True)
dropout = trial.suggest_float("dropout", 0.0, 0.5)
threshold = trial.suggest_float("threshold", 0.0, 1.0, step=0.05)
```

### suggest_categorical
```python
trial.suggest_categorical(name, choices) -> value

optimizer = trial.suggest_categorical("optimizer", ["adam", "sgd", "rmsprop"])
use_feature = trial.suggest_categorical("use_volume", [True, False])
```

### Conditional Parameters
```python
def objective(trial):
    classifier = trial.suggest_categorical("classifier", ["svm", "rf"])
    if classifier == "svm":
        svc_c = trial.suggest_float("svc_c", 1e-10, 1e10, log=True)
    else:
        max_depth = trial.suggest_int("rf_max_depth", 2, 32, log=True)
```

### Enqueuing Specific Trials
```python
study.enqueue_trial({"ema_short": 12, "ema_long": 26, "stop_loss": 0.05})
study.optimize(objective, n_trials=200)  # includes enqueued + new
```

## 3. Samplers

| Sampler | Algorithm | Best For |
|---------|-----------|----------|
| `TPESampler` | Tree-structured Parzen Estimator | **Default.** General-purpose, handles categorical + conditional |
| `CmaEsSampler` | CMA-ES (evolutionary) | Continuous numerical spaces, 5-50 dims. **No categorical.** |
| `GPSampler` | Gaussian Process | Small spaces, expensive objectives. Scales poorly O(n^3) |
| `RandomSampler` | Uniform random | Baselines, debugging |
| `GridSampler` | Exhaustive grid | Small discrete spaces, final fine-tuning |
| `NSGAIISampler` | NSGA-II (genetic) | Multi-objective optimization |
| `NSGAIIISampler` | NSGA-III (genetic) | Multi-objective, 3+ objectives. **Freqtrade's default.** |
| `AutoSampler` | Automatic selection | When unsure |

### Key Sampler Construction
```python
sampler = optuna.samplers.TPESampler(
    seed=42,
    n_startup_trials=10,     # random trials before Bayesian kicks in
    multivariate=True,       # model parameter correlations
    constant_liar=True,      # for parallel optimization
)
```

## 4. Pruners

Pruners terminate unpromising trials early by monitoring intermediate values.

```python
def objective(trial):
    params = {...}
    for epoch in range(100):
        score = train_one_epoch(params, epoch)
        trial.report(score, step=epoch)
        if trial.should_prune():
            raise optuna.TrialPruned()
    return final_score
```

For trading backtests, "steps" could be walk-forward windows or monthly periods.

| Pruner | Algorithm | Key Parameters |
|--------|-----------|----------------|
| `MedianPruner` | Prunes if worse than median at same step | `n_startup_trials=5`, `n_warmup_steps=0` |
| `SuccessiveHalvingPruner` | Keeps top fraction | `min_resource`, `reduction_factor=3` |
| `HyperbandPruner` | Multiple SHA brackets | `min_resource`, `max_resource`, `reduction_factor=3` |
| `ThresholdPruner` | Fixed threshold cutoff | `lower`, `upper`, `n_warmup_steps` |
| `PatientPruner` | Wraps another pruner with patience | `wrapped_pruner`, `patience=1` |

**Recommended default:**
```python
pruner = optuna.pruners.MedianPruner(
    n_startup_trials=5,    # build baseline before pruning
    n_warmup_steps=10,     # avoid pruning on noisy early iterations
)
```

## 5. Storage

| Storage | Use Case | Parallel Safe |
|---------|----------|---------------|
| In-memory (default) | Quick experiments | No |
| `sqlite:///path.db` | Persistence, resume | **No** (locks under concurrency) |
| `postgresql://...` | Production parallel | **Yes** |
| `JournalFileBackend` | NFS-based parallel (no DB) | **Yes** |

```python
# SQLite (single-process)
study = optuna.create_study(storage="sqlite:///optuna.db", study_name="v1", load_if_exists=True)

# Journal storage (parallel, no DB needed)
from optuna.storages import JournalStorage, JournalFileBackend
storage = JournalStorage(JournalFileBackend("./optuna_journal.log"))
study = optuna.create_study(storage=storage, study_name="v1")
```

## 6. Visualization

```python
import optuna.visualization as vis

vis.plot_optimization_history(study)       # progress over time
vis.plot_param_importances(study)          # which params matter (needs sklearn)
vis.plot_contour(study, params=["a","b"])  # 2D contour of interactions
vis.plot_slice(study)                      # each param vs objective
vis.plot_parallel_coordinate(study)        # all params + objective
vis.plot_pareto_front(study, target_names=["profit", "drawdown"])  # multi-obj
```

## 7. Integration with Freqtrade

Freqtrade's hyperopt uses Optuna under the hood. Default sampler: `NSGAIIISampler`.

### CLI
```bash
freqtrade hyperopt --config config.json --strategy MyStrategy \
    --hyperopt-loss SharpeHyperOptLossDaily \
    --spaces buy sell roi stoploss trailing \
    --epochs 500 -j 4
```

### Loss Functions
`SharpeHyperOptLoss`, `SharpeHyperOptLossDaily`, `SortinoHyperOptLoss`, `SortinoHyperOptLossDaily`, `MaxDrawDownHyperOptLoss`, `CalmarHyperOptLoss`, `ProfitDrawDownHyperOptLoss`

### Strategy Parameters
```python
from freqtrade.strategy import IStrategy, IntParameter, DecimalParameter, CategoricalParameter, BooleanParameter

class MyStrategy(IStrategy):
    buy_ema_short = IntParameter(3, 50, default=5, space="buy", optimize=True)
    buy_rsi = DecimalParameter(20.0, 40.0, default=30.0, decimals=1, space="buy")
    use_volume = BooleanParameter(default=True, space="buy")
    # IMPORTANT: Cannot use hyperoptable params in populate_indicators()
```

### Standalone Optuna vs Freqtrade Hyperopt
| Feature | Freqtrade Hyperopt | Standalone Optuna |
|---------|-------------------|-------------------|
| Setup | Low (CLI flags) | High (write objective + backtest) |
| Search space | Strategy params only | Arbitrary |
| Pruning | Not built-in | Full support |
| Storage/resume | In development | Full (SQLite, PostgreSQL) |
| Visualization | Basic table output | Full suite |

**Recommendation:** Freqtrade hyperopt for quick sweeps. Standalone Optuna for pruning, custom spaces, walk-forward, or production persistence.

## 8. Best Practices

- **Trial count heuristic:** 10x params minimum, 100x for thorough. Diminishing returns after 500-1000 for TPE.
- **Timeout as safety:** `study.optimize(objective, n_trials=500, timeout=7200)`
- **Multi-objective:** Use `directions=["maximize", "minimize"]`, access `study.best_trials` for Pareto front
- **Overfitting (#1 trading risk):** Optimize on out-of-sample via walk-forward. Prefer Sharpe/Sortino over raw profit.

## 9. Common Pitfalls

- **Search space too wide:** Wastes trials on extremes. Narrow with domain knowledge.
- **step/log conflict:** Mutually exclusive. Using both raises an error.
- **Reproducibility:** Set `seed` on sampler. Parallel breaks reproducibility.
- **Trial failures:** Caught by default, stored as FAIL, still consume trial count.
- **SQLite concurrency:** Does NOT work for parallel — use PostgreSQL or JournalStorage.
- **Inconsistent spaces:** Changing bounds mid-study confuses the sampler.

## Known Issues
- Freqtrade hyperopt doesn't expose pruning (standalone Optuna needed for that)
- Walk-forward optimization requires custom objective (not built into either)
