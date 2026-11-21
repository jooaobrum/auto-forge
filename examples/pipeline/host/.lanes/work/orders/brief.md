# Orders pipeline

**Profile**: pipeline
**Lane**: build
**Plan**: .specs/plan.md

## Goal

Readers of `orders` get one row per order, its latest status, refreshed daily.

## Readiness

| Item | State | Why |
| --- | --- | --- |
| Data contract | ready | contracts/orders.yaml |
| Input fixture | ready | fixture/orders_raw.csv |
| Golden rows | needs attention | two rows only |
