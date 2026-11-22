# The Problem

Half of the bad models have a badly defined target. Before any model work, write `## Problem` in
`.specs/LAB.md` and have the user confirm it. `route.py problem` checks it; the modeling lane's
`validate_plan.py` reads it again (rule P4).

## 1. Look for the definition that already exists

Before asking, read:

- the comment and tags of the target table and column (on Databricks: `DESCRIBE TABLE EXTENDED <t>`,
  `information_schema.columns`);
- the lineage, when the platform keeps it: which table and job the label comes from;
- the query or job that writes the label column. The code is the real definition.

## 2. Ask what is missing, one question at a time

Each question comes with your recommended answer for the user to confirm or correct.

- **Event** (Target): what happened in the world for a row to be positive? Who decides it happened?
- **Rule** (Label rule): the exact condition on the source columns (values, thresholds, codes), and the
  window: within how long after the prediction does the event count?
- **Prediction time**: when does the model run, and what is known at that moment? Columns filled only
  after the event (status, reason, closing date, rework) are never features: name them in the Label rule.
- **Exclusions**: rows without an outcome yet, cancelled cases, tests, duplicates, odd periods.
- **Cost of FP** and **Cost of FN**: which costs more? Is capacity limited (how many cases can someone
  inspect)? This picks the metric and, later, the threshold.
- **Metric**: one of `pr_auc`, `roc_auc`, `f1`, `macro_f1`, `accuracy`, `log_loss`, `brier`, `rmse`, `mae`.
  Rare positives with limited capacity usually mean `pr_auc`.

## 3. Reproduce the label

Write the rule as SQL over the source, in a ```` ```sql ```` block of `## Problem`, and compare it with
the label column: the rows it covers and the rows where the two disagree. Save the result to the
**Label check** file, `{"rows": <n>, "mismatches": <n>}` (or a CSV with `rows` and `mismatches`). A
mismatch is a question for the user, never something to round away. Positives per month are a good second
look.

## 4. Confirm

Show the Problem and ask the user to confirm it. Write `**Confirmed**: <YYYY-MM-DD> - user: "<their words>"`
only with their words. Then run `route.py problem` until it exits 0:

| Exit | Meaning |
| --- | --- |
| 0 | the Problem is complete, confirmed and the label reproduces |
| 1 | a `FAIL` line names what is missing or wrong |
| 2 | no `.specs/LAB.md` or no `## Problem` |
