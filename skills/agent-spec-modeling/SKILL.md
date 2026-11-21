---
name: agent-spec-modeling
description: Research lane that takes a model from a confirmed Problem to a verified best experiment - a locked time split, EDA on train only, a baseline, then iterations of one change each from an approved backlog, kept only with a gain whose CI is above zero, closed by a Verification on out-of-time data. Use when agent-spec-router routes a model with no champion, or a new round of a model's backlog, here, or the user asks to build a model, run a round or hill-climb a metric.
---

# Agent Spec Modeling

One **Round**, one folder: `.specs/features/<slug>/`. You write the split, the features, the training and the
evaluation however the problem needs; the references give patterns that work; the gates check the pattern was
followed. Every script is standard-library Python in `<skill-dir>/scripts/`, takes `[--root <repo>] <slug>`, and
names the rule it fails (`FAIL [R6] ...`). Exit codes: `0` pass, `1` fail, `2` invalid input.

```
## Problem (router, confirmed) -> split lock -> EDA on train -> backlog -> plan approved
   -> baseline -> LOOP: read the error analysis -> one change -> measure on valid -> leakage checks
                        -> compare with the best (CI) -> keep or revert -> ledger (+ MLflow)
   -> report.md -> Verification on OOT (fresh context) -> delivery: promote or reject
```

## Load points

Read `.specs/LAB.md` `## Domain skills` and load the skills listed for each point when you reach it:
**plan** (before the split and the plan), **work** (before the baseline), **verify** (before the Verification).
A platform skill (Databricks, MLflow) comes from there; nothing here needs one.

## 1. Plan

1. The `## Problem` of `.specs/LAB.md` is confirmed: `route.py problem` (agent-spec-router) exits 0. If not,
   hand back to the router.
2. **Lock the split** before looking at the data: train, valid and OOT time windows with their row counts in
   `.specs/split.lock` ([patterns/split.md](references/patterns/split.md)). The valid judges iterations; the OOT
   belongs to the Verification only.
3. **EDA on train only** ([eda.md](references/eda.md)), into `.specs/features/<slug>/eda.md`.
4. **Backlog** with the user ([ideas.md](references/ideas.md)): hypotheses `H<n>`, each with an idea, a why and
   a source.
5. Fill [references/plan.md](references/plan.md) into `plan.md`; `validate_plan.py <slug>` must exit 0.
6. The user approves the backlog and the budget: `**Approved**: <date> - user: "<their words>"`, then
   `validate_plan.py <slug> --approved`. Only the baseline may run before.

## 2. Work: the climb

The loop is in [loop.md](references/loop.md); each iteration leaves the evidence in
[patterns/iteration.md](references/patterns/iteration.md):

1. **The baseline is iteration one**, kept. Every later iteration changes **one thing**, named `H<n>` (from the
   backlog; add a new idea there first) or `EA-it<NN>` (a finding of iteration NN's error analysis).
2. Its code is recoverable (`experiments/<id>.*` or a `code` commit) and it leaves `error_analysis/<id>.*`
   ([error-analysis.md](references/error-analysis.md)). Read it before the next change.
3. **Leakage checks** every iteration ([patterns/leakage-checks.md](references/patterns/leakage-checks.md),
   ids in [check_catalog.json](references/check_catalog.json)); a failed check makes it `infeasible`.
4. **Keep only a real gain**: `delta >= Min gain` and the 95% paired-bootstrap CI above zero, on the same valid
   rows ([statistics.md](references/statistics.md)). Otherwise `rejected`, and the code goes back to the best.
5. Record it in `ledger.json`, and in MLflow when the project logs there (otherwise pass `--offline` and say
   so in the report). Never read or name the OOT period in `src/`, `notebooks/` or `experiments/`.
6. Stop at the iteration budget. `round_report.py <slug>` writes the Ledger and Climb of `report.md`; fill
   What worked, What did not, Error patterns, Domain findings and Next round.
7. `validate_round.py <slug> [--offline]` (R0-R11). Each `FAIL` line is the next piece of work.

Knowledge: [features.md](references/features.md), [models.md](references/models.md),
[leakage.md](references/leakage.md), recipes in `references/recipes/` and
[recipes-library.md](references/recipes-library.md).

## 3. Verify

A fresh context (a subagent, or a new chat) follows [verify.md](references/verify.md): it judges the ledger's
best at a clean commit, reads the OOT once, by period, runs both mutations and writes `verification.md`. Then
`validate_verification.py <slug> [--offline]` (V0-V7) must exit 0; it writes `gate.json` and `results.md`.
`self-verified` only warns: say so in the delivery. A drop above the plan's Max drop is a finding, not
something to fix on the OOT.

## 4. Deliver

`deliver.py <slug> --decision promote|reject` writes `delivery.md`. `promote` needs the Verification to pass and
writes `.specs/features/<slug>-mlops/spec.md`: hand it to agent-spec-router, which routes it to
agent-spec-mlops. A model already in production that fails on some slices is not a new round: the router sends
it to agent-spec-experiment.

## Files of a round

```
.specs/split.lock                 # the windows, once per project
.specs/features/<slug>/
├── plan.md                       # question, target, data, metric, budget, max drop, backlog, approval
├── eda.md                        # train only
├── ledger.json                   # every iteration: hypothesis, status, value, delta, CI, checks, run
├── experiments/<id>.*            # each iteration's code (or its commit in `code`)
├── error_analysis/<id>.*         # where each version went wrong, on valid
├── report.md                     # what worked, what did not, error patterns, next round
├── verification.md               # by the Verifier; the only place with OOT metrics
└── gate.json, results.md, delivery.md
```

Ported from ds-factory's `exp-hillclimb`, `exp-ideas` and `data-explore` (jooaobrum); the gate structure
derives from tlc-spec-lean by Tech Leads Club (CC-BY-4.0).
