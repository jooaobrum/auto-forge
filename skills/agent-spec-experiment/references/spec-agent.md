# Spec template: agent behavior

Copy to `.specs/features/<slug>/spec.md`. Required: the fields marked *, `## Goal`, and `## Cases` (or a
`**Dataset**:` line). Everything else only when this Experiment needs it; `.specs/LAB.md` supplies the rest.

```markdown
# <title>

**Profile**: agent *
**Lane**: research *
**Approved**: <the user writes this> *
**Failure mode**: <one recurring way the agent gets Cases wrong> *
**Target cases**: q07, q12            <!-- or mark them by Failure mode in the Cases table -->
**Dataset**: <where the Cases live when not in the table below, e.g. an MLflow eval dataset>
**Budget**: 1500000                   <!-- input tokens; default from LAB.md -->
**Variants**: 3
**k**: target 3, affected 1, stable 1

## Goal

<what is different for a user when this ships> *

## Diagnosis

<what error analysis of the failing traces showed; cause class: behavioral>

## Hypotheses

1. <one change, and why it should move the Target>

## Cases

| Case | Question | Rubric | Read | Cite | Route | Failure mode | Tier |
| --- | --- | --- | --- | --- | --- | --- | --- |
| q07 | Why did TOOL-123 fail PCC last week? | names the root cause; cites the passdown | WO-881, PD-12 | PD-12 | history | reads, does not cite | capability |

<!-- Case, Question and Rubric are required. Read / Cite (record ids) when the question is about retrieval.
     Route, Failure mode, Tier only when that is evaluated. Tier: capability (majority of runs) or
     regression (every run must pass). -->

## Metrics

| Metric | Pass at | Guardrail | Target |
| --- | --- | --- | --- |
| cited_recall | 1 | | +0.3 |

<!-- One metric has a Target delta. Rows here override LAB.md. -->

## Edit Scope

- src/agent/skills/history.md
```
