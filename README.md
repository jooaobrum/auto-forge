# agent-spec

Spec-driven work for apps, data pipelines, ML models and agents. You give the agent a spec, a design doc, a
problem or just context; **agent-spec-router** makes it actionable and routes it to the lane whose proof can
close it. The agent runs everything; you answer questions, approve, and read the delivery.

| Skill | What it does |
| --- | --- |
| `agent-spec-router` | the one entry: grills when needed, writes `.specs/LAB.md` once, routes, takes back a `promote` |
| `agent-spec-grilling` | interviews you until ideas become actionable items |
| `agent-spec-writer` | drafts a lane's spec from your context |
| `agent-spec-lean` | build lane for app and code (plan, checks, build, independent Verifier) |
| `agent-spec-pipeline` | build lane for data: a data contract in the spec, compiled to SQL, plus golden rows |
| `agent-spec-experiment` | research lane for agent or model behavior: baseline, variants, per-Case gate, decision |
| `data-databricks-sql`, `ml-mlflow-log` | example domain skills, loaded at the plan / work / verify points |

How the workflow runs, end to end: [docs/workflow.md](docs/workflow.md).

## Install

The repository is the plugin (`skills/<name>/SKILL.md` at the root) and its own marketplace.

**Claude Code**

```
/plugin marketplace add <owner>/<this-repo>
/plugin install agent-spec@agent-spec
```

**VS Code (GitHub Copilot agent mode)** - enable `chat.plugins.enabled`, then run **Chat: Install Plugin
from Source** and paste the repository URL. Or add it to `chat.plugins.marketplaces` in settings:

```json
"chat.plugins.marketplaces": ["<owner>/<this-repo>"]
```

**GitHub Copilot CLI** - install from the repository with its plugin command; it lands in
`~/.copilot/installed-plugins/`, where VS Code also finds it.

**Databricks** - add the repository as a Git folder (Workspace > Create > Git folder). Point the assistant's
instructions at it by pasting [skills/AGENTS-snippet.md](skills/AGENTS-snippet.md) with the Git folder's path.
The scripts are standard-library Python, so a notebook runs them with `%sh python3 <path>/scripts/...`.

**Any other agent** - clone the repository and paste `skills/AGENTS-snippet.md` into the project's `AGENTS.md`.

## Develop

```bash
export UV_PROJECT_ENVIRONMENT=~/.venvs/lanes
uv sync
uv run pytest
uv run ruff check skills tests
bash examples/run_all.sh
```

Decisions: `.specs/STATE.md`. Vocabulary: `GLOSSARY.md`.
