# Memory

Three things outlive a session: decisions in `.specs/STATE.md`, lessons in agent-spec-lean's store, and the
Experiment's own files. The chat does not survive a compaction; the files do.

## Decisions

`.specs/STATE.md` `## Decisions`, as agent-spec-lean's [memory.md](../../agent-spec-lean/references/memory.md)
says: every `active` `AD-NNN` constrains the plan. A choice a future Experiment has to conform to - a rubric
convention, a guardrail the user set, a Surface item nobody may touch - is appended when it is made.

## Lessons

After the delivery, turn what the Experiment taught into lessons with agent-spec-lean's store:
`python3 <lean-dir>/scripts/lessons.py --root <project> add ...`. One per Verifier finding, and one per
rejected hypothesis whose reason would save the next Experiment a variant ("reading records in full overflows
short questions"). The next plan loads the confirmed ones before its Diagnosis.

## Resuming - a new session, or after a compaction

Re-read [SKILL.md](../SKILL.md) and the reference of the phase the files show, then reconcile them with git:
the commits are fact. Where the files put you - the first row that holds:

| The files show | Next |
| --- | --- |
| `plan.md` with no `**Approved**:` line | the plan: present it and stop |
| no `frozen.json` | commit the plan, `freeze` |
| no Baseline in `.specs/baseline/<profile>/` for the Cases | the Baseline ([run.md](run.md)) |
| a variant in `variants.json` with no `runs/<variant>/` | run its Cases from `selection.json` |
| `gate.json` with exit 1 | read its findings and the traces; the next variant or the fix |
| `gate.json` with exit 0 and no `--confirm` in its command | `gate --confirm` on the stable Cases |
| no `verification.md` for the variant of `gate.json` | dispatch the Verifier ([verify.md](verify.md)) |
| a finding with an empty `Closed` | the fix, then the gate again |
| no `delivery.md` | `deliver` |
| `delivery.md` | lessons; a `promote` goes to agent-spec-router |
