# Run

Measure the Baseline, then try the hypotheses one variant at a time until one passes the gate or the
variant cap is reached. The Cases, the Metrics and the Edit Scope are fixed at `freeze`; the order, the wording
of each change and how you read the traces are yours. The bar is [SKILL.md](../SKILL.md) rules 1-4.

Load the **work** domain skills first (`.specs/LAB.md` `## Domain skills`): how the eval runs on this
platform, how runs are logged, how Results files are written.

## Freeze

The plan has its `**Approved**:` line in the user's words. Commit it, then:

```bash
python3 <skill-dir>/scripts/experiment.py freeze <slug>
```

It records the commit every later diff is measured from (`frozen.json`). Every `WARN` it prints is a section
the plan should have: add it now, before the Baseline, and freeze again.

## The Baseline

Run the eval on every Case once, at the frozen commit, with the `**Eval command**:` of LAB.md and k runs per
Case as the plan's `**k**:` says for the Target. Write one Results file:

```json
{"runs": [{"case": "q07", "run": 1, "metrics": {"cited_recall": 0.33, "input_tokens": 52000},
           "touched": ["skill:history"], "trace": "<trace id or url>",
           "read": ["WO-881", "PD-12"], "cited": [], "route": "history"}]}
```

`touched` names the Surface items the run went through (LAB.md `## Surface`): it decides which Cases a later
variant can affect. `read`, `cited` and `route` only when the Cases grade them. A CSV with a `case` column, or
JUnit XML, also work. Then:

```bash
python3 <skill-dir>/scripts/experiment.py baseline <slug> --from <results file>
```

Read the Baseline before the first variant. It is where the pass bars come from: when the plan's
`## Metrics` left a `Pass at` empty, propose one from these numbers and ask. When the Baseline contradicts the
Diagnosis (the Target already passes, or fails for another reason), stop: the plan is wrong, not the variant.

## One variant per hypothesis

For each `### H<n> - <variant>` of the plan, in order:

1. `experiment.py select <slug> --variant <variant>` writes `selection.json`: the Target Cases with their k,
   the affected Cases (they touch a Surface item inside the Edit Scope), the stable ones (k 0 for now), and
   `stale`, the Cases whose Baseline was measured on a Surface that has changed since. Rerun the stale
   Baselines first.
2. Make the **one change** the hypothesis names, on the Surface item it names, inside the Edit Scope. Two
   changes in one variant make its result unreadable: a second idea is a new hypothesis, appended to the plan
   with its Idea and Why before it runs.
3. Run exactly the Cases and k in `selection.json`, and save the Results under `runs/<variant>/`.
4. Commit the change with the hypothesis in the message (`prompt(history): cite the id of every record used`).
   A variant that fails is reverted in the next commit: the next variant starts from the frozen Surface, not
   from a failed one.
5. Gate it ([verify.md](verify.md)). Each `FAIL` line is the next piece of work: read the failing traces
   before you change anything.

`select` exits `3` at the variant cap: stop, deliver `reject` or ask the user for more variants.

## Read the traces, not only the numbers

A metric moved is not a behavior fixed. For each variant, read at least three Target traces that pass and
every one that fails, against the plan's `## Behavior`: the answer does what the line says, for the reason the
hypothesis gave. A pass that games the rubric - every id cited whether used or not, a correct answer to
another question - is a failure you write down, not a win.

## Budget

When `select` or `budget` exits `4`, the token budget is spent: stop and ask the user whether to continue. On
their yes, `experiment.py budget <slug> --add <tokens> --user "<their words>"`; their words are recorded.

## Scope

Outside the Edit Scope, change nothing: the gate fails any path outside it. A fix that needs code is not a
variant: it is a `promote` ([verify.md](verify.md)). Push and deploy need the user's explicit OK.

## Then stop

Append to `## Handoff` in `plan.md`: the variants tried, what each moved, what you read in the traces, and
which variant goes to the Verifier. Then verify ([verify.md](verify.md)).
