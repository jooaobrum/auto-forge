# auto-forge

The agent-spec skills (`skills/`), packaged as a plugin. Every piece of work enters through
`agent-spec-router`. Vocabulary: `GLOSSARY.md`. Decisions: `.specs/STATE.md`. Every lane's gates are
standard-library scripts with pytest suites in `tests/` (the modeling and mlops gates are mutation-tested on
`tests/fixtures/`); a `.specs/HALT` file makes every lane script exit 5.

```bash
uv sync                       # set UV_PROJECT_ENVIRONMENT to keep the venv outside a synced folder
uv run pytest
uv run ruff check skills tests
bash examples/run_all.sh
```


## agent-spec-lean

mutations: 3
