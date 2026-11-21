# Round secom - final test failure from the sensors

**Profile**: model
**Lane**: research
**Data kind**: tabular
**Approved**: 2026-11-20 - user: "approved, 10 iterations"

## Question
Do the sensor signals predict a lot's failure before the final test, with PR-AUC above the baseline in future periods?

## Target
- Definition: `.specs/LAB.md` (## Problem)

## Lessons loaded
none (no lesson applies)

## Data
- Table: `workspace.curated.secom`
- Lock: `.specs/split.lock`

## Metric
- Primary: pr_auc
- Min gain: 0.01
- Period: week

## Budget
- Iterations: 10

## Max drop
- Valid to OOT: 0.30

## Backlog

### H1 - Nothing changes (noise control)
- Idea: run the baseline with one more comment
- Why: measures the evaluator's noise; the gain must be zero
- Source: domain

### H2 - Use sensor s000
- Idea: take s000 out of the baseline's DROP list
- Why: the EDA showed a univariate AUC of 0.82 on s000, the highest of the sensors
- Source: eda
