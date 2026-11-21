# Pattern: one hill-climbing iteration

The code is yours (notebook, script, Job, whatever is fastest). What `validate_round.py` checks is the
evidence each iteration leaves:

1. **One change, with a name:** `hypothesis` starts with `baseline`, `H<n>` (from the backlog) or
   `EA-it<NN>` (from a finding in the error analysis of iteration NN).
2. **Recoverable code:** a snapshot in `experiments/<id>.py` (or `.ipynb`) or the commit in `code`.
3. **The leakage checks** run and reported in `checks` (see [leakage-checks.md](leakage-checks.md)):
   `CHK-LEAK-003` (causality), `CHK-DUP-001` (duplicates) and, on a binary target, `CHK-LEAK-001`.
   Any one failing - `status: infeasible`.
4. **The metric on valid** (`value`) and, from the second kept iteration on, the comparison with the
   current best **on the same rows**, with a CI (`delta`, `ci`).
5. **The decision by the rule:** `kept` only if `delta >= Min gain` and `ci[0] > 0`; otherwise
   `rejected`, and the code goes back to the best.
6. **The error analysis** in `error_analysis/<id>.json` or `.md` ([error-analysis.md](../error-analysis.md)).
7. **The MLflow run** in `mlflow_run_id`, with the tags `round` (the slug), `iteration`, `hypothesis`,
   `stage=iteration`. When the project does not log to MLflow, run `validate_round.py <slug> --offline`
   and say so in the report.

All of it lives in the round folder `.specs/features/<slug>/` (`experiments/<id>.*`,
`error_analysis/<id>.*`, `ledger.json`).

## ledger.json format

```json
{
  "round": "<slug>",
  "best": "dfdee50fa862a2c3",
  "entries": [
    {"iteration": 0, "id": "a1b2c3d4", "hypothesis": "baseline", "status": "kept",
     "metric": "pr_auc", "value": 0.108, "delta": null, "ci": null,
     "checks": {"CHK-LEAK-003": {"ok": true, "detail": "causal on 1100 rows"},
                "CHK-LEAK-001": {"ok": true, "detail": "max univariate AUC 0.71"},
                "CHK-DUP-001": {"ok": true, "detail": "0 duplicates"}},
     "mlflow_run_id": "...", "reason": "baseline"}
  ]
}
```

`status` is `kept`, `rejected`, `infeasible` or `failed`; a failed or infeasible entry carries
`error_summary`. `code` points at the snapshot or commit. The top-level `round` key holds the slug.
`id` is any stable identifier of the version (file hash, short commit sha).

## Example: paired bootstrap and the keep rule

```python
import numpy as np
from sklearn.metrics import average_precision_score as ap

def paired_bootstrap(y, new, old, score=ap, higher_is_better=True, n_boot=1000, seed=0):
    y, new, old = map(np.asarray, (y, new, old))
    sign = 1 if higher_is_better else -1
    rng = np.random.default_rng(seed)
    pos, neg = np.flatnonzero(y == 1), np.flatnonzero(y == 0)   # stratified: every replica has positives
    deltas = []
    for _ in range(n_boot):
        i = np.concatenate([rng.choice(pos, len(pos)), rng.choice(neg, len(neg))])
        deltas.append(sign * (score(y[i], new[i]) - score(y[i], old[i])))
    lo, hi = np.percentile(deltas, [2.5, 97.5])
    return sign * (score(y, new) - score(y, old)), (lo, hi)

delta, (lo, hi) = paired_bootstrap(y_valid, s_new, s_best)
kept = delta >= MIN_GAIN and lo > 0
```

Keep each version's valid scores (e.g. `scores/<id>.npy`) to compare the next one with the best.
