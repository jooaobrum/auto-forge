# Orders pipeline

**Profile**: pipeline
**Lane**: build
**Approved**: 2026-11-22 - user: "go"

## Problem

Readers of `orders` - the sales dashboard and the finance export - get one row per version of an order: an
order updated twice is counted three times and shows every status it ever had. The source gives no count.

When this ships, readers get one row per order with its latest status, refreshed daily.

## Shape

This reuses the raw extract ingestion already lands, instead of reading the source system again. The rule
that keeps the latest version runs in `pipeline.py`, which the fixture run executes end to end.

1. in: `orders_raw` (exists) - every version of every order, with its `version`
2. `pipeline.py` (new) - keeps the highest `version` per `order_id`
3. out: `orders` (door 1), replaced on each run with `loaded_at` set to the run time

```mermaid
sequenceDiagram
    participant R as orders_raw
    participant P as pipeline.py
    participant O as orders
    R->>P: 1. every version of every order
    P->>P: 2. latest version per order_id
    P->>O: 3. replace the table
```

**Changes underneath**

| Front | What changes |
| --- | --- |
| domain | an order meant one version of it, now means the order - the dashboard counts rows |
| stored data | nothing to migrate: the table is replaced on each run |
| readers | the sales dashboard and the finance export read one row per order |

```mermaid
erDiagram
    orders ||--|{ orders_raw : "latest version of"
```

New: `orders`, one row per `order_id` (door 1).

## Surface

None - nothing consumed outside through a route; the `orders` table readers consume is held by
`## Data contract`.

## Landing

| One-way door | Literal shape | Alternative rejected |
| --- | --- | --- |
| `orders` table, one row per order | `orders(order_id integer unique, status string, loaded_at timestamp)`, replaced on each run | a view over `orders_raw`: every reader pays the dedup, and the contract cannot be checked on a stored output |

- Nothing else in this change is hard to reverse

## Criteria

### S1: one row per order (P1)

Readers see each order once, with its latest status.

**Acceptance Criteria**

1. WHEN the pipeline runs on `fixture/orders_raw.csv` THEN `orders` SHALL hold exactly one row per `order_id`
   - order 1 with versions 1 and 2 → one row; order 3 → one row
2. WHEN an order has several versions THEN the pipeline SHALL keep the one with the highest `version`
   - order 1: open in version 1, closed in version 2 → `closed`
3. WHEN an order was cancelled THEN `orders` SHALL show it with status `cancelled`
   - order 3 → `cancelled`

## Input fixture

`fixture/orders_raw.csv` - an order with two versions (open, then closed), and a cancelled one.

## Data contract

### orders

| Column | Type | Required | Unique | Accepted values |
| --- | --- | --- | --- | --- |
| order_id | integer | yes | yes | |
| status | string | yes | | open, closed, cancelled |
| loaded_at | timestamp | | | |

- rowCount between 1 and 1000
- freshness loaded_at 24h

## Golden rows

| order_id | status |
| --- | --- |
| 1 | closed |
| 3 | cancelled |

## Out of scope

| Excluded | Why |
| --- | --- |
| a history of status changes | readers asked for the latest status only |

## Assumptions

| Assumption | Chosen default | Rationale | Confirmed? |
| --- | --- | --- | --- |
| which version is the latest | the highest `version` | `loaded_at` of the raw rows is the ingestion time, not the change time | n |

**Open questions:** none - all resolved or logged above.

## Differences from the source

None - the product matches the source

## Sources

- the ticket asking for one row per order - binding - the grain and the readers
