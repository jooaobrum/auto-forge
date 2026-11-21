---
name: feature-selection
profile: tabular
status: experimental
---

# feature-selection

## When to use
Many variables for few examples (SECOM has 590 signals for 1,567 rows), noise dominating, or a model that is unstable across periods.

## Typical hypotheses
- Remove constants and near-constants (zero variance, one value in > 99% of the training rows).
- Remove variables with > 50% missing in train.
- Permutation importance on valid: remove those with importance <= 0.
- Null importance: keep only variables whose real importance beats the 95th percentile of the importance with a shuffled target.

## Probe and budget
Permutation importance computed on **valid** over the train-only model, and null importance with 20-50 shuffles of the target on train. Compare the model on the subset against the baseline on valid.
Budget: 1 probe for cheap filters (constants, missing), 1 for permutation, 1 for null importance.

## Required checks
- `CHK-REG-001` - No regression against the baseline on valid

## Traps
- Selecting with the whole dataset (train + valid) and then evaluating on valid: selection leakage.
- Importance by gain (gain/split) instead of permutation: it favors high-cardinality variables.
- High correlation between variables splits the permutation importance; group the correlated ones first.

## Source
Alchemist's feature selection (permutation importance) and null importance from Recipe 9 of experimenta-ml.

## Examples
_No runs yet. A recipe leaves `experimental` when it has repeatable runs here and passes review._
