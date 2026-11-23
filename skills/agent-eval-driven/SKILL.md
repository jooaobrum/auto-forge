---
name: agent-eval-driven
description: Improve an AI agent or ML-assisted workflow against an existing project dataset and evaluation script through a bounded, evidence-driven campaign. Use for agent behavior, retrieval, SQL-generation, RAG, or ranking improvements with measurable targets. Do not use for one-off prompt drafting or when no runnable evaluation exists.
---

# Eval Driven

Freeze the evaluation contract. Free the implementation. Keep searching until a gate, budget, or legitimate escalation ends the campaign.

Eval Driven adapts a lean spec workflow for products whose behavior is non-deterministic. The project-provided dataset and evaluator are the proof mechanism. The builder may change the agent harness only within the campaign's authorized levers; it must not weaken, replace, or edit the official evaluator to improve a score.

## Operating model

```text
CONTRACT → CAMPAIGN → BUILD/MEASURE LOOP → VERIFY → PROMOTE
 human       bounded       one builder       fresh       gate or
 approval    search        by default        replay      escalation
```

There is one builder by default. Add a fresh diagnostician or verifier only when the campaign reaches a plateau, evidence is ambiguous, or a promotion decision is high-impact. Do not create a standing multi-agent pipeline.

## Required artifacts

Create these under the project’s chosen evaluation directory. Save the request and the project-supplied dataset/evaluator references once at campaign start.

```text
.agent-evals/
├── request.md
├── contract.md
├── campaign.md
├── eval-spec.md
├── proofs.md
├── ledger.md
├── locked/                 # immutable references or content-addressed copies
├── dev/                    # optional, builder-visible diagnostic cases
└── runs/<run-id>/
```

Read [artifacts.md](references/artifacts.md) before creating the artifacts. Read [improvement-loop.md](references/improvement-loop.md) before starting a campaign or when a hypothesis fails.

## Start a campaign

1. Save the user request verbatim in `request.md`.
2. Locate the project’s dataset and evaluation command. Record their paths, revision or checksums, required environment, and output format in `eval-spec.md`. Do this once before any harness change.
3. Run the evaluator unchanged against the incumbent and save the complete baseline receipt under `runs/baseline/`.
4. Write `contract.md` with the capability, safety boundaries, fixed release gates, and the authority required to change them. Obtain the required human approval.
5. Write the lean `campaign.md`: target, budget, allowed levers, forbidden levers, split policy, and stopping rules. It is a search charter, not an implementation task list.
6. Write `proofs.md`, mapping every must-pass claim to an executable proof. A proof is only satisfied by a saved evaluator receipt or a deterministic inspection artifact, never by the builder’s assertion.

Do not begin optimization until the baseline receipt and the frozen evaluator identity exist.

## Evaluation integrity

Treat the official evaluator and its labelled data as read-only during a campaign. The builder may add candidate diagnostic cases, but may not alter official labels, thresholds, metric code, fixtures, or the official command.

When possible, keep three roles separate:

- `dev`: visible, cheap cases for rapid diagnosis.
- `validation`: frozen cases used to compare candidates.
- `holdout`: unavailable to the builder; replayed by a fresh verifier for promotion.

If the project only supplies one dataset, record that limitation. Reserve a reviewed subset as holdout before repeated optimization where feasible; do not silently reshuffle labels or cases.

## Builder loop

Each builder turn is a medium, bounded round—not an open-ended request to "improve the benchmark." It must leave the next turn more informed.

1. Read the contract, campaign, ledger, incumbent receipt, and relevant failed traces/cases.
2. Tag failures from traces, group them into recurring patterns, and select the largest or highest-risk cluster. State one falsifiable causal hypothesis. Do not select work from an aggregate score alone.
3. Make the smallest coherent change within the allowed levers.
4. Run the round suite: the targeted cluster, safety/critical sentinels, and a small stable control sample. Inspect traces or query results when an aggregate score cannot explain the failure.
5. Run the full official suite only when the round suite is promising, a scheduled checkpoint is due, or promotion is proposed. Save every official receipt unchanged.
6. Compare the candidate with the incumbent on the same cases, configuration, and repetitions. Check all hard gates and relevant slices, not only an aggregate score.
7. Keep, revert, or retain as a branch. Record the evidence, decision, and next search direction in `ledger.md`.
8. Continue the campaign after a rejected hypothesis while budget remains. A failed hypothesis is evidence, not completion.

Never claim the campaign is complete merely because one change failed or because a local dev subset passed.

## Candidate selection

Promote a candidate only when its official receipt meets every hard gate and improves or preserves protected metrics. For non-deterministic behavior, use matched repetitions or a confidence-aware comparison when the evaluator supports it; do not promote on a single noisy increase. Do not drop easy cases forever: use them as a small regression-control sample during rounds and rerun the complete suite at checkpoints and promotion.

For retrieval or SQL-generation work, evaluate at the layer where the uncertainty occurs. A generated SQL query can be non-deterministic even though SQL execution is deterministic. Compare its returned IDs/ranking with labelled relevant IDs using metrics such as recall@k, precision@k, MRR, or nDCG, while separately checking permissions, tenant scope, forbidden columns, and query cost.

## Plateaus and escalation

After two non-improving attempts in one intervention family, switch to a different authorized lever. After four non-improving attempts overall, request a fresh diagnostic review before continuing. Ask for human direction only when evidence indicates that progress requires a change to the contract, labels, evaluator, data access, product policy, or budget.

## Verification

Before a high-impact promotion, use a fresh verifier that did not build the candidate. The verifier re-runs the official command from a clean candidate state, checks artifact identities and gates, inspects a risk-based trace sample, and writes `verification.md`. It does not modify the candidate or relax proofs.

Use `scripts/record_eval.py` when the project evaluator can emit one JSON object with a `metrics` field. The helper records the exact command, exit status, evaluator output, and metadata; it does not score the model or replace the project evaluator.
