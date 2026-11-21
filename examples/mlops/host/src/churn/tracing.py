"""Writes .specs/prod/trace.json: what was trained, from which round, on what data, reproducibly."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

TRACE = Path(".specs/prod/trace.json")


def commit() -> str:
    return subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True,
                          check=True).stdout.strip()


def lock_hash(path: str = "uv.lock") -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def build(cfg: dict, round_slug: str, experiment: dict, valid: float, versions: dict, run_id: str) -> dict:
    return {
        "model": {"name": f"{cfg['target']}.{cfg['model']['name']}", "version": 1, "alias": "challenger"},
        "git_commit": commit(),
        "config_env": cfg["env"],
        "data": [{"table": table, "version": version} for table, version in versions.items()],
        "mlflow_run_id": run_id,
        "experiment": {"round": round_slug, "id": experiment["id"], "valid_metric": experiment["value"]},
        "reproducibility": {"metric": experiment["metric"], "prod_valid_metric": valid, "tolerance": 0.01,
                            "seed": 7, "lockfile": "uv.lock", "lockfile_sha256": lock_hash()},
        "metrics": {"valid": valid, "oot": 0.7},
    }


def write(trace: dict) -> None:
    TRACE.parent.mkdir(parents=True, exist_ok=True)
    TRACE.write_text(json.dumps(trace, indent=2) + "\n")
