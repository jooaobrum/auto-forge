# churn - to production

**Profile**: model
**Lane**: build
**Round**: churn
**Experiment**: c0ffee0123456789
**Approved**: 2026-11-22 - user: "go, dev only for now"

## Goal

Experiment `c0ffee0123456789` of round `churn` runs in production to the team's standard and reproduces its
valid metric.

## Proof

`validate_prod.py churn-mlops` (D1-D10), then `promote.py gate churn-mlops`.

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
