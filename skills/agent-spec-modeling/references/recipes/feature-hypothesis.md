---
name: feature-hypothesis
profile: tabular
status: experimental
---

# feature-hypothesis

## When to use
A new variable (or family: group aggregates, per-entity normalization, counts, ratios) that should move the target through a mechanism you can state in one sentence.

## Typical hypotheses
- Group aggregate (sensor mean in the batch, deviation per machine) with a window that ends before the event.
- Per-entity normalization: value minus the entity's own historical mean.
- Count of missing values or alarms per row, when absence is informative.
- Interaction with a known mechanism (temperature x pressure).

## Probe and budget
Gain from adding the variable to a **fixed baseline** (same model, same hyperparameters), with temporal validation: train on train, metric on valid, and the metric per valid period to see stability. One probe per hypothesis; variable families count as one.
Typical budget: 1 probe per hypothesis, up to 6 per round.

## Required checks
- `CHK-LEAK-001` - No variable with univariate AUC >= 0.98 in train or valid
- `CHK-LEAK-002` - Every variable exists at prediction time
- `CHK-GAIN-001` - Minimum gain over the baseline on valid

## Traps
- A variable computed with data after the event (a window that includes the event itself).
- Aggregates that use the target (target encoding) without out-of-fold.
- A gain that shows up in only one valid period: unstable, it does not confirm.
- A gain below the plan's `Min gain` is not "almost confirmed": it is rejected.

## Source
Alchemist's hypothesis format; group aggregates and per-entity normalization from Recipe 3 of experimenta-ml.

## Examples
_No runs yet. A recipe leaves `experimental` when it has repeatable runs here and passes review._
