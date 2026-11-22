---
name: agent-spec-pipeline
description: Build lane for data pipelines (Databricks or any SQL engine) proven by a data contract and golden rows on the output, run on a small input fixture. Use when agent-spec-router routes pipeline work here, or the user builds or changes a pipeline, a table or a data contract. agent-spec-lean's flow - plan, checks, build, verify with an independent Verifier - where the contract gate is one of the proofs.
---

# Agent Spec Pipeline

agent-spec-lean, for a pipeline. The proof of a pipeline is its output: a **data contract** (what every row
promises) and **golden rows** (exact rows a known input must produce), checked on a small input fixture in a
dev schema. Everything else is lean's: the plan, the checks, the build, the Verifier.

```
┌──────┐   ┌────────┐   ┌───────┐   ┌────────┐   ┌─────────┐
│ PLAN │ → │ CHECKS │ → │ BUILD │ → │ VERIFY │ → │ DELIVER │
└──────┘   └────────┘   └───────┘   └────────┘   └─────────┘
 lean plan   contract     run on      proofs +     route.py
 + contract  is a proof   fixture     Verifier     deliver
```

## Rules

agent-spec-lean's rules hold, all of them ([SKILL.md](../agent-spec-lean/SKILL.md)). What the pipeline adds:

1. **The output is the proof.** Each criterion is proven on the input fixture, by a test that runs the
   pipeline as it runs in production (file or table in, table out) - not by a test of a helper.
2. **The contract gate is a check.** One check's proof runs the pipeline on the fixture, the compiled
   `contract.sql` on its output, and `contract.py gate`: every rule and golden row at 0 violations.
3. **The contract and the golden rows are fixed at approval**, like the checks: changing a rule or a golden row
   to make the gate pass is renegotiation with the user.
4. **Never against production.** The fixture runs into a dev schema; a run on production data, a backfill or a
   schema change in production needs the user's explicit OK.

## Load points

Read `.specs/LAB.md` `## Domain skills` and load the skills listed for each point when you reach it:
**plan** (how to query the data), **work** (platform conventions), **verify** (how results are read).

## Phases

| Phase | What it produces | Reference |
| --- | --- | --- |
| Plan | lean's plan plus `## Input fixture`, `## Data contract`, `## Golden rows`; approved by the user | [plan.md](references/plan.md), then lean's [plan.md](../agent-spec-lean/references/plan.md) |
| Checks | one check per criterion, proven on the fixture, plus the contract gate as a check | lean's [checks.md](../agent-spec-lean/references/checks.md) |
| Build | the pipeline, its tests, the contract compiled and run on the fixture | lean's [build.md](../agent-spec-lean/references/build.md) |
| Verify | `check_proofs.py`, then the Verifier: mutations in the rules that decide the output | lean's [verify.md](../agent-spec-lean/references/verify.md) |
| Deliver | `route.py deliver` refuses until lean's `validate_verification.py` passes | agent-spec-router |

Decisions, lessons and resuming: lean's [memory.md](../agent-spec-lean/references/memory.md).

## The contract

- **Compile**: `python3 <skill-dir>/scripts/contract.py compile <slug> --dialect spark` (or `sqlite` locally)
  writes `contract.sql`, one query returning `(case, violations)` per rule and golden row. When the project
  keeps an ODCS file in `contracts/`, the plan leaves `## Data contract` out and that file is read instead.
- **Run** the pipeline on the fixture into a dev schema, run `contract.sql` there (a notebook, Genie, a SQL
  warehouse), and save its output as `.specs/features/<slug>/runs/main/contract.csv`.
- **Gate**: `contract.py gate <slug>` - exit `1` names every rule with violations and every missing golden row.

The contract check's proof is one command that does the three, so `check_proofs.py` reruns it at `HEAD`.

## Scripts

| When | Command |
| --- | --- |
| The user approved the plan, committed | `route.py freeze <slug>` (runs lean's `validate_plan.py`) |
| Before building | lean's `validate_checks.py <slug>` |
| After building | `contract.py compile`, the run, `contract.py gate <slug>` |
| Before the Verifier, and after the fix | lean's `check_proofs.py <slug> [--mutations <file>]` |
| Before declaring done | lean's `validate_verification.py <slug>`, then `route.py deliver <slug>` |

## Artifacts

```
.specs/features/<slug>/
├── plan.md                      # lean's plan + Input fixture, Data contract, Golden rows
├── checks.md                    # lean's checks; one of them is the contract gate
├── contract.sql, contract.json  # compiled from the plan's contract
├── runs/main/contract.csv       # the contract's output on the fixture
├── proofs.md, mutations.json, verification.md   # lean's verify
└── gate.json, results.md, delivery.md
```
