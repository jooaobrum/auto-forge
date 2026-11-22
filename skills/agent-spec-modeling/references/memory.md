# Memory

Three things outlive a session: decisions in `.specs/STATE.md`, lessons in agent-spec-lean's store, and the
round's own files. The chat does not survive a compaction; the files do.

## Decisions

`.specs/STATE.md` `## Decisions`, as agent-spec-lean's [memory.md](../../agent-spec-lean/references/memory.md)
says: every `active` `AD-NNN` constrains the plan. A choice the next round has to conform to - a column never to
use, a population excluded, a metric the business chose - is appended when it is made.

## Lessons

After the delivery, turn what the round taught into lessons with agent-spec-lean's store
(`python3 <lean-dir>/scripts/lessons.py --root <project> add ...`): one per Verifier finding, one per rejected
or infeasible hypothesis whose reason would save the next round an iteration ("s000 leaks: it is read after the
final test"). The next plan lists the ones it loaded in `## Lessons loaded`.

## Resuming - a new session, or after a compaction

Re-read [SKILL.md](../SKILL.md) and the reference of the phase the files show, then reconcile them with git:
the commits are fact. Where the files put you - the first row that holds:

| The files show | Next |
| --- | --- |
| `route.py problem` does not exit 0 | back to agent-spec-router: the Problem |
| no `.specs/split.lock` | lock the split ([patterns/split.md](patterns/split.md)) |
| no `eda.md` | EDA on train ([eda.md](eda.md)) |
| `plan.md` with no `**Approved**:` line | the plan: present it and stop |
| no `ledger.json`, or no baseline in it | the baseline ([loop.md](loop.md)) |
| fewer iterations in the ledger than the Budget, and a hypothesis not tried | the next iteration |
| no `report.md`, or `validate_round.py` fails | the report, then `validate_round.py` |
| no `verification.md` | dispatch the Verifier ([verify.md](verify.md)) |
| `validate_verification.py` fails | its findings; a drop above Max drop goes to the user |
| no `delivery.md` | `deliver.py` |
| `delivery.md` | lessons; a `promote` goes to agent-spec-router |
