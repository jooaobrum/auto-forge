---
name: data-window
profile: tabular
status: experimental
---

# data-window

## When to use
The process changes over time (sensor drift, recipe change, seasonality) and it is unclear how much history helps.

## Typical hypotheses
- Train only on the last N days/weeks of train.
- Weight recent examples (weight decreasing with age).
- Remove a known anomalous period from training.

## Probe and budget
The same model configuration trained on different windows that **end at the same point** (the end of train), evaluated on the same temporal valid. Report the metric per valid period.
Budget: 3-4 windows per round.

## Required checks
- `CHK-SPLIT-003` - OOT dates after the train and valid dates
- `CHK-OOT-001` - The round's code does not cite the holdout or its dates

## Traps
- A window that advances into valid or OOT.
- Comparing windows with different valid sizes.
- A window that is too short leaves training without positives on imbalanced problems: check the positives per window.

## Source
Alchemist's data-window study (the name only; the content is the team's).

## Examples
_No runs yet. A recipe leaves `experimental` when it has repeatable runs here and passes review._
