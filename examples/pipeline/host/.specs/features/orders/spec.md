# Orders pipeline

**Profile**: pipeline
**Lane**: build
**Approved**: 2026-11-22 - user: "go"

## Goal

Readers of `orders` get one row per order, its latest status, refreshed daily.

## Input fixture

`fixture/orders_raw.csv` - an order with two versions, and a cancelled one.

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
