---
name: agent-spec-mlops
description: Build lane that takes a verified modeling round to production code - one config per environment, pipelines with a main() and tested logic, organized MLflow, declared monitoring, a trace and a model card - through agent-spec-lean's plan, checks, build and independent Verifier, with validate_prod.py (D1-D10) among the proofs, then promotes the challenger over the champion slice by slice. Use when agent-spec-router hands over a `<slug>-mlops` plan from a promoted round, or the user asks to industrialize a model, write its pipelines, produce its model card, or promote, swap or roll back a champion.
---

# Agent Spec MLOps

The research is done; what is left is build work held to the team's standard. So this is agent-spec-lean, for a
model going to production: the notebook becomes production code ([standard.md](references/standard.md)),
`validate_prod.py` checks the standard was followed and that production reproduces the experiment, lean's
Verifier judges the work, and `promote.py` decides whether the challenger may take the champion's place. Every
script is standard-library Python in `<skill-dir>/scripts/`. Exit codes: `0` pass, `1` fail, `2` invalid input,
`5` halted (`.specs/HALT` exists: stop and ask the user).

```
┌──────┐   ┌────────┐   ┌───────┐   ┌────────┐   ┌─────────┐   ┌─────────┐
│ PLAN │ → │ CHECKS │ → │ BUILD │ → │ VERIFY │ → │ DELIVER │ → │ PROMOTE │
└──────┘   └────────┘   └───────┘   └────────┘   └─────────┘   └─────────┘
 lean plan   D1-D10 and   port the    proofs +     route.py      per slice,
 + contract  the score    experiment  Verifier     deliver       user's OK
```

## Rules

agent-spec-lean's rules hold, all of them ([SKILL.md](../agent-spec-lean/SKILL.md)). What production adds:

1. **Port, do not improve.** The same data preparation, features, model and threshold as the round's best
   experiment. A change to any of them is a new modeling round, not this work.
2. **Production reproduces the experiment**: the valid metric within the trace's tolerance, on the same valid
   window (D7). A gap is a finding, never a tolerance widened.
3. **The standard is checked by a script**: `validate_prod.py` (D1-D10) is the proof of the checks that claim
   a rule of [standard.md](references/standard.md); the logic it cannot see (the score, the features) gets
   tests of its own, and those are where the Verifier's mutations go.
4. **Nothing leaves dev without the user.** `git push`, a deploy, and any alias change in `qa` or `prod` need
   the user's explicit OK; `champion` moves only through `promote.py approve` with their words.

## Load points

Read `.specs/LAB.md` `## Domain skills` and load the skills listed for each point when you reach it:
**plan** (before the plan), **work** (before writing the pipelines), **verify** (before the proofs and the
Verifier). The platform skill lives there: Databricks bundles, Unity Catalog and MLflow conventions
(`data-databricks-sql`, `ml-mlflow-log` are the examples). Nothing here needs one; with `platform: databricks`
in the config the Databricks rules (D5, the Unity Catalog registry of D10) apply.

## Phases

| Phase | What it produces | Reference |
| --- | --- | --- |
| Plan | the seed of `deliver.py --decision promote`, completed: lean's plan plus the contract of the tables written, the proof, the promotion | [plan.md](references/plan.md), then lean's [plan.md](../agent-spec-lean/references/plan.md) |
| Checks | one check per rule of the standard the plan claims (proof: `validate_prod.py`), one per rule of the ported logic (proof: its tests) | lean's [checks.md](../agent-spec-lean/references/checks.md) |
| Build | config, pipelines, tests, MLflow, monitoring, the trace and the model card, to the standard | [standard.md](references/standard.md), lean's [build.md](../agent-spec-lean/references/build.md) |
| Verify | `check_proofs.py`, then the Verifier: mutations in the ported logic, the trace against the data | lean's [verify.md](../agent-spec-lean/references/verify.md) |
| Deliver | `route.py deliver` refuses until lean's `validate_verification.py` passes | agent-spec-router |
| Promote | challenger against champion, slice by slice | [promote.md](references/promote.md) |

Decisions, lessons and resuming: lean's [memory.md](../agent-spec-lean/references/memory.md).

## Build, to the standard

Port the best experiment as it is.

1. `config/project.yml` with `dev`, `qa` and `prod`, each writing to its own `catalog.schema` (D1); nothing of it
   hardcoded in `src/` (D2).
2. `src/<pkg>/pipelines/<name>.py` with a `main()` that reads the config, at least `train` and `score` (D3);
   one `tests/test_<module>.py` per module (D4).
3. Deploy targets and jobs with `--env` (D5, Databricks); MLflow registry and tags (D10); monitoring declared
   (D6).
4. Run `train` in `dev`: it writes `.specs/prod/trace.json` with the commit, the tables and their versions, the
   run, the model version, the source round and its valid metric, the lock file hash and the seed (D7, D9).
5. `model_card.py` writes `MODEL_CARD.md`; a person reviews Intended use and Limitations (D8).

The checks that claim the standard share one proof that runs the tests with
`--junitxml .specs/features/<slug>/runs/main/tests.xml` and then `validate_prod.py <slug>`, so
`check_proofs.py` reruns it at `HEAD`. `validate_prod.py` writes `gate.json` and `results.md`; each
`FAIL [Dn]` line is the next piece of work, and `WARN [D5] skipped` says the platform rules did not apply.

## Promote

[promote.md](references/promote.md): add `## Promotion` to the plan (champion, challenger, metric, slices),
backtest both versions on the recent period into `runs/champion/` and `runs/challenger/`, then
`promote.py gate <slug>`. No slice may regress and the target gain needs a CI above zero. Show `promotion.md`;
on the user's OK, `promote.py approve <slug> --user "<their words>"`, then move the alias. Rollback is the
previous version in `.specs/prod/promotions.md`.

## Scripts

| When | Command |
| --- | --- |
| The user approved the plan, committed | `route.py freeze <slug>` (runs lean's `validate_plan.py`) |
| Before building | lean's `validate_checks.py <slug>` |
| After `train` in dev | `model_card.py`, then `validate_prod.py <slug>` |
| Before the Verifier, and after the fix | lean's `check_proofs.py <slug> [--mutations <file>]` |
| Before declaring done | lean's `validate_verification.py <slug>`, then `route.py deliver <slug>` |
| To promote | `promote.py gate <slug>`, then `promote.py approve <slug> --user "<their words>"` |

## Artifacts

```
config/project.yml, src/<pkg>/, tests/, MODEL_CARD.md   # the standard (references/standard.md)
.specs/prod/trace.json, .specs/prod/promotions.md
.specs/features/<slug>-mlops/
├── plan.md                      # seeded by the round, completed; ## Promotion added later
├── checks.md                    # lean's checks; D1-D10 and the ported logic
├── runs/main/tests.xml          # the tests' JUnit, read by D4
├── proofs.md, mutations.json, verification.md   # lean's verify
├── gate.json, results.md, delivery.md
└── promotion.md                 # promote.py
```

Ported from ds-factory's `deploy-industrialize` and `deploy-promote` (jooaobrum).
