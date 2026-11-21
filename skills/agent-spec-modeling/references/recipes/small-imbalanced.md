---
name: small-imbalanced
profile: tabular
status: experimental
---

# small-imbalanced

## When to use
Few examples and a rare class (SECOM has 104 failures in 1,567). Accuracy is useless; the variance between splits is high.

## Typical hypotheses
- `class_weight="balanced"` or a weight proportional to the inverse of the prevalence.
- Low-variance models (regularized logistic regression, shallow trees) before deep boosting.
- Threshold chosen on valid by the business criterion (F1, recall at a fixed precision).
- Resampling (SMOTE, undersampling) **only inside train**.

## Probe and budget
Repeated temporal cross-validation inside train+valid (blocks by time) to estimate the variance, PR metrics (PR-AUC, recall@precision) and the threshold tuned separately, on valid.
Budget: 1 probe per technique; repeat with 3 seeds to see the variance.

## Required checks
- `CHK-IMB-001` - Realistic prevalence in valid and OOT
- `CHK-IMB-002` - Threshold tuned on valid and never on OOT

## Traps
- Resampling before the split: valid and OOT end up with an unrealistic prevalence (CHK-IMB-001).
- Tuning the threshold on OOT (CHK-IMB-002): the threshold is recorded in the run before Verify.
- Reporting ROC-AUC alone: with 7% positives it looks good while the precision is poor.
- A 0.01 PR-AUC difference between configurations is usually within noise; look at the variance.

## Source
Recipes 6 (severe imbalance) and 9 (small dataset) of experimenta-ml.

## Examples
_No runs yet. A recipe leaves `experimental` when it has repeatable runs here and passes review._
