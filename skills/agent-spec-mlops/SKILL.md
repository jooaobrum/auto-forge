---
name: agent-spec-mlops
description: Build lane that takes a verified modeling round to production code - one config per environment, pipelines with a main() and tested logic, organized MLflow, declared monitoring, a trace and a model card - proven by validate_prod.py (D1-D10). Use when agent-spec-router hands over a `<slug>-mlops` spec from a promoted round, or the user asks to industrialize a model, write its train and score pipelines, or produce its model card.
---

# Agent Spec MLOps

The notebook becomes production code. You implement; the standard is in
[references/standard.md](references/standard.md); `validate_prod.py` checks it was followed and that production
reproduces the experiment. Every script is standard-library Python in `<skill-dir>/scripts/`. Exit codes: `0`
pass, `1` fail, `2` invalid input.

## Load points

Read `.specs/LAB.md` `## Domain skills` and load the skills listed for each point when you reach it:
**plan** (before the spec), **work** (before writing the pipelines), **verify** (before the gate). The platform
skill lives there: Databricks bundles, Unity Catalog and MLflow conventions (`data-databricks-sql`,
`ml-mlflow-log` are the examples). Nothing here needs one; with `platform: databricks` in the config the
Databricks rules (D5, the Unity Catalog registry of D10) apply.

## 1. Plan

The input is `.specs/features/<slug>-mlops/spec.md`, written by agent-spec-modeling's `deliver.py --decision
promote`: the round and its best experiment (`validate_verification.py` passed). Complete it from
[references/spec-mlops.md](references/spec-mlops.md). The user approves it (`**Approved**:` in their words);
commit, then `route.py freeze <slug>` (agent-spec-router).

## 2. Work

Port the best experiment as it is: the same data preparation, features, model and threshold.

1. `config/project.yml` with `dev`, `qa` and `prod`, each writing to its own `catalog.schema` (D1); nothing of it
   hardcoded in `src/` (D2).
2. `src/<pkg>/pipelines/<name>.py` with a `main()` that reads the config, at least `train` and `score` (D3);
   one `tests/test_<module>.py` per module (D4).
3. Deploy targets and jobs with `--env` (D5, Databricks); MLflow registry and tags (D10); monitoring declared
   (D6).
4. Run `train` in `dev`: it writes `.specs/prod/trace.json` with the commit, the tables and their versions, the
   run, the model version, the source round and its valid metric, the lock file hash and the seed (D7, D9).
5. `model_card.py` writes `MODEL_CARD.md`; a person reviews Intended use and Limitations (D8).

## 3. Verify

Run the tests with `--junitxml .specs/features/<slug>/runs/main/tests.xml`, then
`validate_prod.py <slug>` (D1-D10). It writes `gate.json` and `results.md`. Each `FAIL [Dn]` line is the next
piece of work; a `WARN [D5] skipped` says the platform rules did not apply.

## 4. Deliver

`route.py deliver <slug>` (agent-spec-router) once the gate passed, and report `delivery.md`. `git push`, a
deploy and any alias change in `qa` or `prod` need the user's explicit OK.

Ported from ds-factory's `deploy-industrialize` and `deploy-promote` (jooaobrum).
