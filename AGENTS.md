# auto-forge

The agent-spec skills (`skills/`), packaged as a plugin. Every piece of work enters through
`agent-spec-router`. Vocabulary: `GLOSSARY.md`. Decisions: `.specs/STATE.md`.

```bash
uv sync                       # set UV_PROJECT_ENVIRONMENT to keep the venv outside a synced folder
uv run pytest
uv run ruff check skills tests
bash examples/run_all.sh
```


## agent-spec-lean

mutations: 3
