# Eval Lean artifacts

## `contract.md`

The approved authority document. Keep it short.

```md
# Contract — <capability>

## Job
<User outcome and operational context.>

## Must
- <observable behavior>

## Must not
- <safety or policy boundary>

## Release gates
| Claim | Gate | Threshold | Authority to change |
| --- | --- | --- | --- |
| Retrieval coverage | recall@20 | >= 0.90 | product + domain owner |
| Tenant safety | cross-tenant rows | 0 | security owner |

## Approval
<date, approver, exact approval text>
```

## `campaign.md`

The bounded search charter. It grants autonomy inside named limits, not authority to rewrite the contract.

```yaml
mission: Improve semantic SQL retrieval for retention analysts.
incumbent: runs/baseline
target:
  recall_at_20: ">= 0.90"
  policy_violations: 0
budget:
  rounds: 12
  official_eval_runs: 6
  cost_usd: 40
allowed_levers:
  - tool descriptions
  - semantic catalog
  - examples
  - routing and retry policy
forbidden_levers:
  - official dataset, labels, metric code, thresholds
  - new data permissions
search_policy:
  after_two_same_family_failures: switch_lever
  after_four_total_failures: fresh_diagnosis
evaluation_policy:
  each_round: targeted_failure_cluster + safety_sentinels + regression_controls
  full_validation: promising_candidate | every_3_kept_candidates | promotion
stop:
  - all release gates pass
  - budget exhausted
  - authorized levers cannot address the evidence
```

## `eval-spec.md`

Record the project-provided evaluator instead of copying its semantics into prose.

```yaml
official_evaluation:
  dataset_path: path/from/project
  dataset_revision: <git SHA or SHA-256>
  command: ./scripts/evaluate-agent --suite validation --json
  command_revision: <git SHA or SHA-256>
  required_environment: <variables, fixture, service>
  output_contract: "one JSON object containing metrics and per-case results"
splits:
  dev: optional path
  validation: supplied project dataset
  holdout: optional path; verifier-only
metrics:
  recall_at_20: higher_is_better
  ndcg_at_10: higher_is_better
  cross_tenant_rows: must_equal_zero
```

## `proofs.md`

`proofs.md` is a claim-to-evidence ledger. It prevents completion claims based only on a narrative. It is not a duplicate of the evaluator.

```md
# Proofs — <capability>

| Claim | Proof command / inspection | Required saved artifact | Pass condition |
| --- | --- | --- | --- |
| Relevant accounts are retrieved | official evaluator from `eval-spec.md` | `runs/<id>/receipt.json`, per-case output | recall@20 >= 0.90 on validation |
| Ranking is useful | same receipt | `runs/<id>/metrics.json` | nDCG@10 >= 0.85 |
| Tenant isolation holds | deterministic policy check | query trace + policy report | 0 cross-tenant rows |
| Candidate is reproducible | fresh verifier rerun | `verification.md` + receipt | same evaluator identity; all gates pass |
```

A proof should name the exact evaluator identity and receipt. “The agent says it works” and an unversioned screenshot are not proof.

## `ledger.md`

Append one row per completed round. Retain rejected candidates and their evidence. Link the trace IDs and failure tags that informed the change.

| Round | Failure cluster | Trace tags | Hypothesis | Change | Round result | Decision | Next direction |
| --- | --- | --- | --- | --- | --- | --- |
| 3 | payment aliases | `semantic_alias`, `narrow_filter` | Missing domain taxonomy narrows SQL filters | Add taxonomy to tool context | targeted recall@20 0.71 → 0.84 | keep | diagnose temporal filters |

## Run receipt

Every official run stores the evaluator’s raw output plus normalized metadata:

```json
{
  "run_id": "r-004",
  "candidate_revision": "git:abc123",
  "evaluator_revision": "git:def456",
  "dataset_revision": "sha256:...",
  "command": ["./scripts/evaluate-agent", "--suite", "validation", "--json"],
  "exit_code": 0,
  "metrics": {"recall_at_20": 0.84, "ndcg_at_10": 0.79},
  "artifacts": ["raw-evaluator-output.json", "per-case.jsonl"]
}
```
