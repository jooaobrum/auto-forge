# Spec template: a model to production

`.specs/features/<slug>-mlops/spec.md`. `deliver.py --decision promote` of agent-spec-modeling writes its
first lines; complete the rest with the user.

```markdown
# churn - to production

**Profile**: model
**Lane**: build
**Round**: churn
**Experiment**: dfdee50fa862a2c3
**Approved**: <only in the user's words: YYYY-MM-DD - user: "...">

## Goal

Experiment `dfdee50fa862a2c3` of round `churn` runs in production to the team's standard and reproduces its
valid metric.

## Proof

`validate_prod.py churn-mlops` (D1-D10).

## Decisions

- Package: `src/churn/`; pipelines: features, train, score, monitor
- Reproduction tolerance on the valid metric: 0.01
- Platform: databricks (or none)
```
