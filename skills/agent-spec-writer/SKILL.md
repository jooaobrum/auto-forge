---
name: agent-spec-writer
description: Use when there is context (a problem, design doc, transcripts, notes) but no spec a lane can run, or when agent-spec-router asks for one. Drafts `.specs/features/<slug>/spec.md` from the lane's template and grills only for what is missing.
---

# Agent Spec Writer

1. **Read everything given** and the repo, `.specs/LAB.md` and `.specs/STATE.md`.
2. **Pick the template** of the lane agent-spec-router chose:
   - app or code: agent-spec-lean's plan (`agent-spec-lean/references/plan.md`)
   - pipeline: `agent-spec-pipeline/references/spec-pipeline.md`
   - agent behavior: `agent-spec-experiment/references/spec-agent.md`
   - model: `agent-spec-experiment/references/spec-model.md`
3. **Fill it from the context.** Keep only the sections this work needs; every template marks what is
   required. Take defaults from `.specs/LAB.md` instead of repeating them.
4. **Grill for the gaps** with agent-spec-grilling: only what the context and the repo do not answer.
5. **Done** when the lane's freeze accepts it once the user approves: experiment specs pass
   `experiment.py freeze`, pipeline specs compile with `contract.py compile`, plans pass agent-spec-lean's
   `validate_plan.py`. Hand back to agent-spec-router.
