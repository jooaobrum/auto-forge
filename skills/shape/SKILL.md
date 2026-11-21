---
name: shape
description: Turn offline material (meeting transcripts, research, notes) into a Brief that names the goal, the Profile, the lane and what is not ready yet, by grilling the user in short rounds. Use before planning any app, pipeline, model or agent work, or when the user says "shape", "brief" or drops material in .lanes/inbox/.
---

# Shape

Stage 1 of `lanes`: offline material → a **Brief** at `.lanes/work/<slug>/brief.md`. Vocabulary lives in the
`lanes` repo's `GLOSSARY.md`; use its words (Profile, lane, Case, Readiness).

## Steps

1. **Read everything first.** Every file in `.lanes/inbox/<slug>/`, the host's `AGENTS.md`, `lanes.json`, its
   glossary, and the code the material names. Facts you can look up are yours; decisions are the user's.
   Done when you can say, per item the material raises, whether the repo already answers it.

2. **Grill in rounds.** Ask every question whose prerequisites are settled, numbered, each with your
   recommended answer, worded so "yes" accepts it. Wait, fold the answers in, ask the next round. Cover:
   - the **goal**: what is different for a user when this ships;
   - the **Profile**: `app`, `pipeline`, `model` or `agent`;
   - the **lane**, by what can prove it: an end-to-end test that reproduces the user's behavior → `build`;
     only a rate over a dataset → `research`;
   - for `research`: the Failure Mode, the Target Metric, the Cases that show it, and the metrics from
     `lanes.json` that guard it;
   - for `pipeline`: the output datasets and the rules their data contract promises, the input fixture, the
     golden rows;
   - what each item needs before planning.
   Done when no question is left whose answer would change the plan.

3. **Write the Brief**, in this shape:

   ```markdown
   # <title>

   **Profile**: agent
   **Lane**: research
   **Plan**: <build lane only: path of the tlc-spec-lean plan.md>

   ## Goal

   <one paragraph: what is different for a user when this ships>

   ## Readiness

   | Item | State | Why |
   | --- | --- | --- |
   | <item> | ready / needs attention / not ready | <evidence, or what is missing> |

   ## Metrics

   - <metric names from lanes.json, research lane>
   ```

   Every item the material raised gets a Readiness row. `not ready` means planning cannot start without it;
   `needs attention` means planning can start but the item carries risk the plan must name.

4. **Make the results reachable.** The gate reads Results files (`{"runs":[{"case","run","metrics","touched",
   "trace"}]}`, a CSV with a `case` column, or JUnit XML). When the host's runner writes something else
   (an MLflow eval, a notebook table), write the smallest glue script in the host that converts it, and name
   it in the Brief's Readiness table.

5. **Check it**: run `rl brief <slug>`. Exit `2` names what is missing or `not ready`; resolve it with the
   user and rerun. Done when it exits `0`; then hand over to the `lanes` skill for stage 3.
