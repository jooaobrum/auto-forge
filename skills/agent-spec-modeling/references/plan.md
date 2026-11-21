# Plan template

The round's plan, `.specs/features/<slug>/plan.md`. `validate_plan.py <slug>` checks it (P0-P10), then
`validate_plan.py <slug> --approved` once the user approved it (A1). Every field is one line; the backlog is
filled with the user ([ideas.md](ideas.md)).

```markdown
# Round <slug> - <the question in a few words>

**Profile**: model
**Lane**: research
**Data kind**: tabular
**Approved**: <only in the user's words: YYYY-MM-DD - user: "...">

## Question
<one full sentence: what is predicted, for whom, and what good looks like>

## Target
- Definition: `.specs/LAB.md` (## Problem)

## Lessons loaded
none

## Data
- Table: `catalog.schema.table`
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

### H1 - <the idea in a few words>
- Idea: <the one change this iteration makes>
- Why: <why it should move the metric, with the evidence>
- Source: <eda | domain | lesson L-NNN | error analysis | recipe <name>>
```

- **Data kind**: `tabular` or `image`.
- **Lessons loaded**: the ids of the lessons that apply from the project's lesson store when it keeps one
  (agent-spec-lean keeps `.specs/lessons.json`), or `none`.
- **Primary**: `pr_auc`, `roc_auc`, `f1`, `macro_f1`, `accuracy`, `log_loss`, `brier`, `rmse` or `mae`;
  usually the `**Metric**` of the Problem. **Period**: `day`, `week`, `month` or `quarter`, how the
  Verification reports the OOT.
- **Max drop**: the largest valid-to-OOT drop allowed, in (0, 1], in the metric's units.

## The split lock

`.specs/split.lock` is written once per project, before any EDA ([patterns/split.md](patterns/split.md)):

```json
{
  "table": "catalog.schema.table",
  "time_col": "event_ts",
  "label_col": "label",
  "windows": {"train": ["2025-01-01", "2025-12-31"], "valid": ["2026-01-01", "2026-03-31"],
              "oot": ["2026-04-01", "2026-06-30"]},
  "counts": {"train": 52000, "valid": 13000, "oot": 12500}
}
```

The windows are ordered train < valid < oot with no overlap, and every split has rows.
