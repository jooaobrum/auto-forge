# Pattern: leakage checks (examples to adapt)

Ids and meaning in [../check_catalog.json](../check_catalog.json). Each iteration reports the result in
the round's `ledger.json` (`checks.<id>.ok` and `detail`). How is yours; below, one way that works.

## CHK-LEAK-003 - causal features

Compute the features with train only and with train+valid; the training rows must not change.

```python
import numpy as np

def causality_check(prepare, dev, id_col, time_col):
    train = dev[dev.split == "train"]
    a = prepare(train.sort_values(time_col)).set_index(id_col)
    b = prepare(dev.sort_values(time_col)).set_index(id_col)
    ids = a.index.intersection(b.index)
    changed = [c for c in a.columns.intersection(b.columns)
               if a[c].dtype.kind in "if" and not np.allclose(a.loc[ids, c], b.loc[ids, c], equal_nan=True)]
    return {"ok": not changed, "detail": f"change with future rows: {changed}" if changed else "causal"}
```

## CHK-LEAK-001 - a variable that separates the target on its own (binary)

```python
from sklearn.metrics import roc_auc_score

def univariate_leak(df, label, features, threshold=0.98):
    aucs = {}
    for f in features:
        m = df[f].notna()
        if df.loc[m, label].nunique() == 2 and df.loc[m, f].nunique() > 1:
            a = roc_auc_score(df.loc[m, label], df.loc[m, f]); aucs[f] = max(a, 1 - a)
    leaks = {f: a for f, a in aucs.items() if a >= threshold}
    return {"ok": not leaks, "detail": f"leakage: {leaks}" if leaks else f"max AUC {max(aucs.values(), default=0.5):.3f}"}
```

## CHK-DUP-001 - the same vector in train and valid

```python
import pandas as pd

def cross_split_duplicates(X, split):
    key = pd.util.hash_pandas_object(X.round(6), index=False)
    shared = pd.DataFrame({"k": key.values, "s": split.values}).groupby("k")["s"].nunique().gt(1).sum()
    return {"ok": shared == 0, "detail": f"{shared} vectors in more than one split"}
```

## CHK-OOT-001 - the code does not cite the holdout

`validate_round.py` looks for `oot`, `out of time` and the OOT window dates from the lock in `src/`,
`notebooks/` and the round's `experiments/` (and in the paths you pass with `--code`). A reference to
the holdout outside Verify fails the round. Verification code lives in `verify/`.

## Verify mutations (CHK-MUT-001/002)

```python
def shuffled_target(fit_predict, train, oot, label, score, chance, repeats=10, tol=0.05, seed=0):
    rng = np.random.default_rng(seed)
    vals = []
    for _ in range(repeats):
        t = train.copy(); t[label] = rng.permutation(t[label].values)
        vals.append(score(oot[label], fit_predict(t)(oot)))
    med = float(np.median(vals))          # the median: a random model can align with a strong feature
    return {"killed": abs(med - chance) <= tol, "value": med, "chance": chance}

def future_column(dev, label, features):
    d = dev.assign(__future=dev[label] + np.random.default_rng(0).normal(0, 0.01, len(dev)))
    return {"killed": not univariate_leak(d, label, features + ["__future"])["ok"]}
```

`chance` is the prevalence for PR-AUC and 0.5 for ROC-AUC.
