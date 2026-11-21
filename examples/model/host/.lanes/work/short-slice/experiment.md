# Experiment: short-input slice

**Approved**: 2026-11-21 - user: "go"

## Diagnosis

Failure Mode: the `short` slice sits under the accuracy bar; its labels flip at a lower score than the
global threshold assumes. Cause class: behavioral (a parameter), so it stays in the research lane.

## Hypothesis

Lowering the threshold to 0.45 lifts `short` without dropping `long` or `rare` under 0.92.
