# Verification secom

**Verifier**: subagent
**HEAD**: 7441053
**Experiment**: `dfdee50fa862a2c3`

## OOT by period
| Period | n | positives | pr_auc |
| --- | --- | --- | --- |
| 2008-10-03/2008-10-09 | 78 | 4 | 0.512 |
| 2008-10-10/2008-10-16 | 79 | 6 | 0.471 |

## Valid vs OOT
- Valid: 0.571
- OOT: 0.480
- Drop: 0.091

## Mutations
- CHK-MUT-001: killed - a shuffled target gives pr_auc 0.071 against chance 0.064
- CHK-MUT-002: killed - CHK-LEAK-001 rejected `__future_label` with AUC 1.00

## Findings
- none

## Verdict
PASS
