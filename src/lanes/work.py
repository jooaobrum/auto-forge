"""The host repo, its config and one piece of work: the files every command reads and writes."""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path

OK, GATE_FAIL, INVALID, VARIANT_CAP, BUDGET_SPENT = 0, 1, 2, 3, 4

PROFILES = ("app", "pipeline", "model", "agent")
LANES = ("build", "research")


class LanesError(Exception):
    """Invalid or missing input; the CLI turns it into exit 2."""


@dataclass
class Work:
    root: Path
    slug: str

    @property
    def dir(self) -> Path:
        return self.root / ".lanes" / "work" / self.slug

    @property
    def runs_dir(self) -> Path:
        return self.dir / "runs"

    def path(self, name: str) -> Path:
        return self.dir / name

    def read_json(self, name: str) -> dict:
        path = self.path(name)
        if not path.exists():
            raise LanesError(f"{path.relative_to(self.root)} is missing")
        try:
            return json.loads(path.read_text())
        except json.JSONDecodeError as exc:
            raise LanesError(f"{path.relative_to(self.root)} is not valid JSON: {exc}") from exc

    def write_json(self, name: str, data: dict) -> None:
        self.dir.mkdir(parents=True, exist_ok=True)
        self.path(name).write_text(json.dumps(data, indent=2) + "\n")

    def experiment(self) -> dict | None:
        return self.read_json("experiment.json") if self.path("experiment.json").exists() else None

    def frozen(self) -> dict:
        if not self.path("frozen.json").exists():
            raise LanesError(f"{self.slug} is not frozen - run `rl freeze {self.slug}` after approval")
        return self.read_json("frozen.json")


def load_config(root: Path) -> dict:
    path = root / "lanes.json"
    if not path.exists():
        raise LanesError("lanes.json is missing at the repo root")
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        raise LanesError(f"lanes.json is not valid JSON: {exc}") from exc


def profile_config(config: dict, profile: str) -> dict:
    profiles = config.get("profiles", {})
    if profile not in profiles:
        raise LanesError(f"lanes.json declares no profile `{profile}`")
    return profiles[profile]


def git(root: Path, *args: str) -> str:
    try:
        done = subprocess.run(["git", *args], check=False, cwd=root, capture_output=True, text=True)
    except FileNotFoundError as exc:
        raise LanesError("git is not installed") from exc
    if done.returncode != 0:
        raise LanesError(f"git {' '.join(args)} failed: {done.stderr.strip()}")
    return done.stdout
