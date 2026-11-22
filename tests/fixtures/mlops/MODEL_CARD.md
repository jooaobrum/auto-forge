# Model card - workspace.poc_secom_dev.secom_fail

## Model
- `workspace.poc_secom_dev.secom_fail` version 3 (alias `challenger`), task binary, threshold 0.62
- Environment: `dev`

## Traceability
- Git commit: `a1b2c3d`
- Run: `0123456789abcdef0123456789abcdef`
- Source experiment: round `secom`, experiment `dfdee50fa862a2c3` (`.specs/features/secom/verification.md`)
- Reproducibility: production valid pr_auc 0.569 vs experiment 0.571 (tolerance 0.01), seed 42, uv.lock sha256 `19fc54824208...`

## Data
- `workspace.curated.secom` v12

## Metrics
- Valid pr_auc: 0.569
- OOT pr_auc: 0.48 (from the round's Verification)

## Intended use
Process engineering, before the final test, to rank the lots most likely to fail for inspection.

## Limitations
FN-heavy at the F1 threshold; the week of 09-16 is the weakest; depends on sensor s000.

## Monitoring
- Inference table: `inference`; metrics: pr_auc, positive_rate, score_mean
- Drift vs training, threshold 0.2; schedule daily; alert `ds-alerts`
