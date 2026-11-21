"""Read a round's files: plan.md, report.md and verification.md, and collect a gate's findings.

Ported from ds-factory's exp-hillclimb `_spec.py`, itself derived from tlc-spec-lean (Tech Leads Club, CC-BY-4.0).
The round files are markdown with a small, fixed grammar:
  **Key**: value                  header fields (before the first `## `)
  ## Section                      sections
  ### H1 - title                  items inside a section (backlog hypotheses)
  - Key: value                    fields inside a section or an item
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

NUMBER = re.compile(r"[-+]?\d+(?:\.\d+)?")
ITEM_HEAD = re.compile(r"^###\s+([A-Z]+\d+)\s*[-—–]\s*(.+?)\s*$")
HEADER_FIELD = re.compile(r"^\*\*([^*]+)\*\*:\s*(.*)$")
LIST_FIELD = re.compile(r"^-\s+([^:]+?):\s*(.*)$")
PASS, FAIL, INVALID = 0, 1, 2


@dataclass
class Item:
    id: str
    title: str
    fields: dict = field(default_factory=dict)
    lines: list = field(default_factory=list)

    def get(self, key: str, default: str = "") -> str:
        return self.fields.get(key.lower(), default)


@dataclass
class Section:
    name: str
    lines: list = field(default_factory=list)
    fields: dict = field(default_factory=dict)
    items: list = field(default_factory=list)

    @property
    def text(self) -> str:
        return "\n".join(self.lines).strip()

    def get(self, key: str, default: str = "") -> str:
        return self.fields.get(key.lower(), default)


@dataclass
class Doc:
    title: str
    header: dict
    sections: dict

    def section(self, name: str) -> Section | None:
        return self.sections.get(name.lower())

    def h(self, key: str, default: str = "") -> str:
        return self.header.get(key.lower(), default)


def parse(text: str) -> Doc:
    title, header, sections = "", {}, {}
    current: Section | None = None
    item: Item | None = None
    for raw in text.splitlines():
        line = raw.rstrip()
        if line.startswith("# ") and not title:
            title = line[2:].strip()
            continue
        if line.startswith("## "):
            current = Section(line[3:].strip())
            sections[current.name.lower()] = current
            item = None
            continue
        if current is None:
            match = HEADER_FIELD.match(line.strip())
            if match:
                header[match.group(1).strip().lower()] = match.group(2).strip()
            continue
        match = ITEM_HEAD.match(line)
        if match:
            item = Item(match.group(1), match.group(2))
            current.items.append(item)
            continue
        target = item if item is not None else current
        target.lines.append(line)
        match = LIST_FIELD.match(line.strip())
        if match:
            target.fields.setdefault(match.group(1).strip().lower(), match.group(2).strip())
    return Doc(title, header, sections)


def number(text: str | None) -> float | None:
    match = NUMBER.search(text or "")
    return float(match.group(0)) if match else None


def path_value(text: str) -> str:
    """The path in a `- Key: value` field: the first backticked token, else the first word."""
    match = re.search(r"`([^`]+)`", text or "")
    if match:
        return match.group(1).strip()
    return (text or "").split(" ")[0].strip()


def table_rows(section: Section) -> list[list[str]]:
    """Rows of the first markdown table in a section, header excluded, as lists of cells."""
    rows = []
    for line in section.lines:
        cells_line = line.strip()
        if not cells_line.startswith("|"):
            continue
        cells = [c.strip() for c in cells_line.strip("|").split("|")]
        if all(re.fullmatch(r":?-{2,}:?", c) for c in cells if c):
            continue
        rows.append(cells)
    return rows[1:] if rows else []


def round_dir(root: Path, slug: str) -> Path:
    return Path(root) / ".specs" / "features" / slug


def read_round_file(root: Path, slug: str, name: str) -> tuple[str | None, Path]:
    path = round_dir(root, slug) / name
    return (path.read_text(encoding="utf-8") if path.exists() else None), path


def skill_dir() -> Path:
    return Path(__file__).resolve().parent.parent


def load_catalog() -> dict:
    path = skill_dir() / "references" / "check_catalog.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


class Report:
    """Collects rule failures. Every message starts with its rule code, e.g. [P8]."""

    def __init__(self, name: str):
        self.name = name
        self.errors: list = []
        self.warnings: list = []

    def fail(self, code: str, msg: str) -> None:
        self.errors.append(f"[{code}] {msg}")

    def warn(self, code: str, msg: str) -> None:
        self.warnings.append(f"[{code}] {msg}")

    def codes(self) -> set:
        return {e[1:e.index("]")] for e in self.errors}

    @property
    def ok(self) -> bool:
        return not self.errors

    def print(self) -> None:
        for line in self.warnings:
            print(f"WARN {line}")
        for line in self.errors:
            print(f"FAIL {line}")
        count = len(self.errors)
        verdict = "pass" if self.ok else f"fail ({count} problem{'' if count == 1 else 's'})"
        print(f"{self.name}: {verdict}")
