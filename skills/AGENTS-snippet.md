## auto-forge

Every piece of work starts with **agent-spec-router** (`skills/agent-spec-router/SKILL.md`): give it a spec, a
design doc, a problem or just context. It grills when the context is not actionable, writes `.specs/LAB.md`
the first time, and routes to agent-spec-lean (app, code), agent-spec-pipeline (data), agent-spec-modeling (a
new model, from a confirmed Problem to a Verification on out-of-time data), agent-spec-mlops (a verified model to
production and its promotion) or agent-spec-experiment (agent behavior, or a failure mode of a model in
production, on a dataset). The agent runs every script; when `.specs/HALT` exists, every script stops.
