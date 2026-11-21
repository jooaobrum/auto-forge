# LAB

**Eval command**: `python model.py --selection <selection.json> --out <file>`
**Results glue**: none needed - model.py writes Results files

## Metrics

| Metric | Pass at | Guardrail | Target |
| --- | --- | --- | --- |
| accuracy | 0.92 | | |
| train_seconds | | +20% | |

## Surface

| Item | Paths | Affects all |
| --- | --- | --- |
| param:threshold | model/config.json | yes |

## Edit Scope

- model/config.json
