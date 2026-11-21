# The loop

The code is yours. One shape that works well, inherited from experimenta-ml: **one mutable file**
(`experiment.py` or a notebook) with the data preparation and the pipeline, and an **evaluator** that
you write once at the start of the round and never touch again. A fixed evaluator means fair
comparisons between iterations. If the problem asks for another layout, use it; the gate only looks at
the evidence ([patterns/iteration.md](patterns/iteration.md)).

## Evaluator principles (write once per round)

- Reads only train and valid (filter in the SQL by the lock windows), never the holdout.
- Computes features causally: the frame ordered by time, windows and aggregates only looking back.
  Everything that learns from data (imputer, scaler, encoder, selection, target encoding) is fitted on
  train, inside the pipeline.
- Trains on train, scores valid, keeps the valid scores per version (for the paired bootstrap).
- Runs the leakage checks ([patterns/leakage-checks.md](patterns/leakage-checks.md)).
- Writes the error analysis ([patterns/error-analysis-example.md](patterns/error-analysis-example.md)).
- Records the iteration in the round's `ledger.json` and in MLflow when the project logs to it.

Changing the evaluator in the middle of a round invalidates the comparisons: if you must, close the
round and open another.

## Search order (from experimenta-ml)

0. **Understand** - the `## Problem` in `.specs/LAB.md`, [eda.md](eda.md), the lessons that apply from
   the project's lesson store when it keeps one (agent-spec-lean keeps `.specs/lessons.json`), or none.
   Without these, do not start.
1. **Baseline** - numeric columns only, median imputation, StandardScaler, LogisticRegression
   (`class_weight="balanced"` if imbalanced) or Ridge for regression. It is the ruler; do not optimize.
2. **Cleaning** - constant columns, ids disguised as features, informative missingness (an indicator),
   categoricals, suspected leakage columns (the eda.md leakage suspects, and any column filled only
   after the event, which never becomes a feature).
3. **Domain features** - first the backlog ones that come from the EDA and the domain: group-relative
   (`x - batch_median`), temporal (time since, position in the sequence), ratios with a mechanism.
4. **Interactions** - only between variables that already showed signal; the domain prior decides which.
5. **Model** - LightGBM/XGBoost with sensible defaults when the features stopped paying off in the
   linear model.
6. **Hyperparameters** - only at the end, few iterations, on the best recipe.

Do not jump to hyperparameters before features. Do not swap the model before cleaning.

## Rhythm of one iteration

1. Read the round's `ledger.json` (what was tried, the current best) and the error analysis of the best
   and of the last one.
2. Write in one sentence: the error pattern, the change, and why it should attack that pattern.
3. If the idea is new and not trivial, test it first in the EDA, on train (a `groupby` against the
   target): cheap.
4. Start from the best's code, apply **one** change, run the evaluator.
5. Decide by the rule (min gain + CI); rejected or infeasible - go back to the best's code.
6. Record it in the ledger, even the rejected ones: they become lessons.

## When to stop the round

- The budget is spent.
- Three rejected iterations in a row in the same direction: the direction is over; change family or close.
- The backlog is empty and the error analysis suggests nothing new with a mechanism.

Close with `round_report.py <slug>`, write the report, run `validate_round.py <slug>` (add `--offline`
when the project does not log to MLflow, and say so in the report) and move on to Verify.
