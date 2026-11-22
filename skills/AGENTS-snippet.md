## auto-forge

Every piece of work starts with **agent-spec-router** (`skills/agent-spec-router/SKILL.md`): give it a spec, a
design doc, a problem or just context. It grills when the context is not actionable, writes `.specs/LAB.md`
the first time, and routes to agent-spec-lean (app, code), agent-spec-pipeline (data), agent-spec-modeling (a
new model, from a confirmed Problem to a Verification on out-of-time data), agent-spec-mlops (a verified model to
production and its promotion) or agent-spec-experiment (agent behavior, or a failure mode of a model in
production, on a dataset). The agent runs every script; when `.specs/HALT` exists, every script stops.

Two subagents in `agents/` (repository root) take a step in a clean context: `verifier` judges a lane's work at
Verify, never its author, and `modeling-iteration-runner` runs one change of a modeling round. With no
subagents (Databricks Genie Code), run the `verify-model` or `run-modeling-iteration` skill in a new chat
instead; a modeling Verifier then writes `**Verifier**: fresh-context` and `**Fallback**: <platform> - <why>`.
