# Models

## Ladder

| Step | Binary | Regression | When to climb |
| --- | --- | --- | --- |
| Ruler | LogisticRegression (`class_weight="balanced"` if rare), imputer + scaler | Ridge | always starts here |
| Strong linear | Logistic with L1/elastic-net, splines/binning on variables with a nonlinear relation | Lasso, Poisson/Tweedie for counts | features stop paying off and the EDA shows nonlinearity |
| Trees | LightGBM / XGBoost (`n_estimators` 300-800, `learning_rate` 0.03-0.1, `num_leaves` 15-63, high `min_child_samples` if little data) | same with a suitable objective | interactions and nonlinearities the linear model misses |
| Ensemble | average of linear + trees | same | only at the end, if the two err in different places (compare the error analyses) |

## Small or imbalanced data

- Few positives: low-variance models, strong regularization, high `min_child_samples`, low depth.
- `class_weight` changes calibration: if the error analysis shows an overconfident top decile, lower it.
- Resampling (SMOTE, undersampling) only inside the pipeline (imblearn) and only on training.

## Hyperparameters

- Only at step 6 of the search order, on the best recipe, with few iterations.
- One iteration = one set of values with a justification ("more regularization because valid dropped by
  period"), not a blind search.
- Early stopping uses a slice of **train** (`validation_fraction`), never the valid that decides the
  iterations.
