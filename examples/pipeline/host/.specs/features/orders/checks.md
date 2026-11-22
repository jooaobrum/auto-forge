# Orders pipeline - checks

Mutations: 2
Build: none - a single script with no build, type check or lint configured
Plan: `.specs/features/orders/plan.md`

## Checks

### S1 - one row per order

**C1** - On the fixture, `orders` holds exactly one row per `order_id`: 1, 2 and 3 (AC 1)
Proof: `python3 -m pytest tests/test_pipeline.py -k test_one_row_per_order`

**C2** - Order 1, open in version 1 and closed in version 2, is `closed` (AC 2)
Proof: `python3 -m pytest tests/test_pipeline.py -k test_latest_version_wins`

**C3** - Order 3 is `cancelled` (AC 3)
Proof: `python3 -m pytest tests/test_pipeline.py -k test_cancelled_order_kept`

**C4** - The output meets the Data contract and the Golden rows: 0 violations on every rule
Proof: `bash proofs/contract.sh`

## Coverage

| Set (size) | Member -> proof | Unproven |
| --- | --- | --- |
| fixture orders (3) | 1 C1, C2 · 2 C1 · 3 C1, C3 | - |
| contract cases (8) | order_id required C4 · order_id unique C4 · status required C4 · status accepted values C4 · rowCount C4 · freshness C4 · golden row 1 C4 · golden row 3 C4 | - |

- No other check claims more than the single case its proof exercises

## Swept

- validation: C4
- failure modes: n/a - a malformed raw file fails the run before writing, as the script does today
- idempotency: C1
- authorization: n/a - the dev schema has no per-user access in this pipeline
- concurrency: n/a - one run at a time, scheduled daily
- data lifecycle: n/a - the table is replaced on each run
- dependency failure: n/a - no dependency beyond the raw file
- state transitions: n/a - no state machine
- observability: C4

## Handoff
