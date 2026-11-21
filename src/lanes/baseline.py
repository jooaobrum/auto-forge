"""Baselines: per-Case results of the current agent or model, keyed by the content they ran against."""

from __future__ import annotations

import json
from pathlib import Path

from lanes import brief as briefs
from lanes.results import by_case, read_file
from lanes.surface import content_hash, item_paths
from lanes.work import LanesError, Work, load_config, profile_config


def baseline_dir(root: Path, profile: str) -> Path:
    return root / ".lanes" / "baseline" / profile


def load_all(root: Path, profile: str) -> dict[str, dict]:
    directory = baseline_dir(root, profile)
    if not directory.exists():
        return {}
    return {p.stem: json.loads(p.read_text()) for p in sorted(directory.glob("*.json"))}


def record(work: Work, source: Path) -> list[str]:
    """Store a Baseline per Case from a Results file; the hash is taken at the frozen commit when frozen."""
    brief = briefs.load(work)
    surface = profile_config(load_config(work.root), brief.profile).get("surface", {})
    commit = work.frozen()["commit"] if work.path("frozen.json").exists() else None
    if not source.exists():
        raise LanesError(f"{source} is missing")
    directory = baseline_dir(work.root, brief.profile)
    directory.mkdir(parents=True, exist_ok=True)
    written = []
    for case, runs in sorted(by_case(read_file(source)).items()):
        touched = sorted({item for run in runs for item in run.touched})
        data = {
            "case": case,
            "runs": [run.metrics for run in runs],
            "touched": touched,
            "surface_hash": content_hash(work.root, item_paths(surface, touched), commit),
        }
        (directory / f"{case}.json").write_text(json.dumps(data, indent=2) + "\n")
        written.append(case)
    return written
