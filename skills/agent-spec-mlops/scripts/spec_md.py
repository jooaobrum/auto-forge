"""Read the markdown a spec or LAB.md is written in: bold fields, sections, tables and lists.

Shared by agent-spec-router, agent-spec-pipeline, agent-spec-experiment, agent-spec-modeling and agent-spec-mlops;
every copy is identical.
"""

from __future__ import annotations

import re
from pathlib import Path

APPROVED = re.compile(r"^\*\*Approved\*\*:\s*(?!<)\S", re.MULTILINE)
YES = {"yes", "y", "true", "x", "✓", "1"}
COMMENT = re.compile(r"<!--.*?-->", re.DOTALL)
CONFIRMED = re.compile(r'^\d{4}-\d{2}-\d{2}\s+-\s+user:\s*"[^"]*\S[^"]*"$')
METRICS = ("pr_auc", "roc_auc", "f1", "macro_f1", "accuracy", "log_loss", "brier", "rmse", "mae")
LOWER_IS_BETTER = ("log_loss", "brier", "rmse", "mae")
PROBLEM_FIELDS = ("Target", "Label rule", "Prediction time", "Cost of FP", "Cost of FN", "Metric")
HALT_EXIT = 5


def halted(root) -> str:
    """The message when `<root>/.specs/HALT` exists: every lane script stops before doing anything; "" otherwise."""
    path = Path(root) / ".specs" / "HALT"
    if not path.exists():
        return ""
    reason = next((line.strip() for line in path.read_text(errors="replace").splitlines() if line.strip()), "")
    return ("HALT .specs/HALT exists" + (f" ({reason})" if reason else "")
            + " - nothing ran; remove the file to resume")


def strip_comments(text: str) -> str:
    """Markdown with its HTML comments removed: template notes never become values."""
    return COMMENT.sub("", text)


def field(text: str, name: str) -> str:
    """The value after `**<name>**:` on its own line, stripped of backticks; "" when absent."""
    match = re.search(rf"^\*\*{re.escape(name)}\*\*\s*:\s*(.+?)\s*$", strip_comments(text), re.IGNORECASE | re.MULTILINE)
    return match.group(1).strip().strip("`") if match else ""


def section(text: str, heading: str, level: int = 2) -> str:
    """The text under `## <heading>` up to the next heading of the same or a higher level; "" when absent."""
    hashes = "#" * level
    match = re.search(rf"^{hashes}\s+{re.escape(heading)}\s*$(.*?)(?=^#{{1,{level}}}\s|\Z)", text,
                      re.IGNORECASE | re.MULTILINE | re.DOTALL)
    return match.group(1).strip() if match else ""


def subsections(text: str, level: int = 3) -> dict[str, str]:
    """`### <name>` blocks inside a section, in order, keyed by name."""
    hashes = "#" * level
    parts = re.split(rf"^{hashes}\s+(.+?)\s*$", text, flags=re.MULTILINE)
    return {parts[i].strip(): parts[i + 1].strip() for i in range(1, len(parts) - 1, 2)}


def _cells(line: str) -> list[str]:
    return [c.strip().strip("`").strip() for c in line.strip().strip("|").split("|")]


def table(text: str) -> list[dict[str, str]]:
    """The first markdown table in `text` as rows keyed by header; cells stripped of backticks."""
    lines: list[str] = []
    for line in strip_comments(text).splitlines():
        if line.strip().startswith("|"):
            lines.append(line)
        elif lines and line.strip():
            break
    if len(lines) < 2:
        return []
    header = _cells(lines[0])
    rows = []
    for line in lines[2:]:
        cells = _cells(line)
        cells += [""] * (len(header) - len(cells))
        rows.append(dict(zip(header, cells)))
    return rows


def bullets(text: str) -> list[str]:
    """Items of `-` or `*` lists, stripped of backticks."""
    return [m.group(1).strip().strip("`")
            for m in re.finditer(r"^\s*[-*]\s+(.+?)\s*$", strip_comments(text), re.MULTILINE)]


def split_list(cell: str) -> list[str]:
    """`a, b, c` -> ["a", "b", "c"]."""
    return [part.strip().strip("`") for part in cell.split(",") if part.strip().strip("`")]


def is_yes(cell: str) -> bool:
    return cell.strip().lower() in YES


def problem_findings(text: str, fields: tuple = PROBLEM_FIELDS) -> list[str]:
    """What the `## Problem` section of a LAB.md lacks: each field filled, a known metric, the user's confirmation."""
    body = section(text, "Problem")
    if not body:
        return ["no ## Problem section"]
    findings = []
    for name in fields:
        value = field(body, name)
        if not value or value.startswith("<"):
            findings.append(f"**{name}**: missing or not filled")
    metric = field(body, "Metric").lower()
    if "Metric" in fields and metric and not metric.startswith("<") and metric not in METRICS:
        findings.append(f"**Metric**: {metric} is not one of {', '.join(METRICS)}")
    if not CONFIRMED.match(field(body, "Confirmed")):
        findings.append('**Confirmed**: <date> - user: "<their words>" - only the user confirms the Problem')
    return findings
