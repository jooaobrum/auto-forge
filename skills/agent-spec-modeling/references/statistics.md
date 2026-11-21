# When a gain is noise

## The keep rule

For each iteration, compare the new version's scores with the current best's **on the same valid rows**,
with ~1000 paired bootstrap resamples (stratified by class in the binary case, so every replica has
positives; example in [patterns/iteration.md](patterns/iteration.md)). It stays only if:

- the point gain >= the plan's `Min gain`, **and**
- the lower limit of the 95% CI of the gain > 0.

The gain shown is always "positive = better", whether the metric goes up (PR-AUC) or down (RMSE).

## Choosing the Min gain

- Run the noise control: an iteration with no real change (a comment) has gain 0 by construction; two
  different seeds of the same model show the training noise. The `Min gain` sits above that.
- Small valid or few positives - wide CI - only big gains pass. It is honest: with 30 positives you
  cannot tell 0.01 of PR-AUC.
- Do not change the `Min gain` in the middle of the round to save an idea.

## Multiple comparisons

Each iteration chooses by valid. With 30 iterations, some pass by luck even with a CI. Defenses: the CI
per iteration, a finite budget, the search order (ideas with a mechanism first) and Verify, which
measures the valid-to-OOT drop of the best. A big drop = the round overfit valid.

## Metrics

| Problem | Primary | Why |
| --- | --- | --- |
| Rare binary (< 10% positives) | PR-AUC | ROC-AUC stays high with poor precision when the class is rare |
| Balanced binary | ROC-AUC or log loss | ranking or probability |
| Decision with cost | recall @ fixed precision, expected cost | the threshold is part of the solution |
| Regression | RMSE (large errors matter) or MAE (robust) | choose by the cost of the error |

The chance level for PR-AUC is the prevalence; for ROC-AUC, 0.5.

## Threshold

Chosen on valid (the F1 one is a good reference for the error analysis), never on OOT. If the business
has a constraint (minimum precision, inspection capacity), choose by it, on valid.

## Stability

Look at the metric per period in the error analysis. A gain that comes from one period only is fragile,
even with a positive CI; note it in the report.
