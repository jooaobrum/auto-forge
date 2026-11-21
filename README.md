# lanes

Take any piece of work - app, data pipeline, ML model, agent - from offline material to delivery:
shape → goal → plan → approve → work → verify → deliver. Work goes to the **build lane** when an
end-to-end test reproducing the user's behavior proves it, and to the **research lane** when only a
rate over a dataset does.

- `skills/shape/SKILL.md` - offline material and a short grilling become a Brief (what is ready, what is not)
- `skills/lanes/SKILL.md` - plan, approve, work, verify, deliver
- `rl` (`python -m lanes`) - the rules: brief, freeze, baseline, select, contract, gate, budget, deliver.
  It reads and writes files and runs nothing, so Claude Code, GitHub Copilot and Databricks Genie can all drive it.
- `examples/run_all.sh` - one worked example per Profile on local engines

To adopt in a host repo: add a `lanes.json` (see `examples/*/host/lanes.json`), copy `skills/`, paste
`skills/AGENTS-snippet.md` into the host's `AGENTS.md` (or Genie's workspace instructions), and
`pip install` this package. Vocabulary: `GLOSSARY.md`.
