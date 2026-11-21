# Ideas: grilling into the backlog

Question the user (and the data) until every idea has a mechanism that fits in one sentence. The output is
the `## Backlog` of the round's `plan.md` (`.specs/features/<slug>/plan.md`), which `validate_plan.py`
checks. Run it between the EDA ([eda.md](eda.md)) and the hill-climbing loop ([loop.md](loop.md)).

## Inputs

The `## Problem` of `.specs/LAB.md`, `.specs/features/<slug>/eda.md` (Findings, Candidate features,
Leakage suspects), the lessons that apply from the project's lesson store when it keeps one
(agent-spec-lean keeps `.specs/lessons.json`), or none, and [recipes/feature-ideas.md](recipes/feature-ideas.md).

## Grilling

One question at a time, always with your own proposed answer for the user to confirm or correct.
Go on until no ambiguity is left:

1. **Mechanism:** "Why would this variable change the target? What happens in the process?" With no
   answer, the idea goes to the end of the list.
2. **Availability:** "At prediction time, does this value already exist? With what delay does it arrive?"
   If it does not exist, it is dropped.
3. **Grain:** "Is it per row, per group or per period? Relative or absolute?"
4. **Evidence:** "What in the EDA or in a lesson supports this? Which number?" Without evidence, the idea
   may stay, marked `Source: domain`, but a quick test on train comes first.
5. **Form:** "Which transformation expresses the mechanism? (ratio, difference to the group, lag, log, threshold)"
6. **Risk:** "Can it leak? Does it use the future, the target or a post-event column?"
7. **Cost:** "Does it need another table? Is it in the catalog, with which key and what timing?"

Push back on vague answers ("it should help", "it is important"): ask for the concrete case, the number,
the example of one batch or customer.

## Backlog

Write it in `plan.md`, in search order (cleaning -> domain -> group/time -> interactions -> model):

```markdown
### H1 - <idea in a few words>
- Idea: <what changes in experiment.py>
- Why: <the mechanism, and the evidence with a number>
- Source: <eda | domain | lesson L-NNN | recipe <name>>
```

Between 6 and 15 ideas for the first round. Model and hyperparameter ideas go last. Then run
`validate_plan.py <slug>` and ask for approval of the backlog and the budget (see [loop.md](loop.md)).
