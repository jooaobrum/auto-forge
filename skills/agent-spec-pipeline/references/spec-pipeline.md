# Spec template: pipeline

Copy to `.specs/features/<slug>/spec.md`. Required: the fields marked *, `## Goal`, and either
`## Data contract` or an ODCS file in `contracts/`.

```markdown
# <title>

**Profile**: pipeline *
**Lane**: build *
**Approved**: <the user writes this> *

## Goal

<what readers of the output get when this ships> *

## Input fixture

<path of the small versioned input, and what it covers>

## Data contract

### orders

**Table**: dev.sales.orders

| Column | Type | Required | Unique | Accepted values |
| --- | --- | --- | --- | --- |
| order_id | integer | yes | yes | |
| status | string | yes | | open, closed, cancelled |
| loaded_at | timestamp | | | |

- rowCount between 1 and 1000
- freshness loaded_at 24h
- sql no_open_without_date: SELECT COUNT(*) FROM dev.sales.orders WHERE status = 'open' AND loaded_at IS NULL

## Golden rows

| order_id | status |
| --- | --- |
| 1 | closed |
| 3 | cancelled |
```

Rules: `rowCount between <a> and <b>`, `freshness <column> <hours>h`, `sql <name>: <query returning a
violation count>`. Golden rows check the first dataset; values compare as text.
