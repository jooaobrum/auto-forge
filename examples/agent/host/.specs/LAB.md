# LAB

**Eval command**: `python agent.py --selection <selection.json> --out <file>`
**Results glue**: none needed - agent.py writes Results files
**Budget**: 2000000

## Metrics

| Metric | Pass at | Guardrail | Target |
| --- | --- | --- | --- |
| cited_recall | 0.8 | | |
| correctness | 1 | | |
| input_tokens | | +15% | |

## Surface

| Item | Paths | Affects all |
| --- | --- | --- |
| skill:history | prompts/history.md | |
| tool:resolve_equipment | tools/resolve_equipment.py | |

## Edit Scope

- prompts/
