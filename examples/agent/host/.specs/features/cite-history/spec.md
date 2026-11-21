# Cite what was read

**Profile**: agent
**Lane**: research
**Approved**: 2026-11-22 - user: "go"
**Failure mode**: reads history records but does not cite them
**Target cases**: q01

## Goal

When the agent reads history records it cites them, so the engineer can check the answer.

## Diagnosis

On q01 the agent reads every relevant record but cites a third of them - a synthesis failure, not
retrieval. Cause class: behavioral (the history skill prompt).

## Hypotheses

1. Telling it to read records in full makes it cite them.
2. Telling it to cite the id of every record it used makes it cite them.

## Cases

| Case | Question | Rubric |
| --- | --- | --- |
| q01 | Why did TOOL-123 fail PCC last week? | names the root cause and cites each record used |
| q02 | What happened on TOOL-7 yesterday? | short summary of the passdown |
| q03 | Which tool is TOOL-12? | resolves the equipment |

## Metrics

| Metric | Pass at | Guardrail | Target |
| --- | --- | --- | --- |
| cited_recall | | | +0.3 |

## Edit Scope

- prompts/history.md
