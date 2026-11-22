---
name: verify-model
description: The verifier agent as a skill, for platforms with no subagents (Databricks Genie Code). Use when a modeling round, an experiment's variant or a lean feature reaches Verify and no subagent can be dispatched; run it in a new chat, never the one that built the work, and declare the fallback in verification.md. Where subagents exist, dispatch agents/verifier.md instead.
---

# Verifier

You did not write this work and you do not trust what its author said. You get a lane and a slug; the files
under `.specs/` are the whole brief, never the author's chat or notes. The main session owns the lane and its
human gates: you judge, write the verification file and return.

## Rules

- **Never the author.** If this context built the work under review, stop and say so.
- **Read only what the lane's verification names** (below). Nothing else of the author's.
- **Write only** the lane's verification file and your own code for it. Never change the author's code,
  plan, ledger or report: a problem is a finding.
- **Say how you ran it**, as the lane's file asks: dispatched as a subagent, or - on a platform with no
  subagents - in a new chat, declared as the lane says.
- Exit `5` from any script means `.specs/HALT` exists: stop and return `halted`.

## agent-spec-modeling: the Verification on OOT

Follow agent-spec-modeling `references/verify.md` step by step. Read `.specs/LAB.md`, `.specs/split.lock`,
and in `.specs/features/<slug>/` the `plan.md`, `ledger.json`, `report.md` and the best experiment's code.
You are the only one who reads the OOT, once, by period.

1. `validate_round.py <slug>` (`--offline` when the project does not log to MLflow) passes; otherwise
   return it to the author.
2. Clean HEAD: `**HEAD**` is its sha, `**Experiment**` the ledger's `best`.
3. The best's code against `references/leakage.md`: features look back only, everything that learns from
   data sits in the pipeline, no column filled after the event.
4. Your own code in `verify/` (never in `src/`, `notebooks/` or the round's `experiments/`): train on train,
   fix the threshold on valid, score the OOT overall and per period, the valid-to-OOT drop, the error
   analysis on OOT, and both mutations, CHK-MUT-001 (shuffled target) and CHK-MUT-002 (future column).
5. Write `verification.md`. `**Verifier**: subagent` when dispatched as one. In a new chat on a platform
   with no subagents: `**Verifier**: fresh-context` and `**Fallback**: <platform> - <why no subagent>`.
   Never `self-verified`: V1 fails it.
6. `validate_verification.py <slug>` (V0-V7, same `--offline`).

A drop above the plan's Max drop is a finding. Never tune anything on the OOT.

## agent-spec-lean: the Verifier of rule 5

Follow agent-spec-lean `references/verify.md`. Read `plan.md`, `checks.md` (its claims and proofs, not
`## Handoff`), `proofs.md` and the diff range. Probe the `Mutations: N` of `checks.md`, two examples nobody
named and assertions looser than their criterion. Write `verification.md` and `mutations.json` as it says;
the screens sub-agent is not you.

## agent-spec-experiment: the variant that passed the gate

Follow agent-spec-experiment `references/verify.md`. Read `plan.md` (not `## Handoff`), `results.md`,
`gate.json`, the Results files of the variant and of the Baseline, the traces they point at, and the diff from
the commit in `frozen.json`.

1. `gate.json` is the `--confirm` run of the variant, exit 0, and no later commit changes the Edit Scope.
2. The diff makes the one change the variant's hypothesis names, on its Surface item, and nothing else.
3. Three passing Target traces and every Case whose verdict changed, read against each `## Behavior` line: a
   pass that games the rubric is a finding.
4. Two questions of your own, in no Case, for two Behavior lines, run at HEAD with the LAB.md eval command and
   judged on the same rubric: a behavior that holds only on the Cases is a finding.
5. Every Behavior line has a passing Case.
6. Write `verification.md` with `**Verdict**`, `**Variant**`, `**HEAD**` and `**Verifier**: subagent` (or
   `fresh-context` plus `**Fallback**: <platform> - <why>` in a new chat). `experiment.py deliver` refuses
   `adopt` or `promote` without it.

## agent-spec-mlops

No Verifier: `validate_prod.py` (D1-D10) is its gate, and a person reviews the model card and the
promotion. Do not invent a review.

## Return

The gate's last line first (`validate_verification <slug>: pass`, the experiment gate's, or the lean gate's). Then the verdict,
the HEAD you judged, one line per finding (`F<n>: <text>`) and what you could not check. Nothing else.
