---
name: agent-spec-writer
description: Use when there is context - a PRD, a design doc, a ticket, transcripts, notes or only a conversation - but no plan a lane can run, when agent-spec-router asks for one, or when a seeded plan (a promote hand-off) needs completing. Drafts `.specs/features/<slug>/plan.md` from the lane's plan guide, detailed enough for an agent to work from, and grills only for what the sources do not answer.
---

# Agent Spec Writer

Every piece of work starts with a plan: `.specs/features/<slug>/plan.md`. It is written for two readers: the
human who approves it and objects to it, and the agent who works from it without the conversation. So it is
detailed - everything the work touches, why, what may break and how it will be proven - and every sentence
in it comes from a source, a fact you looked up, or the user's answer.

## 1. Pick the plan guide

agent-spec-router chose the lane and the Profile. Read the guide in full before writing a word:

| Work | Plan guide |
| --- | --- |
| app or code (build) | `agent-spec-lean/references/plan.md` |
| pipeline (build) | `agent-spec-pipeline/references/plan.md` - the lean plan plus fixture, contract, golden rows |
| a model to production (build) | `agent-spec-mlops/references/plan.md` - the lean plan plus contract, proof, promotion |
| agent behavior, or a model in production failing on a slice (research) | `agent-spec-experiment/references/plan.md` |
| a new model, or a new round of its backlog (research) | `agent-spec-modeling/references/plan.md` |

Build plans are lean plans: what must be true (Problem, Criteria), then what is being built (Shape, Surface,
Landing). Research plans keep that two-halves form for a rate over a dataset: what must be true (Problem,
Behavior or Question, Cases or Metric), then what is being tried (Diagnosis, Shape of the path the cases take,
Hypotheses, Edit Scope).

## 2. Read every source

- **What the user brought**, in full: a PRD, a design doc, a ticket, captures, transcripts, notes. Mark each
  one binding (the requirement) or non-binding (the user called it inspiration) as lean's plan says.
- **The project**: `.specs/LAB.md` (its defaults are not repeated in the plan), `.specs/STATE.md`
  `## Decisions` (every active one constrains the plan), the confirmed lessons, and the code the work touches.
- **The evidence**, for research: the failing traces or the per-slice error analysis (agent, model in
  production), the EDA and the previous round's report (modeling). Count; the numbers and the ids go in the
  plan.
- **A seeded plan** (`<slug>-build/plan.md` from an Experiment, `<slug>-mlops/plan.md` from a round): keep
  what the seed wrote, read the folder it points at, and complete the rest.

## 3. Map the sources onto the plan

Go through the sources one sentence at a time. Each sentence lands on exactly one of:

- a section of the plan: a criterion or behavior, a hop of the Shape, a door, a hypothesis, a Case;
- an `Out of scope` row with its reason;
- an `Assumptions` row with your default, `Confirmed? n`;
- an open question, marked `blocks`, `blocks go-live` or `open`.

A sentence that lands nowhere is the requirement that goes missing: nobody downstream reads the source again.
Then walk the plan the other way: a section the sources do not fill is a fact to look up in the repo or a
question for the user, never a guess written as a fact.

## 4. Grill for the gaps

Call **agent-spec-grilling** with the open questions only: the ones the sources and the repo do not answer
and that are the user's to decide (scope, product behavior, what may not regress, a trade-off, a bar). Each
answer lands in the plan in the turn it arrives.

## 5. Validate, present, hand back

Run the lane's check on the draft and fix every finding:

| Lane | Check |
| --- | --- |
| app, pipeline, model to production | `agent-spec-lean/scripts/validate_plan.py <slug>`; a pipeline also `contract.py compile <slug>` |
| agent, model in production | `experiment.py freeze <slug>` once approved: it refuses a plan with no Problem, Diagnosis or Hypotheses |
| modeling | `validate_plan.py <slug>` (P0-P11) |

Present the plan and stop. The user approves it in their words (`**Approved**: <date> - user: "..."`); never
write one they did not give. Hand back to agent-spec-router.
