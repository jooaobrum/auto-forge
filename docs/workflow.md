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

## Data science end to end (planned)

**Status: planned, not built** (AD-030). Today the router and the experiment lane exist, and the experiment
lane needs a model, an eval and a frozen holdout already in place. The design below takes a model from a
problem to production. It adds two lanes, a `route.py problem` command and a promotion script, each one
SKILL.md plus standard-library scripts. The rules come from the gates of ds-factory's `exp-hillclimb` and
`deploy-industrialize`, which become references inside the two lanes, not skills of their own.

```
  "predict which customers churn in the next 30 days"
        |
  1. ROUTER (exists) -- interview --> LAB.md gains ## Problem
        |     [you] confirm the Problem          gate: route.py problem
        v
  2. MODELING lane (planned): split lock -> EDA -> baseline -> rounds, one change each
        |     gate: validate_plan   [you] approve the plan
        |     gate: validate_round  gate: validate_verification (PASS on OOT)
        v     delivery: promote
  3. MLOPS lane (planned): notebook -> production code, tests, organized MLflow
        |     gate: validate_prod
        v
  4. PROMOTION (planned): challenger vs champion, slice by slice
        |     gate: promotion script   [you] OK the alias swap
        v
  5. AFTER: point fixes -> EXPERIMENT lane (exists)
```

| Step | Gate | Type | What it checks | Status |
| --- | --- | --- | --- | --- |
| 1 Problem | confirm the Problem | human | target, label rule, prediction time, cost of FP and FN, metric | planned |
| 1 Problem | `route.py problem` | script | `## Problem` holds all five and your confirmation; the label rule, run in SQL, reproduces the label | planned |
| 2 Modeling | `validate_plan` P0-P10 | script | the plan is complete and the split is locked (below) | planned |
| 2 Modeling | approve the plan | human | `**Approved**:` in your words (rule A1) | planned |
| 2 Modeling | `validate_round` R0-R11 | script | the round followed the pattern (below) | planned |
| 2 Modeling | `validate_verification` V0-V7 | script | a fresh context judged the best experiment on OOT: PASS | planned |
| 3 MLOps | `validate_prod` D1-D10 | script | the production standard (below) | planned |
| 4 Promotion | promotion script | script | per slice: no slice regresses, target gain with a CI above zero | planned |
| 4 Promotion | OK the alias swap | human | challenger becomes champion, your words recorded | planned |
| 5 After | `experiment.py gate` | script | baseline, at most 3 variants, per-Case gate with cost limits | exists |
| any | `.specs/HALT` | script | when the file exists, every script exits non-zero before doing anything | planned, optional |

**1. Problem.** No separate domain skill: the router interviews you and writes `## Problem` into LAB.md.
The router sends a model with no champion, or a new round of its backlog, to modeling; a Failure Mode of a
model already in production, judged on holdout slices, to the experiment lane.

**2. Modeling lane** (`skills/agent-spec-modeling/`, from `exp-hillclimb`). The split is locked first, EDA
reads only train, the baseline is iteration one, and every later iteration changes one thing.

- **Plan.** P0 the plan exists. P1 a Profile (`tabular` or `image`). P2 every section is there and filled:
  Question, Target, Lessons loaded, Data, Metric, Budget, Max drop, Backlog. P3 the question is a full
  sentence. P4 the target has a business definition, label rule, prediction time, exclusions and your
  confirmation. P5 the lessons loaded, or "none". P6 the table as `catalog.schema.table` and a split lock:
  train, valid and OOT time windows in order with no overlap, each with a positive row count. P7 a primary
  metric from a fixed list, a minimum gain of 0 or more, a reporting period. P8 an iteration budget. P9 the
  largest valid-to-OOT drop allowed, in (0, 1]. P10 a backlog of hypotheses `H<n>`, each with an idea, a why
  and a source.
- **Round.** R0 the plan validates as approved. R1 a ledger with iterations. R2 the first feasible iteration
  is the kept baseline. R3 within the iteration budget. R4 each iteration tests the baseline, a backlog
  hypothesis or an error-analysis finding. R5 its code is recoverable and it left an error analysis. R6
  every kept gain reaches the minimum gain with a CI above zero, and the best is the last kept. R7 an MLflow
  run per iteration (unless offline). R8 the report's sections are filled. R9 the required leakage checks
  are reported. R10 the status agrees with the checks: a failed check means infeasible. R11 the code never
  references the OOT period.
- **Verification.** V0 the round validates. V1 a named Verifier (fresh context or subagent; self-verified
  only warns) at a commit sha. V2 it judges the ledger's best. V3 the OOT metric per period. V4 the
  valid-to-OOT drop is stated right and within P9. V5 both mutations killed, or n/a with a reason. V6 every
  finding closed by a commit. V7 the verdict is PASS.

**3. MLOps lane** (`skills/agent-spec-mlops/`, from `deploy-industrialize`), a build lane: the notebook
becomes production code, classes or functions as the team prefers, with tests and organized MLflow.

- D1 one config with `dev`, `qa` and `prod`, each writing to its own `catalog.schema`. D2 no write target or
  input table hardcoded in `src/`. D3 every pipeline in the config, at least `train` and `score`, exists with
  a `main()` that loads the config. D4 every module has a test file, and the tests pass. D5 deploy targets
  `dev`, `qa`, `prod`, and jobs pass `--env`. D6 monitoring is declared: inference table, metrics, drift
  baseline and threshold, schedule, alert. D7 a trace names a verified round and its best experiment, and
  production reproduces its valid metric within a tolerance. D8 a model card with its sections, carrying the
  trace: model and version, commit, run, round, every table read with its version. D9 dependencies locked,
  the lock's hash and the seed recorded. D10 MLflow standard: registry, required tags, model named under the
  environment's `catalog.schema`.
- Databricks and MLflow live in an optional platform skill that LAB.md lists, as `data-databricks-sql` and
  `ml-mlflow-log` do today; the platform-specific rules (D5, D10) come with it.

**4. Promotion.** A new script reuses the experiment lane's gate: the Cases are slices of the recent period,
the Baseline is the champion, the Variant is the challenger. No slice may regress, and the target gain needs
a CI above zero (today's gate checks only the mean delta; the CI is new). Then you OK the alias swap.

**5. After.** Point fixes go to the experiment lane as they do today.

Out of scope for now: proving drift alerts fire (D6 only checks monitoring is declared), retraining and
online serving.

## Where it lives

Every piece of work has a folder, `.specs/features/<slug>/`: the spec, the runs, the results table, the
budget log and the delivery. MLflow or the test runner keeps the raw runs; this folder keeps why the work
was done, what was tried, what the evidence said and what was decided.

## Installed anywhere

The repository is a plugin for Claude Code, VS Code and the Copilot CLI, and a Git folder for Databricks.
The scripts are standard-library Python, so they run wherever the agent has a shell. See the README.
