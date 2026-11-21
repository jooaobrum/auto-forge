# LESSONS - auto-maintained by scripts/lessons.py

> Machine-owned. Do NOT hand-edit. Changes are overwritten on the next `lessons.py` write.
> Canonical state lives in `.specs/lessons.json`. Edit lessons only via the script.
> promote_threshold=2 distinct features · window_days=45 · quarantine_threshold=2

## Confirmed (load these at Plan/Checks)

Corroborated across multiple features. Safe to apply as guidance.

_none_

## Candidates (under observation - do NOT load as guidance yet)

Seen once or not yet corroborated. Tracked, not trusted.

### L-001 - Test a range rule at both bounds and one past each, not only well inside it
- signal: `surviving_mutant` · recurrence: 1 feature(s) · scope: `contract` · harmful: 0
- features: mvp-lanes
- evidence: src/lanes/contract.py:82 (contract)
- last seen: 2026-11-21T10:45:21Z

### L-002 - When a rule needs at least one item to count, test an input where every item is excluded
- signal: `surviving_mutant` · recurrence: 1 feature(s) · scope: `results` · harmful: 0
- features: mvp-lanes
- evidence: src/lanes/results.py:67 (results)
- last seen: 2026-11-21T10:45:21Z

### L-003 - When an exemption names one owner's folder, put a sibling owner's file in the test input
- signal: `surviving_mutant` · recurrence: 1 feature(s) · scope: `scope` · harmful: 0
- features: mvp-lanes
- evidence: src/lanes/gate.py:58 (scope)
- last seen: 2026-11-21T10:45:21Z

### L-004 - Read git path lists with -z and --no-renames; test a moved file and a path with a space
- signal: `ac_gap` · recurrence: 1 feature(s) · scope: `scope` · harmful: 0
- features: mvp-lanes
- evidence: src/lanes/gate.py:56 (scope)
- last seen: 2026-11-21T10:45:21Z

### L-005 - Quote values read from CSV as text; test a value with a leading zero
- signal: `ac_gap` · recurrence: 1 feature(s) · scope: `contract` · harmful: 0
- features: mvp-lanes
- evidence: src/lanes/contract.py:138 (contract)
- last seen: 2026-11-21T10:45:21Z

### L-006 - Prove a staleness rule by changing the real input it hashes, not by overwriting the stored hash
- signal: `spec_precision_gap` · recurrence: 1 feature(s) · scope: `select` · harmful: 0
- features: mvp-lanes
- evidence: tests/test_select.py:46 (select)
- last seen: 2026-11-21T10:45:21Z

### L-007 - Prove a mean over a set with at least two members whose values straddle the bound
- signal: `spec_precision_gap` · recurrence: 1 feature(s) · scope: `gate` · harmful: 0
- features: mvp-lanes
- evidence: tests/test_gate.py:136 (gate)
- last seen: 2026-11-21T10:45:22Z

## Quarantined (failed when applied - ignore)

A confirmed lesson that recurred alongside failure. Kept for the maintainer to review.

_none_
