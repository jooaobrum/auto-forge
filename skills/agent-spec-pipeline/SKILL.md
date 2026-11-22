---
name: agent-spec-pipeline
description: Build lane for data pipelines (Databricks or any SQL engine) proven by a data contract and golden rows on the output. Use when agent-spec-router routes pipeline work here, or the user builds or changes a pipeline, a table or a data contract. Its plan is a lean plan plus the input fixture, the data contract and golden rows; checks and verify go to agent-spec-lean.
---

# Agent Spec Pipeline

The proof of a pipeline is its output: a **data contract** (what every row promises) and **golden rows**
(exact rows a known input must produce), checked on a small input fixture in a dev schema.

## Load points

Read `.specs/LAB.md` `## Domain skills` and load the skills listed for each point when you reach it:
**plan** (how to query the data), **work** (platform conventions), **verify** (how results are read).

## Steps

1. **Plan.** Write it from [references/plan.md](references/plan.md) (agent-spec-writer drafts it): agent-spec-lean's
   plan, plus `## Input fixture`, `## Data contract` and `## Golden rows`. When the project already has an ODCS
   file in `contracts/`, leave the `## Data contract` section out and it is read instead. The user approves it;
   `route.py freeze <slug>` runs lean's `validate_plan.py` on it.
2. **Checks, build** with agent-spec-lean. The contract gate is a proof its checks cite:
   `python3 <skill-dir>/scripts/contract.py gate <slug>`.
3. **Compile**: `python3 <skill-dir>/scripts/contract.py compile <slug> --dialect spark` (or `sqlite` locally).
   It writes `contract.sql`, one query returning `(case, violations)` per rule and golden row.
4. **Run** the pipeline on the fixture into a dev schema, run `contract.sql` there (a notebook, Genie, a SQL
   warehouse), and save its output as `.specs/features/<slug>/runs/main/contract.csv`.
5. **Gate**: `contract.py gate <slug>` - exit `1` names every rule with violations and every missing golden
   row. Fix and loop. Then `agent-spec-router`'s `route.py deliver <slug>`.
