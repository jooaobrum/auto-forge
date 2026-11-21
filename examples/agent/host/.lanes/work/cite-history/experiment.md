# Experiment: cite what was read

**Approved**: 2026-11-21 - user: "go"

## Diagnosis

Failure Mode: on q01 the agent reads every relevant record but cites a third of them - a synthesis
failure, not retrieval. Cause class: behavioral (the history skill prompt).

## Hypotheses

1. Telling it to read records in full makes it cite them.
2. Telling it to cite the id of every record it used makes it cite them.
