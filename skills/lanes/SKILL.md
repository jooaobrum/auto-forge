---
name: lanes
description: Take a ready Brief through plan, approval, work, verification and delivery, in the build lane (end-to-end test proves it) or the research lane (a rate over a dataset proves it), for apps, pipelines, models and agents. Use after `rl brief` passes, or when the user says "experiment", "run the gate", "data contract" or "deliver".
---

# Lanes

Stages 3-7 for one piece of work at `.lanes/work/<slug>/`. The CLI is `rl` (or `python -m lanes`); it reads and
writes files and runs nothing. You run the work with the host's own tools and keep going until the gate
closes the goal. Exit codes: `0` ok, `1` gate fail, `2` invalid input, `3` variant cap, `4` budget spent.

## 3. Plan

- **build lane**: plan with tlc-spec-lean; the Brief's `**Plan**:` line points at that `plan.md`. For the
  `pipeline` Profile the plan cites the data contract `contracts/<dataset>.yaml` (ODCS v3 subset: `required`,
  `unique`, `nullValues`, `invalidValues`, `duplicateValues`, `rowCount`, `freshness`, `sql`), the input
  fixture and the golden rows CSV.
- **research lane**: write `experiment.md` (Diagnosis: the Failure Mode read from failing traces, its cause
  class, hypotheses) and `experiment.json`:
  `{"failure_mode", "target_metric", "min_delta", "target_cases", "edit_scope", "budget_tokens"}`.
  When the cause class is deterministic, the fix belongs in code: say so and route it to the build lane.

## 4. Approve

The user writes `**Approved**: <date> - user: "<their words>"` in the plan. Commit, then `rl freeze <slug>`.

## 5. Work

- **research**: record the current behavior once with `rl baseline <slug> --from <results file>`, then per
  Variant `rl select <slug> --variant <name>`, edit only inside the Edit Scope, run exactly the Cases and k
  in `selection.json`, save Results files under `runs/<variant>/`. Rerun Cases `select` lists as stale.
- **pipeline**: `rl contract <slug> contracts/<dataset>.yaml --golden <golden.csv> --dialect spark|sqlite`;
  run the pipeline on the fixture into a dev schema, run `contract.sql` there (Genie, a notebook, SQLite), save
  its output as `runs/main/contract.csv`.
- **app**: run the host's e2e suite with JUnit output into `runs/main/junit.xml`.

## 6. Verify

`rl gate <slug> --variant <name>` (`--confirm` once before delivering an Experiment; a Build Change of an
agent or model cites `rl gate <slug> --regression-only` as its proof). Each `FAIL` line is the next piece of
work: rework and return to 5. Stop when the gate passes or `rl select` exits `3`.

When `rl budget <slug>` or `rl select` exits `4`, stop and ask the user whether to continue. On their yes,
`rl budget <slug> --add <tokens> --user "<their words>"`.

## 7. Deliver

`rl deliver <slug>` (research: `--decision adopt|promote|reject`). `promote` writes a build-lane Brief for
the code fix; continue it with step 3. Report `delivery.md` to the user.
