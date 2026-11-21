"""The Brief: Shape's output, refused while a field is missing or an item is not ready."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from lanes.work import LANES, PROFILES, LanesError, Work, load_config

READINESS = ("ready", "needs attention", "not ready")


@dataclass
class Brief:
    goal: str = ""
    profile: str = ""
    lane: str = ""
    plan: str = ""
    readiness: list = field(default_factory=list)  # (item, state)
    metrics: list = field(default_factory=list)


def _field(text: str, name: str) -> str:
    match = re.search(rf"^\**{name}\**\s*:\s*\**\s*`?([\w./-]+)`?", text, re.IGNORECASE | re.MULTILINE)
    return match.group(1).strip().lower() if match else ""


def _section(text: str, heading: str) -> str:
    match = re.search(rf"^##\s+{heading}\s*$(.*?)(?=^##\s|\Z)", text, re.IGNORECASE | re.MULTILINE | re.DOTALL)
    return match.group(1).strip() if match else ""


def parse(text: str) -> Brief:
    brief = Brief(goal=_section(text, "Goal"), profile=_field(text, "Profile"), lane=_field(text, "Lane"))
    plan = re.search(r"^\**Plan\**\s*:\s*`?([^`\s]+)`?", text, re.IGNORECASE | re.MULTILINE)
    brief.plan = plan.group(1) if plan else ""
    for line in _section(text, "Readiness").splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) >= 2 and cells[1].lower() in READINESS:
            brief.readiness.append((cells[0], cells[1].lower()))
    for line in _section(text, "Metrics").splitlines():
        match = re.match(r"\s*[-*]\s+`?([\w.-]+)`?", line)
        if match:
            brief.metrics.append(match.group(1))
    return brief


def load(work: Work) -> Brief:
    path = work.path("brief.md")
    if not path.exists():
        raise LanesError(f".lanes/work/{work.slug}/brief.md is missing")
    return parse(path.read_text())


def check(work: Work) -> tuple[int, list[str], list[str]]:
    """Return (exit code, errors, warnings)."""
    brief = load(work)
    errors, warnings = [], []
    if not brief.goal:
        errors.append("missing: goal (## Goal has no text)")
    if brief.profile not in PROFILES:
        errors.append(f"missing: profile (one of {', '.join(PROFILES)})")
    if brief.lane not in LANES:
        errors.append(f"missing: lane (one of {', '.join(LANES)})")
    for item, state in brief.readiness:
        if state == "not ready":
            errors.append(f"not ready: {item}")
        elif state == "needs attention":
            warnings.append(f"needs attention: {item}")
    if brief.lane == "research" and brief.profile in PROFILES:
        declared = load_config(work.root).get("profiles", {}).get(brief.profile, {}).get("metrics", [])
        if not any(m in declared for m in brief.metrics):
            errors.append(
                f"research lane needs a metric declared for profile `{brief.profile}` in lanes.json "
                f"(declared: {', '.join(declared) or 'none'}; brief names: {', '.join(brief.metrics) or 'none'})"
            )
    return (2 if errors else 0), errors, warnings
