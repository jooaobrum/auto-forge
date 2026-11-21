# lanes

Portable harness that takes any piece of work (app, pipeline, model, agent) from offline material
to delivery, routing it to the lane whose proof can close it. Vocabulary: `GLOSSARY.md`.
Decisions: `.specs/STATE.md`.

The repo sits in a Google Drive folder, so the virtual environment lives outside it:

```bash
export UV_PROJECT_ENVIRONMENT=~/.venvs/lanes
uv sync
uv run pytest
uv run ruff check src tests
```

## tlc-spec-lean

mutations: 3
