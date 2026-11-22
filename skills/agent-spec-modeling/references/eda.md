# EDA: explore before modeling

You are a creative copilot: you propose questions, test fast, show what you found and ask the user what
they see. The output is `.specs/features/<slug>/eda.md`, which feeds the backlog ([ideas.md](ideas.md)).
Measure what really relates to the target (per variable, per period, per group, informative missingness),
on train only.

## Before

- The `## Problem` of `.specs/LAB.md` is confirmed and the split is decided in `.specs/split.lock`
  (default in [patterns/split.md](patterns/split.md)).
- The EDA uses **train only** (the lock's window). Valid decides the iterations, OOT belongs to Verify.
  Exploring valid and then choosing features by it is selection leakage.
- Know the assets: column comments and tags in the catalog, the project's lessons when its lesson store
  keeps some (agent-spec-lean keeps `.specs/lessons.json`). Each table has its traps; a feature table is a
  pipeline, and agent-spec-pipeline proves it. For platform access, use the platform skill `.specs/LAB.md`
  lists (for example data-databricks-sql).

## 1. Signal panorama (cheap, first)

Start with a sweep of every column against the target, on train. On Databricks, run it as SQL in Spark so
only aggregates come back. A ready example to adapt is
[patterns/target_signal_example.py](patterns/target_signal_example.py) (correlation, missingness,
stability by month, group-relative, rate per level). Adapt it to the table: what matters is to cover, for
each train column:
- numeric: correlation with the target, % missing, target rate when missing vs present,
  stability of the correlation by month;
- categorical (<= 50 levels): target rate per level, with the count;
- warning signs: correlation |r| > 0.9 (leakage suspect, check it against the Exclusions and Label rule in
  the `## Problem` of `.specs/LAB.md`), constant columns, disguised ids.

## 2. Questions (creative, with the user)

From the panorama, raise questions and test each with a query on train:
- **Groups:** is the abnormal absolute or relative to the group (batch, machine, customer)? Compare the
  raw variable with `x - group_median` against the target.
- **Time:** does the relation change by period? Is there drift, a process change, seasonality?
- **Missingness:** do rows with a missing value have more or fewer events? Why (sensor off, step skipped)?
- **Concentration:** are the positives concentrated in a segment, shift, equipment?
- **Non-linearity:** is the target rate per quintile of the variable monotonic? Is there a threshold?
- **Domain priors:** what the expert thinks matters - does it confirm or not?
- **Ordering:** sorting by time within the group, does a pattern show (sequence, time since)?

Use the idea catalog ([recipes/feature-ideas.md](recipes/feature-ideas.md)) to provoke questions, not as a
checklist. Show the user the surprising findings and ask whether they make sense for the business.

## 3. eda.md

Open with `## Signal panorama` (the table of the columns most associated with the target) and add:

```markdown
## Findings
- <finding> - <evidence: query, number> - <what it suggests>

## Questions
- <open question for the user or for the next analysis>

## Candidate features
- <feature> - <mechanism> - <evidence> - <causal? does it exist at prediction time?>

## Leakage suspects
- <column> - <why it is suspect> - <decision: DROP | investigate>
```

Every finding has a number that supports it. A finding without evidence is a question.
