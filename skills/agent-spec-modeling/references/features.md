# Features

The catalog of ideas by data type is in [recipes/feature-ideas.md](recipes/feature-ideas.md). The
recipes by kind of problem are in [recipes-library.md](recipes-library.md) (experimenta-ml) and in
`recipes/`. A feature table is a pipeline: agent-spec-pipeline proves it.

## Priority

1. **From the domain and the EDA** (the backlog, see [ideas.md](ideas.md)): they have a mechanism and
   pay off most.
2. **Group-relative:** when there is a batch, machine, customer or session, the abnormal is usually
   relative (`x - group_median`, `x / group_mean`, rank in the group), not the absolute value.
3. **Temporal:** lags, windows looking back, time since the last event, position in the sequence.
4. **Informative missingness:** a missing indicator when the EDA shows a different target rate.
5. **Interactions:** only between variables that already showed signal, pulled by the domain.
6. **Generic in bulk** (all ratios, all pairs): last, and with selection inside the pipeline.

## Rules

- Always causal: features computed on the frame ordered by time, only looking back (CHK-LEAK-003).
- What learns from data is fitted on train, inside the pipeline.
- One family per iteration, to know what worked.
- Every feature must exist at prediction time (the `Prediction time` field of the `## Problem` in
  `.specs/LAB.md`).
