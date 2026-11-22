# Promotion: challenger against champion

Test a new version and promote it safely. The experiment lane's gate, applied to a promotion: the Cases are
slices of the recent period, the Baseline is the champion, the Variant is the challenger. No slice may regress,
and the target gain needs a CI above zero.

## Before promoting

1. `validate_prod.py <slug>` passes on the commit that ships; `promote.py` refuses to run otherwise.
2. `.specs/prod/trace.json` names the version that ships and the verified round it came from.
3. Add `## Promotion` to the spec:

```markdown
## Promotion

**Champion**: version 1
**Challenger**: version 2
**Period**: 2026-10-01..2026-10-31
**Metric**: accuracy
**Min gain**: 0.05
**Tolerance**: 0

| Slice | Description | Target |
| --- | --- | --- |
| all | every account scored in October | yes |
| new | tenure under 6 months | |
| long | tenure of 6 months or more | |
```

- **Metric** defaults to the `**Metric**` of `## Problem` in `.specs/LAB.md`; `log_loss`, `brier`, `rmse` and
  `mae` count lower as better.
- **Target** slices carry the gain that must be real; with none marked, a slice named `all` is the target.
- **Min gain** (default 0) is the smallest target gain worth a swap. **Tolerance** (default 0) is how far a
  slice's mean may fall before it counts as a regression.
- **Champion**: `none` for the first model in production: the gate has nothing to compare and passes.

## Backtest

Score the same recent period with both versions (shadow scoring or a backtest window), slice by slice, on at
least 20 paired bootstrap resamples: resample `i` draws the same rows for both models. Write one Results file
per model:

```
.specs/features/<slug>/runs/champion/backtest.json
.specs/features/<slug>/runs/challenger/backtest.json
{"runs": [{"case": "new", "run": 0, "metrics": {"accuracy": 0.81}}, ...]}
```

## Gate

`promote.py gate <slug>` writes `promotion.md` (per slice: champion, challenger, gain and its 95% CI) and
`promotion.json`. It fails when:

- a slice regresses: its mean gain is below `-Tolerance`, even when the average wins;
- the target gain, averaged over the Target slices per resample, is below Min gain, or its 2.5th percentile is
  not above zero;
- a slice has no runs for one model, or fewer than 20 paired resamples.

## The alias swap

Show `promotion.md` and ask the user. On their OK, `promote.py approve <slug> --user "<their words>"` records
it in `promotion.json` and `.specs/prod/promotions.md` (date, versions, words, evidence). Then move the
`champion` alias with the platform skill (on Databricks with MLflow:
`MlflowClient().set_registered_model_alias(name, "champion", version)`). A deploy and an alias change in `qa`
or `prod` need that explicit OK.

## Rollback

Move `champion` back to the previous version listed in `.specs/prod/promotions.md`. The code does not change,
and monitoring keeps the same inference table.
