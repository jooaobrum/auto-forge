# Verify

Two parts, as in agent-spec-lean. A script settles what can be settled mechanically: the gate, per Case, on
the frozen bars. A fresh Verifier spends its time on what needs judgement: where the variant passes the gate
and still does not do what the plan's `## Behavior` says.

Load the **verify** domain skills first (how traces and evals are read on this platform).

## The gate

```bash
python3 <skill-dir>/scripts/experiment.py gate <slug> --variant <variant>
```

It judges each Case of `selection.json` against the Baseline and writes `results.md` and `gate.json`:

- **Per Case**: a `regression` Case passes only if every run passes; a `capability` Case on a majority.
  A Case that passed the Baseline and fails now is `regressed`.
- **Target**: the mean of the Target metric over the Target Cases moves by at least the plan's delta.
- **Guardrails**: no Case spends more than the Baseline plus its guardrail (`input_tokens` +15%, `latency_ms`
  +20% by default).
- **Edit Scope**: every path changed since the frozen commit is inside it.

Each `FAIL` line is the next piece of work ([run.md](run.md)). Loop until a variant passes or `select` exits
`3`. Then run the stable Cases once and confirm:

```bash
python3 <skill-dir>/scripts/experiment.py gate <slug> --variant <variant> --confirm
```

## Author is not verifier

The Verifier is a fresh context with no inherited chat: the **verifier** agent (`agents/verifier.md` of this
plugin), dispatched with the slug and the variant and nothing about what to accept. With no subagents, a new
chat runs the `verify-model` skill and declares `**Verifier**: fresh-context` with `**Fallback**: <platform> -
<why>`; the delivery warns. Never `self-verified`: `deliver` refuses it.

## What the Verifier does

It reads `plan.md` (not `## Handoff`), `results.md`, `gate.json`, the Results files of the variant and of the
Baseline, the traces they point at, and the diff from the frozen commit. It fixes nothing; it writes
`verification.md`.

1. **The gate holds at `HEAD`**: `gate.json` is the `--confirm` run of the variant, with exit 0, and no commit
   after it changes the Edit Scope.
2. **One change, the one named**: the diff since the frozen commit makes the change the hypothesis of this
   variant names, on its Surface item, and nothing else.
3. **The behavior, not the number**: read three passing Target traces and every Case whose verdict changed,
   against each `## Behavior` line. A pass that games the rubric - every id cited whether used or not, a right
   answer to another question, a shorter answer that drops what the rubric asks - is a finding.
4. **Two questions nobody named**: for two Behavior lines, write a question of the same kind that is in no
   Case, run it at `HEAD` with the eval command, and judge it on the same rubric. A behavior that holds only
   on the Cases is overfit: a finding.
5. **Every Behavior line has a passing Case**: a line with no Case, or only failing ones, is a finding.

## Report

`.specs/features/<slug>/verification.md`:

```markdown
# <slug> verification

**Verdict**: PASS
**Variant**: cite-ids
**HEAD**: <sha>
**Verifier**: subagent

## Findings

| Finding | Evidence | Fix | Closed |
| --- | --- | --- | --- |
| q07 passes by citing every record read, used or not | trace t-88: cites WO-881, which the answer never uses | cite only the records used in the answer | <commit> |
```

With nothing to report, `None - <one line on what was probed>` under `## Findings`. A finding is closed by a
commit and a new gate run, and the builder fills `Closed`; `deliver` refuses an empty one. What cannot be
closed goes to the user, and the decision is `reject`.

## Deliver

```bash
python3 <skill-dir>/scripts/experiment.py deliver <slug> --decision adopt|promote|reject
```

- **adopt**: the variant stays; it needs a passing gate and a `verification.md` with `**Verdict**: PASS` for
  that variant.
- **promote**: it works, but the fix belongs in code (it must hold on every run, not on a rate). Same
  evidence as adopt; it seeds `.specs/features/<slug>-build/plan.md`: hand it to agent-spec-router.
- **reject**: nothing passed, or the Verifier's findings cannot be closed. Revert the variants; the plan, the
  results and what was learned stay.

Report `delivery.md`, opening with the gate's last line. Cases under "Proposed for regression" get
`regression` in their Tier once the user agrees. Then distill lessons ([memory.md](memory.md)).
