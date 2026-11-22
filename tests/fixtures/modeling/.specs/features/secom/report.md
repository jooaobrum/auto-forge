# Report secom

## Climb
- Iterations: 3 (kept 2, rejected 1, infeasible 0, failed 0)

## Ledger
| it | status | hypothesis | valid | delta vs best | CI 95% | checks failed |
| --- | --- | --- | --- | --- | --- | --- |
| 00 | **kept** | baseline | 0.1084 | - | - | - |
| 01 | rejected | H1: nothing changes | 0.1084 | +0.0000 | [+0.0000, +0.0000] | - |
| 02 | **kept** | H2: brings s000 back | 0.5714 | +0.4630 | [+0.1791, +0.6842] | - |

## What worked
- H2 (s000 back): the sensor carries the main failure signal; +0.46 PR-AUC with a CI above zero.

## What did not
- H1 (control): zero gain, as expected; the evaluator is deterministic for the same pipeline.

## Error patterns
- FN-heavy at the F1 threshold: some failures have no signal yet.
- The week of 09-16 is the worst; check for a recipe change in that period.

## Domain findings
- Confirmed: failure concentrates on a few sensors; the label rule matches the source count.

## Next round
- z-score of s000 within the week (error analysis: the worst week drifts).
- A smaller class weight to reduce over-confidence in the top decile.
