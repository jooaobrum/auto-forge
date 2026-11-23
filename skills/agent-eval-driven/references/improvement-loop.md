# Improvement loop

## Diagnose before changing

An aggregate regression score does not reveal what to fix. Tag failed traces and group them into a small taxonomy before choosing an intervention: retrieval coverage, ranking, intent interpretation, semantic alias, temporal filter, tool choice, SQL constraint, policy violation, response synthesis, or operational limit.

Tags must be grounded in the trace, not guessed from the final score. A SQL case can carry both `semantic_alias` and `narrow_filter`; preserve both tags. The campaign should prioritize a cluster using its frequency, severity, user impact, and estimated evaluation cost—not only its count.

Maintain a failure register:

| Trace/case | Outcome | Tags | Evidence | Cluster | Severity |
| --- | --- | --- | --- | --- | --- |
| q-018 | missed `c044` | `semantic_alias`, `narrow_filter` | query omitted canonical payment event | payment vocabulary | high |

An agent may propose tags, but a fresh diagnostician should review the taxonomy when a plateau or high-impact promotion makes wrong categorization expensive.

For SQL or retrieval tasks, inspect the query and returned IDs alongside the label set:

```text
intent → generated query → executed result IDs → ranked top-k → labelled relevant IDs
```

SQL execution may be deterministic while query generation is not. Evaluate the result set and hard query properties rather than requiring an exact SQL string.

## Form a useful hypothesis

A good hypothesis has a predicted metric effect and a local mechanism:

> “The agent misses payment failures because the semantic catalog does not link `card declined` and `charge failure` to the canonical event. Adding that mapping should improve recall@20 on the payment-alias slice without widening tenant scope.”

Avoid “improve the prompt” or “make retrieval better.” Those do not give the next round a way to learn from a negative result.

## Keep the best state, not only the newest state

Every candidate starts from the incumbent unless branch evidence suggests otherwise. A candidate can be:

- **kept** — improves the incumbent and preserves hard gates;
- **reverted** — no useful gain or a protected regression;
- **branched** — incomplete or locally useful but not globally promotable.

Do not delete a reverted attempt’s receipt. Its diagnosis prevents repeated searches.

## Use budget to force continuation and restraint

A round is complete after a measured decision, not after a failed hypothesis. The campaign is complete only when it reaches the target, exhausts budget, or identifies a required decision outside its authority.

Change intervention family after repeated non-improvement. Examples of distinct families are: improve semantic context; change tool schema; improve query planning; add a bounded repair loop; change ranking; improve abstention/clarification behavior. Rephrasing the same prompt is not a new family.

## Spend evaluation budget deliberately

Do not run every easy case after every change. Use a tiered schedule, written in `campaign.md`:

1. **Round suite:** cases in the targeted failure cluster, plus safety-critical sentinels and a small control sample of previously easy cases. Run after each meaningful change.
2. **Checkpoint suite:** the entire frozen validation set. Run after a candidate wins its round suite, after a configured number of kept candidates, or when a change affects shared infrastructure such as routing, model choice, permissions, retrieval, or tool schema.
3. **Promotion suite:** full validation, holdout when available, and repeated unstable cases. A fresh verifier performs this run.

The control sample exists to catch broad regressions cheaply. Rotate it across rounds, stratified by case type and difficulty. Always retain non-negotiable safety tests; never sample them away. A cluster-targeted score is a diagnostic signal, not proof of global improvement.

Record the cost of every run: model calls, tokens, wall time, database/query cost, and human review time where available. Prefer the cheapest suite that can falsify the current hypothesis, then spend the full-suite budget only after the evidence earns it.

## Review only when it changes the decision

Use a fresh diagnostician when repeated attempts cannot localize the issue. Use a fresh verifier for release or high-impact promotion. Otherwise, retain one builder; extra agents are not evidence.
