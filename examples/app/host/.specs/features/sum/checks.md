# Sum command - checks

Mutations: 2
Build: none - a single-module script with no build, type check or lint configured
Plan: `.specs/features/sum/plan.md`

## Checks

### S1 - a user sums numbers

**C1** - Running the command with `2 3` prints `5` (AC 1)
Proof: `python3 -m pytest e2e/test_cli.py -k test_user_sums_two_numbers`

**C2** - Running the command with no numbers prints `0` (AC 2)
Proof: `python3 -m pytest e2e/test_cli.py -k test_user_sums_nothing`

## Coverage

| Set (size) | Member -> proof | Unproven |
| --- | --- | --- |
| argument counts (2) | some numbers C1 · none C2 | - |

- No check claims more than the single case its proof exercises

## Swept

- validation: n/a - non-integers are out of scope (plan, Out of scope)
- failure modes: n/a - the command has no dependency that can fail
- idempotency: n/a - nothing is written
- authorization: n/a - a local command with no users
- concurrency: n/a - nothing is shared
- data lifecycle: n/a - nothing is stored
- dependency failure: n/a - no dependency
- state transitions: n/a - no state
- observability: n/a - the output is the observation

## Handoff
