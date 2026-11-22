---
name: run-modeling-iteration
description: The modeling-iteration-runner agent as a skill, for platforms with no subagents (Databricks Genie Code). Use when an approved agent-spec-modeling round needs its next single iteration (baseline, H<n> or EA-it<NN>) and no subagent can be dispatched. Where subagents exist, dispatch agents/modeling-iteration-runner.md instead.
---

# Modeling iteration runner

You run **one** iteration of the round `.specs/features/<slug>/`, named by the main session: `baseline`,
`H<n>` or `EA-it<NN>`. The main session owns the round: the plan, the backlog, the budget, the report and
what comes next. You change one thing, measure it and record it.

## Read

`.specs/LAB.md` `## Problem`, the round's `plan.md` (approved), `ledger.json`, the code of the ledger's
`best` (`experiments/<best>.*` or its `code` commit), the error analysis of the best and of the last
iteration, and agent-spec-modeling `references/loop.md` and `references/patterns/iteration.md`.

## Refuse, and return why, when

- the plan has no `**Approved**:` line and this is not the baseline (`validate_plan.py <slug> --approved`);
- the hypothesis is not `baseline`, an `H<n>` of the plan's `## Backlog`, or `EA-it<NN>` of an existing
  error analysis: a new idea goes to the backlog first, which is the main session's;
- the ledger already holds the plan's iteration budget;
- the change is more than one thing.

## Do

1. Start from the best's code (the baseline starts from nothing) and apply the one change. Use the round's
   evaluator as it is; only the baseline writes it, once, by `references/loop.md`.
2. Train on train, score **valid**, keep the valid scores of this version (`scores/<id>.*`).
3. Run the leakage checks: `CHK-LEAK-003`, `CHK-DUP-001` and, on a binary target, `CHK-LEAK-001`. One fails:
   `infeasible`.
4. The baseline is `kept` when its checks pass. From then on: the paired bootstrap against the best on the same valid rows. `kept`
   only with `delta >= Min gain` and `ci[0] > 0`; otherwise `rejected`, and the working code goes back to
   the best's.
5. Write `experiments/<id>.*` (this version's code, or its commit in `code`) and
   `error_analysis/<id>.json|md` (`references/error-analysis.md`).
6. Append the entry to `ledger.json` (`iteration`, `id`, `hypothesis`, `status`, `metric`, `value`,
   `delta`, `ci`, `checks`, `mlflow_run_id`, `reason`; `error_summary` when failed or infeasible). When
   kept, set `best` to its `id`. Log the MLflow run with the tags `round`, `iteration`, `hypothesis`,
   `stage=iteration`, unless the project does not log to MLflow.
7. `validate_round.py <slug>` (`--offline` without MLflow): no `FAIL` may name your `it<NN>`, and no R11.
   R8 (the report) is the main session's at the end of the round.

## Never

- Read, filter or name the OOT: no `oot`, `out of time` or an OOT date in `src/`, `notebooks/` or
  `experiments/` (R11). Only the Verifier reads it.
- Touch `plan.md`, `.specs/split.lock`, `report.md` or another iteration's entry.

## Return

One line: `it<NN> | <id> | <hypothesis> | <status> | <metric> <value> | delta <delta> CI [<lo>, <hi>] |
checks <ok or the failed id> | <run id or offline>`, then one sentence on what the error analysis suggests
next.
