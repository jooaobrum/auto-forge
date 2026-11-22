# Example: error analysis of one iteration (binary)

The format is free (`error_analysis/<id>.json` or `.md`); what matters is covering what
[../error-analysis.md](../error-analysis.md) lists: confusion at the threshold, calibration per decile,
highest-confidence errors, breakdown by segment and by period, and a summary in sentences.

```python
import json, numpy as np, pandas as pd
from sklearn.metrics import average_precision_score

def error_analysis(valid, X_valid, X_train, y, s, thr, time_col, segments=(), top=10):
    v = valid.assign(_s=s, _period=pd.to_datetime(valid[time_col]).dt.to_period("W").astype(str))
    pred = (s >= thr).astype(int)
    conf = {"tp": int(((pred == 1) & (y == 1)).sum()), "fp": int(((pred == 1) & (y == 0)).sum()),
            "fn": int(((pred == 0) & (y == 1)).sum()), "tn": int(((pred == 0) & (y == 0)).sum()), "threshold": thr}
    dec = pd.qcut(pd.Series(s).rank(method="first"), 10, labels=False)
    calib = [{"decile": d + 1, "mean_score": float(s[dec == d].mean()), "rate": float(y[dec == d].mean())} for d in range(10)]
    mu, sd = X_train.mean(numeric_only=True), X_train.std(numeric_only=True).replace(0, np.nan)
    def dev(i):  # where the row departs most from training
        z = ((X_valid.iloc[i][mu.index] - mu) / sd).abs().dropna().sort_values(ascending=False).head(8)
        return {c: round(float(z[c]), 2) for c in z.index}
    order = np.argsort(-s)
    fps = [{"score": float(s[i]), "z": dev(i)} for i in order if y[i] == 0][:top]
    fns = [{"score": float(s[i]), "z": dev(i)} for i in order[::-1] if y[i] == 1][:top]
    seg = {c: {str(k): {"n": len(g), "rate": float(g[y.name].mean()),
                        "pr_auc": average_precision_score(g[y.name], g["_s"]) if g[y.name].nunique() == 2 else None}
               for k, g in v.groupby(c)} for c in list(segments) + ["_period"]}
    summary = []
    if conf["fn"] > 2 * max(conf["fp"], 1): summary.append("Too many FN: signal is missing for part of the positives")
    if conf["fp"] > 2 * max(conf["fn"], 1): summary.append("Too many FP: negatives that look positive")
    return {"confusion": conf, "calibration": calib, "false_positives": fps, "false_negatives": fns,
            "segments": seg, "summary": summary}
```
