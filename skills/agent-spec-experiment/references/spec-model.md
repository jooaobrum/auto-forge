# Spec template: model

Copy to `.specs/features/<slug>/spec.md`. A Case is a slice of the frozen holdout; k is the number of seeds.
Required: the fields marked `<!-- required -->`, `## Goal`, `## Cases`, and a Target in `## Metrics`.

```markdown
# <title>

**Profile**: model <!-- required -->
**Lane**: research <!-- required -->
**Approved**: <the user writes this> <!-- required -->
**Failure mode**: <the slice or behavior that falls short> <!-- required -->
**Target cases**: short <!-- required -->
**k**: target 3, affected 3, stable 1

## Goal

<what is different for a user when this ships> <!-- required -->

## Diagnosis

<what the per-slice error analysis showed>

## Cases

| Case | Question | Rubric | Tier |
| --- | --- | --- | --- |
| short | inputs under 20 tokens | accuracy at the bar | capability |
| long | inputs of 20 tokens or more | accuracy at the bar | regression |

## Metrics

| Metric | Pass at | Guardrail | Target |
| --- | --- | --- | --- |
| accuracy | 0.92 | | +0.03 |
| train_seconds | | +20% | |

## Edit Scope

- model/config.json
```

Hygiene the work load point should bring (a domain skill such as `ml-mlflow-log`): the holdout stays frozen,
no row of it reaches training, seeds are fixed, one change per variant.
