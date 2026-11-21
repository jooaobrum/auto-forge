# Leakage

Leakage is the model seeing, in training, something it will not have at prediction time. The classic
symptom: a gain that is too big, too easy, and a strong drop on OOT.

| Pattern | Example | How to catch it |
| --- | --- | --- |
| Target inside a variable | a column filled after the outcome (status, reason, closing date) | CHK-LEAK-001 (univariate AUC >= 0.98) at every iteration; the Exclusions and Label rule of the `## Problem` in `.specs/LAB.md` (columns filled only after the event never become features) |
| Variable from the future | batch mean computed with the whole batch, including later rows; centered `rolling`; `bfill` | CHK-LEAK-003 (training features do not change with future rows) at every iteration |
| Statistic fitted outside training | scaler/imputer/encoder/selection fitted on the whole dataset before the split | fit everything that learns on train, inside the pipeline; the Verifier's review |
| Target encoding without out-of-fold | target mean per category computed on the same rows | inside the pipeline, with inner CV (e.g. sklearn's `TargetEncoder`); CHK-LEAK-001 |
| Same individual in two splits | id or group (batch, customer) in train and valid | time split in the lock; CHK-SPLIT-002 when there is a group |
| Duplicate rows across splits | the same feature vector in train and valid | CHK-DUP-001 at every iteration |
| Selection by OOT | choosing threshold, window or model by looking at OOT | OOT exists only in Verify; `validate_round` R11 scans the code (CHK-OOT-001) |
| Too much selection by valid | 50 iterations choosing on the same valid | min gain + CI per iteration; Verify measures the valid-to-OOT drop |
| Target proxy through sampling | positives coming from another source/period than the negatives | EDA: distribution of dates and sources per class ([eda.md](eda.md)) |

## Verify mutations

- **Shuffled target (CHK-MUT-001):** trained with the target shuffled, the pipeline must fall to chance
  on OOT (median of 10 repetitions). If it does not, something in the preparation or the pipeline sees
  the target through another path.
- **Future column (CHK-MUT-002):** a noisy copy of the target is added; CHK-LEAK-001 must fail. It
  guarantees the detector is alive.
