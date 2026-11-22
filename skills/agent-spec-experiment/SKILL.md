---
name: agent-spec-experiment
description: Research lane for agent or model behavior that only a rate over a dataset can prove - prompts, skills, tool descriptions, model parameters. Use when agent-spec-router routes research work here, or the user wants to improve an agent or model on a dataset, run an experiment, or compare variants. Runs diagnosis, baseline, variants, a per-Case gate and a decision.
---

# Agent Spec Experiment

One Experiment, one Failure Mode, one plan at `.specs/features/<slug>/plan.md`. You run every script:
`python3 <skill-dir>/scripts/experiment.py [--root <repo>] <command> <slug>`. Exit codes: `0` ok, `1` gate
fail, `2` invalid input, `3` variant cap, `4` budget spent, `5` halted (`.specs/HALT` exists).

## Load points

Read `.specs/LAB.md` `## Domain skills` and load the skills listed for each point when you reach it:
**plan** (before the plan), **work** (before running variants), **verify** (before gating).

## 1. Plan

- **Diagnose.** Read the failing traces (error analysis, 20-50 outputs), name one Failure Mode and its
  cause class. Deterministic (fixable in code) → tell agent-spec-router: it belongs in the build lane.
- **Plan.** Write it from [references/plan.md](references/plan.md) (agent-spec-writer drafts it): the
  Problem, the Behavior and its Cases, the Metrics, then the Diagnosis, the Shape of the path the Cases take,
  one hypothesis per variant and the Edit Scope. `freeze` refuses it without a Problem, a Diagnosis and
  Hypotheses. Settings come from the plan, then `.specs/LAB.md`, then defaults: 3 variants, k target 3 / affected 1 /
  stable 1, guardrails `input_tokens` +15% and `latency_ms` +20%. Propose pass bars from the Baseline numbers.
- The user writes `**Approved**:`; commit, then `experiment.py freeze <slug>`.

## 2. Work

1. Run the eval on every Case once (the `**Eval command**:` in LAB.md), write a Results file, then
   `experiment.py baseline <slug> --from <file>`.
2. Per variant: `experiment.py select <slug> --variant <name>`, edit only inside the Edit Scope, run exactly
   the Cases and k in `selection.json`, save Results files under `runs/<variant>/`. Rerun stale Baselines first.

A Results file: `{"runs":[{"case","run","metrics":{...},"touched":[...],"trace","read":[ids],"cited":[ids],"route"}]}`
(`read`, `cited`, `route` only when the Cases grade them); a CSV with a `case` column, or JUnit XML, also work.

## 3. Verify

`experiment.py gate <slug> --variant <name>`. Each `FAIL` line is the next piece of work; loop until it
passes or `select` exits `3`. Before delivering: `gate --confirm` (runs the Stable Cases once).
Regression Cases pass only if every run passes; capability Cases pass on a majority.

When `select` or `budget` exits `4`, stop and ask the user whether to continue; on their yes,
`experiment.py budget <slug> --add <tokens> --user "<their words>"`.

## 4. Deliver

`experiment.py deliver <slug> --decision adopt|promote|reject`, then report `delivery.md`. `promote` writes
`.specs/features/<slug>-build/plan.md`, a seed agent-spec-writer completes as a lean plan: hand it to
agent-spec-router. Cases listed under "Proposed for
regression" get `regression` in their Tier once the user agrees.
