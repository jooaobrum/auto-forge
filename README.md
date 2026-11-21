# auto-forge

**Spec-driven agent workflows for apps, data pipelines, ML models and agents.**

Bring a spec, a design doc, a meeting transcript or a single sentence. auto-forge turns it into an actionable
spec, decides what will prove the work is done, lets the agent build or experiment until that proof passes,
and hands you back a delivery with the evidence. You talk, approve and read; the agent does the rest.

Most coding-agent workflows assume every change can be proven by a unit test. Real work is not like that:
an agent prompt that fixes three questions can quietly break five others, a pipeline can pass its tests and
still ship a broken column, a model tweak can win on average and lose on the slice that matters. auto-forge
routes each piece of work to the **lane whose proof can close it**:

| Lane | Proven by | For |
| --- | --- | --- |
| **build** | an end-to-end test that reproduces the user's behavior | app features, code fixes |
| **build** | a data contract and golden rows on the pipeline's output | data pipelines (Databricks or any SQL engine) |
| **research** | a per-case comparison against a baseline on a dataset | agent behavior, ML models |

In the research lane nothing hides in an average: every case that passed before and fails now is named, a
variant that improves recall by spending +100k tokens per turn fails its guardrail, edits outside the agreed
files fail the gate, and the agent stops and asks you when the token budget runs out.

**Planned, not built yet:** two lanes take a model from a problem to production - `agent-spec-modeling`
(a locked split, rounds of one change each, verified on out-of-time data) and `agent-spec-mlops` (production
code, then a per-slice promotion of challenger over champion). See
[Data science end to end](docs/workflow.md#data-science-end-to-end-planned).

**New here? Start with [docs/onboarding.md](docs/onboarding.md).** How the workflow runs end to end:
[docs/workflow.md](docs/workflow.md).

## What's inside

| Skill | What it does |
| --- | --- |
| `agent-spec-router` | the one entry: grills when needed, learns the project once (`.specs/LAB.md`), routes, takes back a `promote` |
| `agent-spec-grilling` | interviews you until ideas become actionable items |
| `agent-spec-writer` | drafts a lane's spec from your context |
| `agent-spec-lean` | build lane for app and code: plan, proof-backed checks, build, independent Verifier |
| `agent-spec-pipeline` | build lane for data: a data contract in the spec, compiled to SQL, plus golden rows |
| `agent-spec-experiment` | research lane: baseline, up to 3 variants, a per-case gate, a decision |
| `data-databricks-sql`, `ml-mlflow-log` | example domain skills your team replaces with its own know-how |

Everything is markdown plus standard-library Python scripts, so it runs wherever an agent has a shell:
Claude Code, GitHub Copilot in VS Code, the Copilot CLI, Databricks, or any agent that reads `AGENTS.md`.

## Install

**Claude Code**

```
/plugin marketplace add jooaobrum/auto-forge
/plugin install auto-forge@auto-forge
```

**VS Code (GitHub Copilot agent mode)** - turn on `chat.plugins.enabled`, run **Chat: Install Plugin from
Source** and paste `https://github.com/jooaobrum/auto-forge`. Or list it as a marketplace in your settings:

```json
"chat.plugins.marketplaces": ["jooaobrum/auto-forge"]
```

**GitHub Copilot CLI** - install it from `jooaobrum/auto-forge` with the CLI's plugin command; VS Code finds
it there too.

**Databricks** - Workspace > Create > Git folder > `https://github.com/jooaobrum/auto-forge`. Paste
[skills/AGENTS-snippet.md](skills/AGENTS-snippet.md) into the assistant's instructions, with the Git folder's
path in front of `skills/`.

**Any other agent** - clone the repository and paste `skills/AGENTS-snippet.md` into your project's
`AGENTS.md`.

## Try it in two minutes

```bash
git clone https://github.com/jooaobrum/auto-forge.git && cd auto-forge
bash examples/run_all.sh
```

It needs Python 3.9+, git and pytest (`pip install pytest`, for the app example). It runs one worked example per kind of work - an app, a pipeline, a model and an agent - from `spec.md` to
`delivery.md` on your laptop. Watch the agent example: its first variant is rejected with
`FAIL q02: regressed` and an input-token guardrail breach, the second is adopted.

## Develop

```bash
uv sync            # Python 3.9+; set UV_PROJECT_ENVIRONMENT to keep the venv out of a synced folder
uv run pytest
uv run ruff check skills tests
```

The project builds itself with its own build lane: plans, checks, proofs and verifications live in
`.specs/features/`, decisions in `.specs/STATE.md`, vocabulary in `GLOSSARY.md`.

`agent-spec-lean` is derived from [tlc-spec-lean](https://github.com/tech-leads-club) by Tech Leads Club
(CC-BY-4.0).
