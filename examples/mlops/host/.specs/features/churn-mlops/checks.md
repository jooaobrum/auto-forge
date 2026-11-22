# churn - to production - checks

Mutations: 2
Build: none - the package has no build, type check or lint configured; its tests run in C5 and C6
Plan: `.specs/features/churn-mlops/plan.md`

## Checks

### S1 - production reproduces the experiment

**C1** - `train --env dev` writes `.specs/prod/trace.json` whose valid accuracy is within 0.01 of 0.75, from round `churn`, experiment `c0ffee0123456789` (AC 1, D7)
Proof: `bash proofs/prod.sh`

**C2** - The trace lists every table read with its version, the commit and the hash of `uv.lock`, and `MODEL_CARD.md` carries them (AC 2, D8, D9)
Proof: `bash proofs/prod.sh`

**C3** - `dev`, `qa` and `prod` each write to their own `catalog.schema`, and `src/` names none of them (AC 3, D1, D2)
Proof: `bash proofs/prod.sh`

**C4** - Every job calls its pipeline with `--env` (AC 4, D5)
Proof: `bash proofs/prod.sh`

**C5** - An account with 2 months of tenure and 5 support calls scores `1.0`; one with 30 months and no calls is not flagged at 0.5 (AC 5)
Proof: `python3 -m pytest tests/test_model.py -k test_short_tenure_with_calls_is_risky`

**C6** - On two labelled accounts with one hit, accuracy is `0.5` (AC 5)
Proof: `python3 -m pytest tests/test_model.py -k test_accuracy`

## Coverage

| Set (size) | Member -> proof | Unproven |
| --- | --- | --- |
| environments (3) | dev C3 · qa C3 · prod C3 | - |
| pipelines in the config (2) | train C1 · score C4 | - |
| standard rules this plan claims (5) | D1 C3 · D2 C3 · D5 C4 · D7 C1 · D8 C2 | - |

- No other check claims more than the single case its proof exercises

## Swept

- validation: C3
- failure modes: n/a - a failed job fails its run; retries are the platform's
- idempotency: n/a - training registers a new version each run, which is the intent
- authorization: n/a - catalog permissions are the platform's, outside this repo
- concurrency: n/a - one scheduled run per job
- data lifecycle: C2
- dependency failure: n/a - an unreadable input table fails the run before anything is written
- state transitions: n/a - aliases move only by promotion (references/promote.md)
- observability: C2

## Handoff
