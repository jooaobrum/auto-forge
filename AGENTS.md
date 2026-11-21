# lanes

The agent-spec skills (`skills/`), packaged as a plugin. Every piece of work enters through
`agent-spec-router`. Vocabulary: `GLOSSARY.md`.
Decisions: `.specs/STATE.md`.

The repo sits in a Google Drive folder, so the virtual environment lives outside it:

```bash
export UV_PROJECT_ENVIRONMENT=~/.venvs/lanes
uv sync
uv run pytest
uv run ruff check skills tests
```

## tlc-spec-lean

mutations: 3
