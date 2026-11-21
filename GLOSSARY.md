# auto-forge

Skills that take any piece of work - app, pipeline, model or agent - from whatever context the user gives to delivery, routing it to the lane whose proof can close it.

## Entry

**Router**:
The one skill every piece of work enters through; it decides whether the work is actionable and which lane proves it.
_Avoid_: dispatcher, orchestrator

**Spec**:
The one document of a piece of work, holding its goal, how it is proven and every setting that differs from LAB.md.
_Avoid_: brief, config, experiment.json

**LAB.md**:
The project's facts learned once by the agent: how the eval runs, the results glue, metrics, surface, default Edit Scope, domain skills.
_Avoid_: lanes.json, settings

**Domain skill**:
A team skill holding know-how a lane needs (how to query the data, platform conventions, logging), loaded at a Load point.

**Load point**:
One of the three moments a lane loads domain skills: plan, work, verify.

**Delivery**:
The last record of a piece of work: the goal, the gate evidence and, for an Experiment, its Decision.

## Lanes

**Lane**:
The route a piece of work takes, chosen by what can prove it is done.
_Avoid_: track, mode, flow

**Build lane**:
The lane for work an end-to-end test can prove, reproducing the user's behavior as closely as possible.
_Avoid_: dev lane, deterministic lane

**Research lane**:
The lane for work only a rate over a dataset can prove: agent behavior and data science models.
_Avoid_: tuning lane, eval lane, experimentation lane

**Profile**:
The declared kind of thing being built - app, pipeline, model or agent - with its default lane and the obligations its plan must hold.
_Avoid_: type, template, stack

**Build Change**:
One unit of work in the build lane, ending in merged code.
_Avoid_: feature, ticket, task

**Experiment**:
One unit of work in the research lane, ending in a Decision.
_Avoid_: tuning, iteration, attempt, run

## Experiment

**Diagnosis**:
The read-only first stage of an Experiment, which names the Failure Mode, its cause class and the proposed Edit Scope.
_Avoid_: investigation, analysis

**Failure Mode**:
A named, recurring way the agent or model gets cases wrong.
_Avoid_: bug, error category

**Cause class**:
Whether a Failure Mode is deterministic (fixable in code, so it goes to the build lane) or behavioral (fixable only on the Behavioral Surface).

**Behavioral Surface**:
The parts of an agent that steer it without being code logic: prompts, skill texts and tool descriptions.
_Avoid_: prompt layer, config

**Edit Scope**:
The paths an Experiment is allowed to change, approved by the human and enforced, not requested.
_Avoid_: allowlist, blast radius

**Variant**:
One candidate change inside an Experiment's Edit Scope.
_Avoid_: attempt, try, candidate

**Decision**:
How an Experiment ends: adopt (the Variant merges), promote (a prototyped code change becomes a Build Change) or reject.

## Measurement

**Case**:
The smallest unit a gate judges: an agent question with its expected outcome, a holdout slice of a model, or one data contract rule.
_Avoid_: sample, example, test

**Target Metric**:
The one metric an Experiment is trying to move.
_Avoid_: primary metric, objective

**Guardrail**:
A metric with a budget that a Variant must not break, checked per Case against the baseline.
_Avoid_: secondary metric, constraint

**Baseline**:
The stored per-Case result of the current agent, valid until the code behind that Case changes.

**Capability Case**:
A Case that passes on a majority of its runs; it graduates after passing three adopted Experiments in a row.

**Regression Case**:
A Case that must pass every one of its runs.

**Target Cases**:
The Cases that show the Failure Mode.

**Affected Cases**:
Cases whose baseline trace touched something inside the Edit Scope.

**Stable Cases**:
Cases neither targeted nor affected, run only in the confirm run.

**Cited recall**:
The share of expected record IDs the final answer cites.

**Read recall**:
The share of expected record IDs the agent read during the turn; read but not cited is a synthesis failure, never read is a retrieval failure.

## Files

**Results file**:
The record of runs in the one shape every gate reads - per Case and run: metrics, the surface it touched, a trace reference - written by whoever ran the work.
_Avoid_: adapter, report, output

**Data contract**:
The schema and quality rules a pipeline's output dataset promises its readers, each rule a Case.
_Avoid_: expectations, schema file, validation
