---
name: agent-spec-router
description: Use first for any piece of work - an app feature, a data pipeline, an ML model or an agent change - whether the user brings a spec, a design doc, a problem or only context. Decides whether the work is actionable and which lane proves it, then hands it to agent-spec-lean (app and code), agent-spec-pipeline (data) or agent-spec-experiment (agent or model behavior judged on a dataset). Also use when a delivery ends in "promote".
---

# Agent Spec Router

The one entry. The user talks and gives context; you do everything else, scripts included. Vocabulary:
**Profile** (`app`, `pipeline`, `model`, `agent`), **lane** (`build`, `research`), **spec** (the one document of
a piece of work, `.specs/features/<slug>/spec.md`).

## 1. Know the project

Read `.specs/LAB.md`. When it does not exist, write it now, from the repo and by asking only what the repo
does not answer, and confirm each part with the user:

```markdown
# LAB

**Eval command**: <how the dataset eval runs, e.g. `uv run python -m minds.eval --cases {cases} --k {k}`>
**Results glue**: <script that writes Results files, or "none needed">
**Budget**: <default input-token budget per Experiment, or "none">

## Metrics

| Metric | Pass at | Guardrail | Target |
| --- | --- | --- | --- |
| cited_recall | 0.8 | | |
| input_tokens | | +15% | |

## Surface

| Item | Paths | Affects all |
| --- | --- | --- |
| skill:history | src/agent/skills/history.md | |
| system_prompt | src/agent/prompts.py | yes |

## Edit Scope

- src/agent/skills/

## Domain skills

| Load point | Skill |
| --- | --- |
| plan | data-databricks-sql |
| verify | ml-mlflow-log |
```

Pick the domain skills from the installed skills by their descriptions (load points: **plan**, **work**,
**verify**). LAB.md is yours to keep current; the user never edits it.

## 2. Is the context actionable?

It is actionable when you can state the goal (what changes for a user) and how it will be proven. When it
names no goal or no way to prove it, call **agent-spec-grilling** before routing. When there is context but no
spec, call **agent-spec-writer** to draft one from the lane's template.

## 3. Route by the proof

| What can prove it | Lane | Hand to |
| --- | --- | --- |
| an end-to-end test reproducing the user's behavior, on app or code | build | **agent-spec-lean** |
| a data contract and golden rows on the pipeline's output | build | **agent-spec-pipeline** |
| only a rate over a dataset: agent behavior, model quality | research | **agent-spec-experiment** |

Write the Profile and the lane into the spec (`**Profile**:`, `**Lane**:`) and hand over.

## 4. Take back a promote

When an Experiment's delivery says `promote`, its fix belongs in code: read `.specs/features/<slug>-build/spec.md`
and route it to the build lane. Every hand-off between lanes passes through here.

## Build-lane bookkeeping

For build work, run `python3 <skill-dir>/scripts/route.py freeze <slug>` once the spec has its
`**Approved**:` line. For an app, judge the e2e JUnit with `route.py junit <slug>` (results in
`runs/main/*.xml`). Close with `route.py deliver <slug>` once a gate passed and report `delivery.md`.
