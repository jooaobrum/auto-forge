---
name: agent-spec-modeling
description: Research lane that takes a model from a confirmed Problem to a verified best experiment - a locked time split, EDA on train only, a baseline, then iterations of one change each from an approved backlog, kept only with a gain whose CI is above zero, closed by a Verification on out-of-time data. Use when agent-spec-router routes a model with no champion, or a new round of a model's backlog, here, or the user asks to build a model, run a round or hill-climb a metric.
---

# Agent Spec Modeling

One **Round**, one folder: `.specs/features/<slug>/`. You write the split, the features, the training and the
evaluation however the problem needs; the references give patterns that work; the gates check the pattern was
followed. Every script is standard-library Python in `<skill-dir>/scripts/`, takes `[--root <repo>] <slug>`, and
names the rule it fails (`FAIL [R6] ...`). Exit codes: `0` pass, `1` fail, `2` invalid input,
`5` halted (`.specs/HALT` exists: stop and ask the user).

```
## Problem (router, confirmed) -> split lock -> EDA on train -> backlog -> plan approved
   -> baseline -> LOOP: read the error analysis -> one change -> measure on valid -> leakage checks
                        -> compare with the best (CI) -> keep or revert -> ledger (+ MLflow)
   -> report.md -> Verification on OOT (fresh context) -> delivery: promote or reject
```

```
┌──────┐   ┌───────┐   ┌────────┐   ┌─────────┐
│ PLAN │ → │ CLIMB │ → │ VERIFY │ → │ DELIVER │
└──────┘   └───────┘   └────────┘   └─────────┘
 split,     one change   OOT, by a    promote or
 EDA, plan  per iter.    Verifier     reject
```

## Rules

These hold even if no reference file is read.

1. **The split is locked before anyone looks at the data**, and the OOT belongs to the Verification only:
   nothing in `src/`, `notebooks/` or `experiments/` reads or names its period (R11).
2. **The plan is the contract.** The Question, the Metric with its Min gain, the Budget and the Max drop are
   fixed at approval; the backlog grows (a new idea is written in the plan before it runs), it is never
   rewritten to fit a result.
3. **One change per iteration**, named `H<n>` or `EA-it<NN>`, its code recoverable, its error analysis written.
4. **Keep only a real gain**: `delta >= Min gain` and the 95% paired-bootstrap CI above zero, on the same valid
   rows. Anything else is `rejected` and the code goes back to the best.
5. **Leakage checks every iteration**; a failed one makes it `infeasible`, whatever its metric.
6. **Author is not verifier.** The **verifier** agent judges the best on the OOT, once; `self-verified` fails V1.
7. **The completion gate is a script**: `validate_verification.py` exits 0 before `deliver.py --decision
   promote`.
8. **The files hold the run.** The approval is `**Approved**: <date> - user: "<their words>"`; after a
   compaction, resume from the files ([memory.md](references/memory.md)). A push, a deploy or a write to a
   production table needs the user's explicit OK.

## Phases

| Phase | What it produces | Reference |
| --- | --- | --- |
| Plan | split lock, EDA on train, backlog, `plan.md` approved | [plan.md](references/plan.md), [eda.md](references/eda.md), [ideas.md](references/ideas.md), [patterns/split.md](references/patterns/split.md) |
| Climb | the baseline, one iteration per hypothesis, the ledger, `report.md` | [loop.md](references/loop.md), [patterns/iteration.md](references/patterns/iteration.md), [error-analysis.md](references/error-analysis.md), [statistics.md](references/statistics.md) |
| Verify | the Verification on OOT by the Verifier, `verification.md`, the gate | [verify.md](references/verify.md) |
| Deliver | `delivery.md`; promote seeds `<slug>-mlops/plan.md` | below |

Decisions, lessons and resuming: [memory.md](references/memory.md).

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
5. Write `plan.md` from [references/plan.md](references/plan.md) (agent-spec-writer drafts it): the question,
   the metric and the bar, the data, the Shape of the path a row takes to a score, the backlog with what each
   hypothesis should move and risks, Out of scope and Assumptions. `validate_plan.py <slug>` must exit 0.
6. The user approves the backlog and the budget: `**Approved**: <date> - user: "<their words>"`, then
   `validate_plan.py <slug> --approved`. Only the baseline may run before.

## 2. Work: the climb

The loop is in [loop.md](references/loop.md); each iteration leaves the evidence in
[patterns/iteration.md](references/patterns/iteration.md). You own the loop and its choices; where subagents
exist, dispatch each iteration to the **modeling-iteration-runner** agent (`agents/modeling-iteration-runner.md`)
with the slug and one hypothesis, and read the ledger row it returns. With no subagents, run the
`run-modeling-iteration` skill in this chat.

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

Dispatch the **verifier** agent (`agents/verifier.md` of this plugin) with the slug and nothing else: it
follows [verify.md](references/verify.md), judges the ledger's best at a clean commit, reads the OOT once, by
period, runs both mutations, writes `verification.md` and returns the verdict and the findings. Then
`validate_verification.py <slug> [--offline]` (V0-V7) must exit 0; it writes `gate.json` and `results.md`.
You never verify your own round: `self-verified` fails V1. With no subagents, a new chat runs the
`verify-model` skill and declares `**Fallback**`; the gate warns: say so in the delivery. A drop above the
plan's Max drop is a finding, not something to fix on the OOT.

## 4. Deliver

`deliver.py <slug> --decision promote|reject` writes `delivery.md`. `promote` needs the Verification to pass and
seeds `.specs/features/<slug>-mlops/plan.md`: hand it to agent-spec-router, which routes it to
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
