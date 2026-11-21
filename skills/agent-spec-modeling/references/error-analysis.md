# Reading the error analysis

`error_analysis/<id>.json` is written at every iteration, on valid. Start with the `summary` (ready-made
sentences) and go down to the detail it points at.

## Fields

| Field | What it is |
| --- | --- |
| `summary` | the heaviest patterns, one line each |
| `confusion` | TP/FP/TN/FN, precision and recall at the threshold that maximizes F1 on valid |
| `calibration_deciles` | mean score vs real rate per score decile |
| `high_confidence_errors` | the FPs with the highest score and the FNs with the lowest score, each with the variables where it departs most from the training mean (z-score) |
| `score_histogram` | score distribution for positives and negatives |
| `residuals`, `high_error_samples`, `residual_histogram` | the regression equivalent |
| `segment_breakdown` | metric per group (the lock's `group_col` and `--segments`) and per period (`_period`) |

## From the pattern to the next change

| Pattern | Reading | Next ideas |
| --- | --- | --- |
| Too many FN | signal is missing for part of the positives | look at the FNs' `deviations`: which variables do they share? features that capture that failure mode; group-relative ones; missingness indicators |
| Too many FP | negatives that look positive | what do the FPs have in common (segment, period)? a feature that separates that context; an interaction with the segment |
| One segment much worse | the model does not see the group's difference | per-group normalization (`x - group_median`), a group feature, or a model that captures interaction (trees) |
| One period much worse | drift or event | temporal feature, training window (recipe data-window), check a process change with the domain |
| Top decile overconfident | overconfident model, usually a high class weight | lower `class_weight`, regularize, calibrate inside the pipeline |
| Positive and negative scores overlap in the histogram | little separation | new features, not hyperparameters |
| High errors with extreme variables (z > 4) | outliers or measurement error | clip/winsorize inside the pipeline, log, outlier indicator |
| Biased residual (regression) | the model under/overestimates systematically | target transform, a feature that explains the level, a count model |
| Heavy error tail (regression) | a few cases very wrong | robust loss (Huber), log of the target, a feature for those cases |

## Findings that become iterations

When the error analysis of iteration N suggests something that is not in the backlog, name the
hypothesis `EA-itNN: <change>` and add it to the next plan's backlog if it is kept. A pattern that
repeats over several iterations and does not yield is a domain finding: it goes to `## Domain findings`
of `report.md` and, with proof, becomes a lesson.
