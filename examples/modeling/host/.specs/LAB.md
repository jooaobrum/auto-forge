# LAB

**Eval command**: `python -m secom.evaluate --round {slug}`
**Results glue**: none needed

## Problem

**Target**: a lot fails when the final functional test of the line rejects it; a failure costs rework of the whole lot
**Label rule**: `label = 1` when the final test result is fail (-1 in the source), `0` when pass; no other source counts
**Prediction time**: right after the lot's last sensor measurement, before the final test
**Exclusions**: lots with no final test result yet (still in process) stay out of training and evaluation
**Cost of FP**: an inspection of a lot that would pass
**Cost of FN**: a failed lot reworked in full
**Metric**: pr_auc
**Label check**: `.specs/label_check.json`
**Confirmed**: 2026-11-18 - user: "that's it, failure = rejected at the final functional test"

```sql
SELECT count(*) AS rows, sum(CASE WHEN (result = -1) = (label = 1) THEN 0 ELSE 1 END) AS mismatches
FROM workspace.curated.secom
```
