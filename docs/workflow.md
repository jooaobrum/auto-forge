# agent-spec: how the workflow works

## The idea in one line

Every piece of work - an app feature, a data pipeline, an ML model or an agent change - starts by telling the
agent what you want, in whatever form you have. The agent turns it into a spec, decides **what will prove it
is done**, does the work, and closes it only when **a script, not a person reading traces, says it is done**.

## What you do, what the agent does

| You | The agent |
| --- | --- |
| give a spec, design doc, problem, transcripts or just a sentence | reads it with the repo and turns it into a spec |
| answer questions when the context is not clear | grills, in short rounds, each question with a recommended answer |
| approve the spec (one line: `**Approved**: <date> - user: "<your words>"`) | plans, builds or experiments, runs every script, loops on failures |
| say whether to continue when the token budget runs out | stops and asks; records your words |
| read `delivery.md` | writes it: goal, evidence, decision, commits |

You fill no config file and run no command.

## The router decides the lane

**agent-spec-router** always runs first. It checks that the work is actionable (a goal and a way to prove
it); if not it calls **agent-spec-grilling**, and **agent-spec-writer** drafts the spec. Then it routes by the
proof:

| What can prove it | Lane | Skill |
| --- | --- | --- |
| an end-to-end test that reproduces the user's behavior, on app or code | build | **agent-spec-lean** |
| a data contract and golden rows on the pipeline's output | build | **agent-spec-pipeline** |
| only a rate over a dataset: agent behavior, model quality | research | **agent-spec-experiment** |

A research Experiment whose fix turns out to belong in code ends in `promote`; the router hands it to the
build lane.

## The project, learned once

The first time in a project the router writes `.specs/LAB.md` and confirms it with you: how the eval runs,
the glue that turns its output into results, the metrics and their bars, which files steer which tool or
skill, the default Edit Scope, and the domain skills to load. Every later piece of work inherits it; a spec
only says what differs.

## Domain skills load at fixed points

Your team's know-how - how to query the data, platform conventions, avoiding leakage, logging to MLflow -
lives in ordinary skills. Each lane loads the ones LAB.md lists at three points: **plan**, **work**,
**verify**. The repo ships two examples, `data-databricks-sql` and `ml-mlflow-log`.

## Build lane

- **App and code** - agent-spec-lean: one plan with EARS criteria and one-way doors, checks with proofs, the
  build, an independent Verifier that injects mutations. The e2e suite's JUnit decides the gate.
- **Pipeline** - agent-spec-pipeline: the spec carries a **data contract** (columns with type, required,
  unique, accepted values; rules for row count, freshness, custom SQL) and **golden rows**. A script compiles
  it into one SQL query; the agent runs the pipeline on a small fixture in a dev schema, runs the query there
  (Databricks notebook, Genie, SQL warehouse) and the gate requires zero violations.

## Research lane

agent-spec-experiment, for one Failure Mode at a time:

1. **Diagnose** from the failing traces; if the cause is in code, it goes to the build lane.
2. **Spec**: for an agent, a table of Cases - question and rubric always, the record ids to read or cite
   when it is about retrieval, route, failure mode or tier only when that is evaluated; for a model, holdout
   slices. One metric gets a Target delta; the rest are pass bars or guardrails (input tokens +15%, latency
   +20% by default).
3. **Baseline** every Case once, then up to 3 **variants**. Each variant runs only what it can affect: Target
   Cases 3 times, Cases whose baseline touched the edited files once, the rest once in the final confirm run.
4. **Gate**, per Case: a Case that passed and now fails is named; a cost guardrail breach is named; the
   Target must rise by its delta; edits outside the Edit Scope fail it. **Regression** Cases must pass every
   run; **capability** Cases pass on a majority. A capability Case that passes 3 adopted Experiments in a
   row is proposed for regression.
5. **Deliver** with a decision: adopt, reject, or promote.

## Where it lives

Every piece of work has a folder, `.specs/features/<slug>/`: the spec, the runs, the results table, the
budget log and the delivery. MLflow or the test runner keeps the raw runs; this folder keeps why the work
was done, what was tried, what the evidence said and what was decided.

## Installed anywhere

The repository is a plugin for Claude Code, VS Code and the Copilot CLI, and a Git folder for Databricks.
The scripts are standard-library Python, so they run wherever the agent has a shell. See the README.
