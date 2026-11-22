# Pattern: time split with a locked holdout

What must be true (the gate checks `.specs/split.lock`, not your code):

- Three windows by time: **train**, **valid** (decides the iterations) and **OOT** (only Verify reads it).
- `train` ends before `valid` starts; `valid` ends before `OOT` starts.
- A day (or the problem's time grain) never sits in two windows.
- Groups that cannot cross (batch, customer) stay whole in one window, if the problem asks for it.
- The decision is written once to `.specs/split.lock` and does not change in the round. Changing it is
  a decision recorded in `.specs/STATE.md` and a new round.

## split.lock format (the gate reads these fields)

```json
{
  "version": 1,
  "table": "workspace.curated.secom",
  "time_col": "timestamp", "id_col": "id", "label_col": "label", "group_col": null,
  "windows": {"train": ["2008-07-19", "2008-09-15"], "valid": ["2008-09-16", "2008-09-30"], "oot": ["2008-10-01", "2008-10-17"]},
  "counts": {"train": 1100, "valid": 230, "oot": 237},
  "positives": {"train": 70, "valid": 17, "oot": 17}
}
```

## Example (adapt; it lives in the project's code)

Windows by row fraction, without cutting a day in half, computed by aggregate in Spark (only the count
per day leaves the cluster):

```python
import pandas as pd

def windows_from_day_counts(counts: pd.Series, valid_frac=0.15, oot_frac=0.15) -> dict:
    counts = counts.sort_index()
    cum = counts.cumsum() / counts.sum()
    tr = cum.index[cum <= 1 - valid_frac - oot_frac]
    va = cum.index[(cum > 1 - valid_frac - oot_frac) & (cum <= 1 - oot_frac)]
    oo = cum.index[cum > 1 - oot_frac]
    day = lambda d: pd.Timestamp(d).date().isoformat()
    return {"train": [day(tr.min()), day(tr.max())], "valid": [day(va.min()), day(va.max())],
            "oot": [day(oo.min()), day(oo.max())]}

days = spark.sql(f"SELECT to_date({t}) AS day, count(*) AS n FROM {table} GROUP BY 1").toPandas()
windows = windows_from_day_counts(days.set_index("day")["n"])
```

To read only what the iteration may see, filter in the SQL, so the OOT rows never leave the cluster:

```python
w = lock["windows"]
dev = spark.sql(f"""SELECT * FROM {lock['table']}
  WHERE to_date({t}) BETWEEN '{w['train'][0]}' AND '{w['valid'][1]}'""").toPandas()
```
