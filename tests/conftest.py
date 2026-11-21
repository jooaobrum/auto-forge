from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from lanes.cli import main

AGENT_CONFIG = {
    "metrics": {
        "cited_recall": {"pass_at": 0.8},
        "correctness": {"pass_at": 1},
        "input_tokens": {"budget_pct": 15},
    },
    "profiles": {
        "agent": {
            "lane": "research",
            "metrics": ["cited_recall", "correctness", "input_tokens"],
            "surface": {
                "skill:history": {"paths": ["prompts/history.md"]},
                "tool:resolve_equipment": {"paths": ["tools/resolve.py"]},
                "system_prompt": {"paths": ["prompts/system.md"], "affects_all": True},
            },
            "default_edit_scope": ["prompts/"],
            "k": {"target": 3, "affected": 1, "stable": 1},
        },
        "pipeline": {"lane": "build", "metrics": []},
        "app": {"lane": "build", "metrics": []},
    },
    "max_variants": 3,
    "budget_tokens": 1_000_000,
}

RESEARCH_BRIEF = """# History citations

**Profile**: agent
**Lane**: research

## Goal

The agent cites the history records it reads.

## Readiness

| Item | State | Why |
| --- | --- | --- |
| Dataset | ready | 40 questions |

## Metrics

- cited_recall
"""


def sh(root: Path, *args: str) -> str:
    return subprocess.run(list(args), cwd=root, check=True, capture_output=True, text=True).stdout


class Host:
    def __init__(self, root: Path, capsys):
        self.root = root
        self.capsys = capsys

    def write(self, rel: str, text: str) -> Path:
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
        return path

    def write_json(self, rel: str, data) -> Path:
        return self.write(rel, json.dumps(data, indent=2))

    def commit(self, message: str = "change") -> None:
        sh(self.root, "git", "add", "-A")
        sh(self.root, "git", "commit", "-q", "-m", message, "--allow-empty")

    def rl(self, *args: str) -> tuple[int, str]:
        self.capsys.readouterr()
        code = main(["--root", str(self.root), *args])
        return code, self.capsys.readouterr().out

    def runs(self, slug: str, variant: str, name: str, runs: list[dict]) -> None:
        self.write_json(f".lanes/work/{slug}/runs/{variant}/{name}.json", {"runs": runs})

    def experiment(self, slug: str = "exp", **fields) -> None:
        data = {"target_metric": "cited_recall", "min_delta": 0.1, "target_cases": ["q01"],
                "edit_scope": ["prompts/history.md"], "failure_mode": "reads history, does not cite it"}
        data.update(fields)
        self.write(f".lanes/work/{slug}/brief.md", RESEARCH_BRIEF)
        self.write(f".lanes/work/{slug}/experiment.md", "# Experiment\n\n**Approved**: 2026-11-21 - user: \"ok\"\n")
        self.write_json(f".lanes/work/{slug}/experiment.json", data)


@pytest.fixture
def host(tmp_path, capsys) -> Host:
    sh(tmp_path, "git", "init", "-q", "-b", "main")
    sh(tmp_path, "git", "config", "user.email", "test@example.com")
    sh(tmp_path, "git", "config", "user.name", "test")
    h = Host(tmp_path, capsys)
    h.write_json("lanes.json", AGENT_CONFIG)
    h.write("prompts/history.md", "cite what you read\n")
    h.write("prompts/system.md", "you are a maintenance agent\n")
    h.write("tools/resolve.py", "def resolve(): ...\n")
    h.commit("initial")
    return h


def run(case: str, n: int = 1, recall: float = 1.0, correct: int = 1, tokens: int = 50_000,
        touched: list | None = None) -> dict:
    return {"case": case, "run": n,
            "metrics": {"cited_recall": recall, "correctness": correct, "input_tokens": tokens},
            "touched": touched or []}


def frozen_experiment(host: Host, baseline_runs: list[dict], slug: str = "exp", **fields) -> None:
    """An Experiment with a recorded Baseline, frozen at the current commit."""
    host.experiment(slug, **fields)
    host.write_json(f".lanes/work/{slug}/base.json", {"runs": baseline_runs})
    host.commit("experiment")
    code, out = host.rl("freeze", slug)
    assert code == 0, out
    code, out = host.rl("baseline", slug, "--from", f".lanes/work/{slug}/base.json")
    assert code == 0, out
