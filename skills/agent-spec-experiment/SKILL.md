---
name: agent-spec-experiment
description: Research lane for agent or model behavior that only a rate over a dataset can prove - prompts, skills, tool descriptions, model parameters. Use when agent-spec-router routes research work here, or the user wants to improve an agent or model on a dataset, run an experiment, or compare variants. One human-reviewed plan (problem, behavior, cases, diagnosis, hypotheses), then a Baseline and one variant per hypothesis, a per-Case gate, an independent Verifier and a decision.
---

# Agent Spec Experiment

agent-spec-lean's shape, for a proof that is a rate over a dataset. Freeze the obligations (the Cases, the
Metrics, the Edit Scope); free the variants; prove it with someone who did not run them.

```
┌──────┐   ┌─────┐   ┌────────┐   ┌─────────┐
│ PLAN │ → │ RUN │ → │ VERIFY │ → │ DELIVER │
└──────┘   └─────┘   └────────┘   └─────────┘
 read it    baseline   gate +       adopt, promote
 approve    variants   Verifier     or reject
```

One Experiment, one Failure Mode, one folder: `.specs/features/<slug>/`. You run every script:
`python3 <skill-dir>/scripts/experiment.py [--root <repo>] <command> <slug>`. Exit codes: `0` ok, `1` gate
fail, `2` invalid input, `3` variant cap, `4` budget spent, `5` halted (`.specs/HALT` exists: stop and ask the
user).

## Rules

These hold even if no reference file is read.

1. **The Cases are the checks.** Each Behavior line of the plan names the Cases that grade it, with a rubric
   and a concrete bar. They, the Metrics and the Edit Scope are frozen at `freeze`; changing them is
   renegotiation with the user, never a way to make a variant pass.
2. **One change per variant**, on one Surface item, inside the Edit Scope, named by a hypothesis of the plan.
   A second idea is a new hypothesis written in the plan before it runs.
3. **A metric moved is not a behavior fixed.** Read the traces of the Target Cases, passing and failing,
   against the Behavior lines; a pass that games the rubric is a failure.
4. **A regression is a stop.** A Case that passed the Baseline and fails in the variant fails the gate,
   whatever the Target did; so does a guardrail breached or a path changed outside the Edit Scope.
5. **Author is not verifier.** The **verifier** agent (`agents/verifier.md`), a fresh context, judges the
   variant that passed; it always runs before `adopt` or `promote`. With no subagents, a new chat runs the
   `verify-model` skill and declares a `**Fallback**`.
6. **The completion gate is a script**: `experiment.py deliver` refuses `adopt` or `promote` without a
   passing gate and a `verification.md` with `**Verdict**: PASS` for that variant and every finding closed.
7. **The files hold the run.** The approval is `**Approved**: <date> - user: "<their words>"` in `plan.md`,
   never one the user did not give. Budget extensions carry the user's words. After a compaction, resume from
   the files ([memory.md](references/memory.md)).
8. An approved plan authorizes local edits, runs and commits. `git push`, a deploy or a change to a production
   prompt needs the user's explicit OK.

## Load points

Read `.specs/LAB.md` `## Domain skills` and load the skills listed for each point when you reach it:
**plan** (before the plan), **work** (before the Baseline), **verify** (before the gate and the Verifier).

## Phases

| Phase | What it produces | Reference |
| --- | --- | --- |
| Plan | problem, behavior, cases, metrics, diagnosis, shape, hypotheses, edit scope; the one default stop for a human | [plan.md](references/plan.md) |
| Run | the Baseline, one variant per hypothesis, Results files, the traces read | [run.md](references/run.md) |
| Verify | the per-Case gate, the confirm run, the Verifier, `verification.md`, the decision | [verify.md](references/verify.md) |

Decisions, lessons and resuming: [memory.md](references/memory.md).

## Scripts

| When | Command |
| --- | --- |
| After the user approves the plan, committed | `freeze <slug>` |
| After the Baseline run | `baseline <slug> --from <results file>` |
| Before each variant | `select <slug> --variant <name>` |
| After each variant's runs | `gate <slug> --variant <name>` |
| Once a variant passes | `gate <slug> --variant <name> --confirm` |
| When the budget is spent and the user says yes | `budget <slug> --add <tokens> --user "<their words>"` |
| After the Verifier | `deliver <slug> --decision adopt\|promote\|reject` |

A Results file: `{"runs":[{"case","run","metrics":{...},"touched":[...],"trace","read":[ids],"cited":[ids],"route"}]}`
(`read`, `cited`, `route` only when the Cases grade them); a CSV with a `case` column, or JUnit XML, also work.

## Artifacts

```
.specs/
├── LAB.md                       # eval command, metrics, Surface, default Edit Scope, domain skills
├── baseline/<profile>/<case>.json   # the Baseline per Case, with the Surface hash it was measured on
└── features/<slug>/
    ├── plan.md                  # the plan, approved; ## Handoff appended after the run
    ├── frozen.json              # the commit every diff is measured from
    ├── variants.json, selection.json
    ├── runs/<variant>/*.json    # Results files
    ├── results.md, gate.json    # the last gate
    ├── verification.md          # the Verifier's verdict and findings
    └── delivery.md              # the decision; promote seeds <slug>-build/plan.md
```

## Output

Produce the artifact; do not narrate the phase. Lead with the gate's verdict and the decision.
