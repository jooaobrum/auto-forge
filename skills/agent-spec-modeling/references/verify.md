# Verify

You are the Verifier. You did not write this round and you do not trust what the author said. Read only
`.specs/LAB.md`, `.specs/split.lock`, the round's `plan.md`, `ledger.json`, `report.md` and the code of
the best experiment (all in `.specs/features/<slug>/`, except the lab and lock files). You are the only
one who reads the holdout, once.

## Steps

1. `validate_round.py <slug>` passes (with `--offline` when the project does not log to MLflow). If not,
   send it back to the author.
2. **Clean HEAD.** `git status` shows no changes; write the sha in `**HEAD**` and the ledger's `best`
   in `**Experiment**`.
3. **Read the best's code** against [leakage.md](leakage.md): do the features only look back? Does
   anything that learns from data sit outside the pipeline? Did any column filled only after the event
   (see Label rule and Exclusions in the `## Problem` of `.specs/LAB.md`) become a feature? Each problem
   is a finding.
4. **Evaluate on the holdout**, with your own code, separate from the round's (in `verify/`, never in
   `src/`, `notebooks/` or the round's experiments/, because `validate_round` R11 scans those for OOT
   references):
   - train the best on train; threshold and any choice fixed on **valid**;
   - score OOT; overall metric and **per period**; valid-to-OOT drop;
   - error analysis on OOT (do the worst period and the worst segment match the valid one?);
   - **mutations** ([patterns/leakage-checks.md](patterns/leakage-checks.md)): shuffled target (median
     of 10 repetitions at chance level) and future column (the univariate check fails);
   - optional: adversarial validation train vs OOT as a drift alert.
5. Write `verification.md` with `**Verifier**: fresh-context|subagent|self-verified`, `**HEAD**: <sha>`,
   ``**Experiment**: `<best id>` `` and the sections:
   - `## OOT by period` (a table, the metric in the last column);
   - `## Valid vs OOT` (`- Valid:`, `- OOT:`, `- Drop:`);
   - `## Mutations` (`- CHK-MUT-001: killed - <evidence>` or
     `- CHK-MUT-002: n/a - <reason of 8+ chars>`);
   - `## Findings` (`- F1: <text> | closed: <sha>` after rechecking the fix);
   - `## Verdict` (PASS).
6. `validate_verification.py <slug>` (V0-V7; `--offline` as above). The final report opens with its last
   line.

No subagent: run in a fresh chat with only this file and write `**Verifier**: self-verified`; the gate
warns. A drop above the limit is not solved here: it is a finding, and the next round starts from it.
