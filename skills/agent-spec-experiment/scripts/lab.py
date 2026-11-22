"""The work folder, the plan merged with `.specs/LAB.md` and its defaults, Results files, the surface and git."""

from __future__ import annotations

import csv
import fnmatch
import hashlib
import json
import re
import subprocess
import xml.etree.ElementTree as ET
from collections import defaultdict
from dataclasses import dataclass, field
from fractions import Fraction
from pathlib import Path

import spec_md

OK, GATE_FAIL, INVALID, VARIANT_CAP, BUDGET_SPENT = 0, 1, 2, 3, 4
DEFAULT_VARIANTS = 3
DEFAULT_K = {"target": 3, "affected": 1, "stable": 1}
DEFAULT_GUARDRAILS = {"input_tokens": 15, "latency_ms": 20}
DEFAULT_BAR = {"cited_recall": "1", "read_recall": "1", "route_match": "1"}


class LabError(Exception):
    """Invalid or missing input; the CLI turns it into exit 2."""


# --- the work folder ------------------------------------------------------------------------------------------

@dataclass
class Work:
    root: Path
    slug: str

    @property
    def dir(self) -> Path:
        return self.root / ".specs" / "features" / self.slug

    @property
    def runs_dir(self) -> Path:
        return self.dir / "runs"

    def path(self, name: str) -> Path:
        return self.dir / name

    def read_json(self, name: str) -> dict:
        path = self.path(name)
        if not path.exists():
            raise LabError(f"{path.relative_to(self.root)} is missing")
        return json.loads(path.read_text())

    def write_json(self, name: str, data) -> None:
        self.dir.mkdir(parents=True, exist_ok=True)
        self.path(name).write_text(json.dumps(data, indent=2) + "\n")

    def frozen(self) -> dict:
        if not self.path("frozen.json").exists():
            raise LabError(f"{self.slug} is not frozen - freeze it after the user approves the plan")
        return self.read_json("frozen.json")


def git(root: Path, *args: str) -> str:
    try:
        done = subprocess.run(["git", *args], check=False, cwd=root, capture_output=True, text=True)
    except FileNotFoundError as exc:
        raise LabError("git is not installed") from exc
    if done.returncode != 0:
        raise LabError(f"git {' '.join(args)} failed: {done.stderr.strip()}")
    return done.stdout


# --- the plan, merged with LAB.md -----------------------------------------------------------------------------

def frac(value) -> Fraction:
    return Fraction(str(value).strip().lstrip("+").rstrip("%").strip())


@dataclass
class Metric:
    name: str
    pass_at: str = ""
    guardrail: str = ""
    target: str = ""


@dataclass
class Spec:
    text: str
    profile: str = ""
    lane: str = ""
    approved: bool = False
    failure_mode: str = ""
    dataset: str = ""
    budget: int = 0
    variants: int = DEFAULT_VARIANTS
    k: dict = field(default_factory=lambda: dict(DEFAULT_K))
    cases: dict = field(default_factory=dict)          # case id -> row
    target_cases: list = field(default_factory=list)
    metrics: dict = field(default_factory=dict)        # name -> Metric
    surface: dict = field(default_factory=dict)        # item -> {"paths": [...], "affects_all": bool}
    edit_scope: list = field(default_factory=list)

    @property
    def target_metric(self) -> Metric | None:
        return next((m for m in self.metrics.values() if m.target), None)

    def thresholds(self) -> dict:
        bars = {name: m.pass_at for name, m in self.metrics.items() if m.pass_at}
        for name, bar in DEFAULT_BAR.items():
            bars.setdefault(name, bar)
        return bars

    def guardrails(self) -> dict:
        out = {}
        for name, metric in self.metrics.items():
            if metric.guardrail:
                out[name] = frac(metric.guardrail)
            elif name in DEFAULT_GUARDRAILS:
                out[name] = Fraction(DEFAULT_GUARDRAILS[name])
        return out


def _metrics(text: str) -> dict:
    out = {}
    for row in spec_md.table(spec_md.section(text, "Metrics")):
        name = row.get("Metric", "")
        if name:
            out[name] = Metric(name, row.get("Pass at", ""), row.get("Guardrail", ""), row.get("Target", ""))
    return out


def _surface(text: str) -> dict:
    out = {}
    for row in spec_md.table(spec_md.section(text, "Surface")):
        item = row.get("Item", "")
        if item:
            out[item] = {"paths": spec_md.split_list(row.get("Paths", "")),
                         "affects_all": spec_md.is_yes(row.get("Affects all", ""))}
    return out


def _k(text: str) -> dict:
    k = dict(DEFAULT_K)
    for tier, value in re.findall(r"(target|affected|stable)\s+(\d+)", spec_md.field(text, "k"), re.IGNORECASE):
        k[tier.lower()] = int(value)
    return k


def lab_text(root: Path) -> str:
    path = root / ".specs" / "LAB.md"
    return path.read_text() if path.exists() else ""


def load_spec(work: Work) -> Spec:
    path = work.path("plan.md")
    if not path.exists():
        raise LabError(f".specs/features/{work.slug}/plan.md is missing")
    text, lab = path.read_text(), lab_text(work.root)
    spec = Spec(text=text)
    spec.profile = spec_md.field(text, "Profile").lower()
    spec.lane = spec_md.field(text, "Lane").lower()
    spec.approved = bool(spec_md.APPROVED.search(text))
    spec.failure_mode = spec_md.field(text, "Failure mode")
    spec.dataset = spec_md.field(text, "Dataset")
    budget = spec_md.field(text, "Budget") or spec_md.field(lab, "Budget")
    spec.budget = int(re.sub(r"[^\d]", "", budget) or 0)
    variants = spec_md.field(text, "Variants")
    spec.variants = int(variants) if variants.isdigit() else DEFAULT_VARIANTS
    spec.k = _k(text)
    for row in spec_md.table(spec_md.section(text, "Cases")):
        if row.get("Case"):
            spec.cases[row["Case"]] = row
    spec.target_cases = spec_md.split_list(spec_md.field(text, "Target cases"))
    merged = _metrics(lab)
    for name, metric in _metrics(text).items():
        base = merged.get(name, Metric(name))
        merged[name] = Metric(name, metric.pass_at or base.pass_at, metric.guardrail or base.guardrail,
                              metric.target or base.target)
    spec.metrics = merged
    spec.surface = {**_surface(lab), **_surface(text)}
    scope = spec_md.bullets(spec_md.section(text, "Edit Scope")) or spec_md.bullets(spec_md.section(lab, "Edit Scope"))
    spec.edit_scope = scope
    return spec


# --- Results files --------------------------------------------------------------------------------------------

@dataclass
class Run:
    case: str
    run: int
    metrics: dict
    touched: list = field(default_factory=list)
    trace: str = ""
    extra: dict = field(default_factory=dict)  # read / cited / route, when the run reports them


def _number(text: str):
    for cast in (int, float):
        try:
            return cast(text)
        except ValueError:
            pass
    return text


def _read_json(path: Path) -> list[Run]:
    data = json.loads(path.read_text())
    if not isinstance(data, dict) or not isinstance(data.get("runs"), list):
        raise TypeError('expected {"runs": [...]}')
    runs = []
    for item in data["runs"]:
        if "case" not in item or not isinstance(item.get("metrics", {}), dict):
            raise ValueError("every run needs `case` and a `metrics` object")
        extra = {key: item[key] for key in ("read", "cited", "route") if key in item}
        runs.append(Run(str(item["case"]), int(item.get("run", 1)), dict(item.get("metrics", {})),
                        list(item.get("touched", [])), str(item.get("trace", "")), extra))
    return runs


def _read_csv(path: Path) -> list[Run]:
    with path.open(newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames or "case" not in reader.fieldnames:
            raise ValueError("expected a `case` column")
        seen: dict = defaultdict(int)
        runs = []
        for row in reader:
            case = row.pop("case")
            seen[case] += 1
            runs.append(Run(case, seen[case], {k: _number(v) for k, v in row.items() if k}))
        return runs


def _read_junit(path: Path) -> list[Run]:
    runs = []
    for case in ET.parse(path).getroot().iter("testcase"):
        if case.find("skipped") is not None:
            continue
        name = ".".join(p for p in (case.get("classname"), case.get("name")) if p)
        failed = case.find("failure") is not None or case.find("error") is not None
        runs.append(Run(name, 1, {"passed": 0 if failed else 1}))
    return runs


READERS = {".json": _read_json, ".csv": _read_csv, ".xml": _read_junit}


def read_file(path: Path) -> list[Run]:
    reader = READERS.get(path.suffix.lower())
    if reader is None:
        raise LabError(f"{path.name}: not a Results file (use .json, .csv or JUnit .xml)")
    try:
        return reader(path)
    except (ValueError, KeyError, TypeError, ET.ParseError, csv.Error) as exc:
        raise LabError(f"{path.name}: malformed Results file - {exc}") from exc


def read_dir(directory: Path) -> list[Run]:
    if not directory.exists():
        return []
    runs: list[Run] = []
    for path in sorted(p for p in directory.rglob("*") if p.is_file()):
        runs.extend(read_file(path))
    return runs


def by_case(runs: list[Run]) -> dict[str, list[Run]]:
    grouped: dict = defaultdict(list)
    for run in runs:
        grouped[run.case].append(run)
    return dict(grouped)


# --- the surface and the Edit Scope ---------------------------------------------------------------------------

def in_scope(path: str, scope: list[str]) -> bool:
    for entry in scope:
        if path == entry or fnmatch.fnmatch(path, entry) or (entry.endswith("/") and path.startswith(entry)):
            return True
    return False


def overlaps(path: str, scope: list[str]) -> bool:
    if in_scope(path, scope):
        return True
    prefix = path if path.endswith("/") else path + "/"
    return any(entry.startswith(prefix) for entry in scope)


def item_paths(surface: dict, items: list[str]) -> list[str]:
    paths: set = set()
    for item in items:
        paths.update(surface.get(item, {}).get("paths", []))
    return sorted(paths)


def _files_at(root: Path, commit: str | None, path: str) -> list[tuple[str, bytes]]:
    if commit is None:
        target = root / path
        if target.is_dir():
            return [(str(p.relative_to(root)), p.read_bytes()) for p in sorted(target.rglob("*")) if p.is_file()]
        return [(path, target.read_bytes())] if target.exists() else [(path, b"<absent>")]
    listing = subprocess.run(["git", "ls-tree", "-r", "-z", "--name-only", commit, "--", path.rstrip("/")],
                             check=False, cwd=root, capture_output=True, text=True).stdout.split("\0")
    listing = [name for name in listing if name]
    if not listing:
        return [(path, b"<absent>")]
    return [(name, subprocess.run(["git", "show", f"{commit}:{name}"], check=False, cwd=root,
                                  capture_output=True).stdout) for name in listing]


def content_hash(root: Path, paths: list[str], commit: str | None = None) -> str:
    digest = hashlib.sha256()
    for path in sorted(paths):
        for name, data in _files_at(root, commit, path):
            digest.update(name.encode() + b"\0" + hashlib.sha256(data).digest())
    return digest.hexdigest()


def out_of_scope(work: Work, commit: str, scope: list[str]) -> list[str]:
    changed = set(git(work.root, "diff", "--name-only", "--no-renames", "-z", commit).split("\0"))
    changed |= set(git(work.root, "ls-files", "--others", "--exclude-standard", "-z").split("\0"))
    changed.discard("")
    own = f".specs/features/{work.slug}/"
    return sorted(p for p in changed
                  if not p.startswith(own) and not p.startswith(".specs/baseline/") and not in_scope(p, scope))


# --- Baselines ------------------------------------------------------------------------------------------------

def baseline_dir(root: Path, profile: str) -> Path:
    return root / ".specs" / "baseline" / profile


def load_baselines(root: Path, profile: str) -> dict:
    directory = baseline_dir(root, profile)
    if not directory.exists():
        return {}
    return {p.stem: json.loads(p.read_text()) for p in sorted(directory.glob("*.json")) if p.stem != "streaks"}
