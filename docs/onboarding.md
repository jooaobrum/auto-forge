# Onboarding: your first day with auto-forge

This guide assumes you have used a coding agent (Claude Code, GitHub Copilot) but never auto-forge. It
takes about 30 minutes.

## 1. The idea in five sentences

1. You describe what you want, in any form: a spec, a design doc, a ticket, a meeting transcript, a sentence.
2. The agent turns it into **one plan** for that piece of work and asks you about whatever is unclear.
3. Before anything is built, the plan says **what will prove the work is done**.
4. You approve the plan, and the agent builds or experiments until a **script** says the proof passes.
5. You read `delivery.md`: the goal, the evidence, the decision, the commits.

You never fill a config file and never run the scripts yourself. You talk, approve and read.

## 2. Words you will see

| Word | Meaning |
| --- | --- |
| **plan** | the one document every piece of work starts with: `.specs/features/<slug>/plan.md` |
| **lane** | how the work is proven: **build** (a test or a data contract) or **research** (a rate over a dataset) |
| **profile** | what you are building: `app`, `pipeline`, `model` or `agent` |
| **case** | one thing the research gate judges: a question for an agent, a slice of the holdout for a model |
| **baseline** | how each case behaves today, recorded before any change |
| **variant** | one attempted change in an Experiment (at most 3) |
| **guardrail** | a cost that may not grow too much, such as input tokens +15% |
| **Edit Scope** | the files the agent is allowed to change in an Experiment |
| **LAB.md** | what the agent learned about your project once: how evals run, metrics, which files steer what |

The full vocabulary is in [GLOSSARY.md](../GLOSSARY.md).

## 3. Install (5 minutes)

Pick your tool and follow the matching block in the [README](../README.md#install). To check it worked, ask
your agent:

> What skills do you have for agent-spec?

It should list `agent-spec-router` and the other `agent-spec-*` skills.

## 4. Watch it work before you use it (5 minutes)

```bash
git clone https://github.com/jooaobrum/auto-forge.git && cd auto-forge
KEEP=1 bash examples/agent/run.sh
```

Near the top it prints `host kept at /tmp/...`. Open that folder and read, in this order:

1. `.specs/LAB.md` - what the agent knows about this (fake) project
2. `.specs/features/cite-history/plan.md` - the Experiment: a failure mode, three questions, a target
3. `.specs/features/cite-history/results.md` - the per-case verdict of the winning variant
4. `.specs/features/cite-history/delivery.md` - what you would read at the end

Scroll up in the terminal output too: the first variant fails with `FAIL q02: regressed` and an
`input_tokens` guardrail breach. That is the gate doing its job.

## 5. Your first real piece of work (15 minutes)

Pick something small. Open your project in your agent and say, in your own words:

> Use agent-spec-router. I want <what you want>. Here is what I know: <paste a ticket, notes, or a link>.

What happens next:

1. **The first time in a project**, the agent writes `.specs/LAB.md` and asks you to confirm each part: how
   your tests or evals run, which metrics matter, which files steer your agent. Answer; it never asks again.
2. **If your context is unclear**, it grills you: numbered questions, each with a recommended answer.
   Answering "yes" accepts the recommendation; otherwise say what you want.
3. **It shows you the plan** and stops. Read the goal and the proof. When you agree, tell it to approve -
   it writes `**Approved**: <date> - user: "<your words>"` with your words.
4. **It works.** In the build lane it plans, writes tests, builds and has an independent reviewer check it.
   In the research lane it records a baseline and tries variants. You can watch or walk away.
5. **It may stop to ask** whether to spend more tokens. Say yes with an amount, or stop.
6. **It reports `delivery.md`.** For an Experiment, the decision is one of:
   - **adopt** - the change goes in;
   - **reject** - the idea did not work, and the evidence says why;
   - **promote** - it works, but the fix belongs in code, so a build-lane plan was seeded for it.

## 6. Which lane will my work take?

| You say | Lane | What proves it |
| --- | --- | --- |
| "Add an export button to the report page" | build (app) | an end-to-end test clicking the button |
| "Deduplicate the orders table on Databricks" | build (pipeline) | a data contract (unique `order_id`, ...) and golden rows on a small input |
| "The agent forgets to cite the work orders it read" | research (agent) | cited recall per question, before and after |
| "The classifier is bad on short inputs" | research (model) | accuracy per holdout slice, across seeds |
| "Predict which customers churn next month" | modeling (a new model) | a confirmed Problem, then the metric on out-of-time data against a baseline |
| "Put the churn model in production" | mlops (build) | the production standard (D1-D10), then no slice regresses against the champion |

You do not choose: the router does, and tells you why.

## 7. Tips

- **Give context, not instructions.** A ticket and two lines on why it matters beat a step-by-step prompt.
- **One problem per piece of work.** In an Experiment, one failure mode at a time.
- **For an agent, start with 10-20 real questions** and their rubric. Add the record ids it should read or
  cite only when the question is about retrieval.
- **Every failure you find later becomes a new case**, so it cannot come back silently.
- **Commit `.specs/`.** It is the record of why something changed and what the evidence said.

## 8. When something goes wrong

| You see | It means | Do |
| --- | --- | --- |
| "no **Approved**: line" | the plan is not approved yet | read it and approve, or ask for changes |
| "variant cap reached" | 3 variants tried, none passed | read `results.md` and decide: reject, or change the hypothesis in a new plan |
| "budget spent" | the token budget is used up | say whether to continue and how much |
| "outside Edit Scope" | the agent changed a file it was not allowed to | ask it to revert, or widen the scope in the plan |
| "stale or missing Baseline" | the code behind some cases changed since the baseline | the agent reruns those cases first |
| "HALT .specs/HALT exists" | someone stopped every lane script | delete `.specs/HALT` when the work may go on |

Questions or ideas: open an issue on [github.com/jooaobrum/auto-forge](https://github.com/jooaobrum/auto-forge).
