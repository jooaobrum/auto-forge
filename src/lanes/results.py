"""Results files: the one shape every gate reads, from JSON, CSV or JUnit XML."""

from __future__ import annotations

import csv
import json
import xml.etree.ElementTree as ET
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

from lanes.work import LanesError


@dataclass
class Run:
    case: str
    run: int
    metrics: dict
    touched: list = field(default_factory=list)
    trace: str = ""


def _number(text: str):
    try:
        return int(text)
    except ValueError:
        try:
            return float(text)
        except ValueError:
            return text


def _read_json(path: Path) -> list[Run]:
    data = json.loads(path.read_text())
    if not isinstance(data, dict) or not isinstance(data.get("runs"), list):
        raise TypeError('expected {"runs": [...]}')
    runs = []
    for item in data["runs"]:
        if "case" not in item or not isinstance(item.get("metrics", {}), dict):
            raise ValueError("every run needs `case` and a `metrics` object")
        runs.append(
            Run(str(item["case"]), int(item.get("run", 1)), item.get("metrics", {}),
                list(item.get("touched", [])), str(item.get("trace", "")))
        )
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
    root = ET.parse(path).getroot()
    runs = []
    for case in root.iter("testcase"):
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
        raise LanesError(f"{path.name}: not a Results file (use .json, .csv or JUnit .xml)")
    try:
        return reader(path)
    except (ValueError, KeyError, TypeError, ET.ParseError, json.JSONDecodeError, csv.Error) as exc:
        raise LanesError(f"{path.name}: malformed Results file - {exc}") from exc


def read_dir(directory: Path) -> list[Run]:
    if not directory.exists():
        return []
    runs: list[Run] = []
    for path in sorted(p for p in directory.rglob("*") if p.is_file()):
        runs.extend(read_file(path))
    return runs


def by_case(runs: list[Run]) -> dict[str, list[Run]]:
    grouped: dict[str, list[Run]] = defaultdict(list)
    for run in runs:
        grouped[run.case].append(run)
    return dict(grouped)
