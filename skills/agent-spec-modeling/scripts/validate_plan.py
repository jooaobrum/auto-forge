"""validate_plan.py - is the round ready to climb?

Usage: python3 <skill-dir>/scripts/validate_plan.py [--root <repo>] <slug> [--approved]

Reads .specs/features/<slug>/plan.md. Content rules only:
  P0  the plan exists
  P1  **Profile**: model and a **Data kind**: tabular or image
  P2  every section is there and filled
  P3  the question is a full sentence
  P4  the target (## Problem of .specs/LAB.md) has a business definition, label rule, prediction time,
      exclusions and the user's confirmation
  P5  the lessons loaded, or "none"
  P6  the table as `catalog.schema.table` and a split lock: train < valid < oot time windows, no overlap,
      each with a positive row count
  P7  a primary metric from the fixed list, a min gain >= 0, a reporting period
  P8  an iteration budget
  P9  the largest valid-to-OOT drop allowed, in (0, 1]
  P10 a backlog of hypotheses H<n>, each with an idea, a why and a source
  A1  with --approved (or once the plan carries one): **Approved**: <date> - user: "<their words>"
Exit: 0 pass, 1 fail, 5 halted (.specs/HALT exists). Standard library only.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import round_md
import spec_md

DATA_KINDS = {"tabular", "image"}
PERIODS = {"day", "week", "month", "quarter"}
SECTIONS = ["Question", "Target", "Lessons loaded", "Data", "Metric", "Budget", "Max drop", "Backlog"]
TARGET_FIELDS = ("Target", "Label rule", "Prediction time", "Exclusions")
APPROVED = re.compile(r'^\d{4}-\d{2}-\d{2}\s+-\s+user:\s+".*\S.*"$')
TABLE = re.compile(r"`[A-Za-z0-9_]+\.[A-Za-z0-9_]+\.[A-Za-z0-9_]+`")
DEFAULT_DEFINITION = ".specs/LAB.md"


def lock_problems(path: Path) -> list[str]:
    """The split pattern: three ordered, non-overlapping time windows with counts (references/patterns/split.md)."""
    try:
        lock = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return [f"not readable JSON ({exc})"]
    out = [f"missing '{key}'" for key in ("table", "time_col", "label_col", "windows", "counts") if key not in lock]
    windows = lock.get("windows", {})
    if all(s in windows and len(windows[s]) == 2 for s in ("train", "valid", "oot")):
        train, valid, oot = windows["train"], windows["valid"], windows["oot"]
        if not (train[0] <= train[1] < valid[0] <= valid[1] < oot[0] <= oot[1]):
            out.append("windows must be ordered train < valid < oot with no overlap")
    else:
        out.append("windows needs train, valid and oot as [start, end]")
    counts = lock.get("counts", {})
    if not all(isinstance(counts.get(s), int) and counts[s] > 0 for s in ("train", "valid", "oot")):
        out.append("counts needs a positive row count for train, valid and oot")
    return out


def max_drop(plan: round_md.Doc | None) -> float | None:
    section = plan.section("Max drop") if plan else None
    if section is None:
        return None
    for key in ("valid to oot", "valid->oot", "valid→oot"):
        if section.get(key):
            return round_md.number(section.get(key))
    return None


def lock_path(root: Path, plan: round_md.Doc | None) -> Path | None:
    data = plan.section("Data") if plan else None
    lock = round_md.path_value(data.get("lock")) if data else ""
    return Path(root) / lock if lock else None


def _target(rep: round_md.Report, root: Path, doc: round_md.Doc) -> None:
    section = doc.section("Target")
    definition = round_md.path_value(section.get("definition")) if section else ""
    definition = definition or DEFAULT_DEFINITION
    path = Path(root) / definition
    if not path.exists():
        rep.fail("P4", f"{definition} not found: ## Target needs '- Definition: `.specs/LAB.md`' with its ## Problem")
        return
    text = path.read_text(encoding="utf-8")
    if not spec_md.section(text, "Problem"):
        rep.fail("P4", f"{definition} has no ## Problem; agent-spec-router writes it with the user")
        return
    for finding in spec_md.problem_findings(text, TARGET_FIELDS):
        rep.fail("P4", f"{definition} ## Problem: {finding}")


def validate(root: Path, slug: str, approved: bool | None = None) -> tuple[round_md.Report, round_md.Doc | None]:
    rep = round_md.Report(f"validate_plan {slug}")
    text, _ = round_md.read_round_file(root, slug, "plan.md")
    if text is None:
        rep.fail("P0", f".specs/features/{slug}/plan.md not found; start it from references/plan.md")
        return rep, None
    doc = round_md.parse(text)

    if doc.h("profile").strip("` ").lower() != "model" or doc.h("data kind").strip("` ").lower() not in DATA_KINDS:
        rep.fail("P1", f"**Profile**: model and **Data kind**: one of {sorted(DATA_KINDS)}")
    for name in SECTIONS:
        section = doc.section(name)
        if section is None or (not section.text and not section.items):
            rep.fail("P2", f"'## {name}' missing or empty")

    question = doc.section("Question")
    if question and len(question.text) < 20:
        rep.fail("P3", "## Question: one full sentence - what is predicted, for whom, what good looks like")

    _target(rep, root, doc)

    lessons = doc.section("Lessons loaded")
    if lessons and not re.search(r"\bL-?\d+\b|\bnone\b", lessons.text, re.IGNORECASE):
        rep.fail("P5", "## Lessons loaded: the ids of the lessons that apply, or 'none'")

    data = doc.section("Data")
    if data:
        if not TABLE.search(data.text):
            rep.fail("P6", "## Data must name the table as `catalog.schema.table`")
        lock = lock_path(root, doc)
        if lock is None or not lock.exists():
            rep.fail("P6", "## Data needs '- Lock: `.specs/split.lock`' and the file must exist "
                           "(references/patterns/split.md)")
        else:
            for problem in lock_problems(lock):
                rep.fail("P6", f"{round_md.path_value(data.get('lock'))}: {problem}")

    metric = doc.section("Metric")
    if metric:
        if metric.get("primary").strip("` ").lower() not in spec_md.METRICS:
            rep.fail("P7", f"- Primary: one of {', '.join(spec_md.METRICS)}")
        gain = round_md.number(metric.get("min gain"))
        if gain is None or gain < 0:
            rep.fail("P7", "- Min gain: the smallest gain worth keeping (>= 0)")
        if metric.get("period").strip("` ").lower() not in PERIODS:
            rep.fail("P7", f"- Period: one of {sorted(PERIODS)}")

    budget = doc.section("Budget")
    iterations = round_md.number(budget.get("iterations")) if budget else None
    if budget and (iterations is None or iterations < 1 or iterations != int(iterations)):
        rep.fail("P8", "## Budget needs '- Iterations: <positive integer>'")

    drop = max_drop(doc)
    if doc.section("Max drop") and (drop is None or not 0 < drop <= 1):
        rep.fail("P9", "## Max drop needs '- Valid to OOT: <number in (0, 1]>'")

    backlog = doc.section("Backlog")
    if backlog:
        if not backlog.items:
            rep.fail("P10", "## Backlog needs at least one '### H1 - <idea>'")
        seen = set()
        for hypothesis in backlog.items:
            if hypothesis.id in seen:
                rep.fail("P10", f"{hypothesis.id} declared twice")
            seen.add(hypothesis.id)
            if len(hypothesis.get("idea")) < 8 or len(hypothesis.get("why")) < 8:
                rep.fail("P10", f"{hypothesis.id}: '- Idea:' and '- Why:' must both say something concrete")
            if not hypothesis.get("source"):
                rep.fail("P10", f"{hypothesis.id}: '- Source:' (eda, domain, lesson L-NNN, error analysis, "
                                "recipe <name>)")

    stated = doc.h("approved")
    wanted = approved or (approved is None and stated and not stated.startswith("<"))
    if wanted and not APPROVED.match(stated):
        rep.fail("A1", '**Approved**: YYYY-MM-DD - user: "<their words>" - never one the user did not give')
    return rep, doc


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="validate_plan.py", description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--root", default=".")
    parser.add_argument("slug")
    parser.add_argument("--approved", action="store_true")
    args = parser.parse_args(argv)
    halt = spec_md.halted(args.root)
    if halt:
        print(halt)
        return spec_md.HALT_EXIT
    rep, _ = validate(Path(args.root).resolve(), args.slug, approved=True if args.approved else None)
    rep.print()
    return round_md.PASS if rep.ok else round_md.FAIL


if __name__ == "__main__":
    sys.exit(main())
