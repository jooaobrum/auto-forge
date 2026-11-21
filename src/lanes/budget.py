"""The token budget: spent from the Results files, raised only with the user's words."""

from __future__ import annotations

import datetime as dt
import json

from lanes.results import read_dir
from lanes.work import LanesError, Work, load_config


def _added(work: Work) -> list[dict]:
    path = work.path("budget.json")
    return json.loads(path.read_text())["added"] if path.exists() else []


def status(work: Work) -> tuple[int, int]:
    """Return (spent, budget) in input tokens."""
    experiment = work.experiment() or {}
    base = int(experiment.get("budget_tokens", load_config(work.root).get("budget_tokens", 0)))
    budget = base + sum(int(a["tokens"]) for a in _added(work))
    spent = sum(int(run.metrics.get("input_tokens", 0) or 0) for run in read_dir(work.runs_dir))
    return spent, budget


def spent_message(spent: int, budget: int) -> str:
    return (f"budget spent: {spent} of {budget} input tokens - stop and ask the user whether to continue; "
            f"if they say yes, run `rl budget <slug> --add <tokens> --user \"<their words>\"`")


def is_spent(work: Work) -> tuple[bool, int, int]:
    spent, budget = status(work)
    return (budget > 0 and spent >= budget), spent, budget


def add(work: Work, tokens: int, user: str | None) -> int:
    if not user or not user.strip():
        raise LanesError("--add needs --user with the user's own words approving it")
    if tokens <= 0:
        raise LanesError("--add needs a positive number of tokens")
    added = _added(work)
    today = dt.date.today().isoformat()
    added.append({"tokens": tokens, "date": today, "user": user})
    work.write_json("budget.json", {"added": added})
    lines = work.path("budget.md").read_text() if work.path("budget.md").exists() else "# Budget\n\n"
    lines += f"- {today}: +{tokens} input tokens - user: \"{user}\"\n"
    work.path("budget.md").write_text(lines)
    return status(work)[1]
