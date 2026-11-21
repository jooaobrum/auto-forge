"""deliver.py - close a round with a decision: promote (to production) or reject.

Usage: python3 <skill-dir>/scripts/deliver.py [--root <repo>] <slug> --decision promote|reject

Needs the gate.json validate_verification.py wrote; promote needs it passing. Writes delivery.md; promote also
writes .specs/features/<slug>-mlops/spec.md for agent-spec-router to hand to agent-spec-mlops.
Exit: 0 ok, 2 invalid input.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import round_md

DECISIONS = ("promote", "reject")


class DeliverError(Exception):
    """Invalid or missing input; exit 2."""


def deliver(root: Path, slug: str, decision: str) -> Path:
    folder = round_md.round_dir(root, slug)
    gate_path = folder / "gate.json"
    if not gate_path.exists():
        raise DeliverError(f"no gate has run - run `validate_verification.py {slug}` first")
    gate = json.loads(gate_path.read_text(encoding="utf-8"))
    if gate["exit"] != 0 and decision == "promote":
        raise DeliverError("the Verification did not pass - fix it, or end with --decision reject: "
                           + "; ".join(gate["findings"][:5]))
    plan_text, _ = round_md.read_round_file(root, slug, "plan.md")
    plan = round_md.parse(plan_text or "")
    question = plan.section("Question").text if plan.section("Question") else ""
    report_text, _ = round_md.read_round_file(root, slug, "report.md")
    report = round_md.parse(report_text or "")
    results = (folder / "results.md").read_text(encoding="utf-8") if (folder / "results.md").exists() else ""
    lines = [f"# Delivery - {slug}", "", "## Goal", "", question, "", "## Decision", "", decision, ""]
    if decision == "promote":
        lines += [(f"Experiment `{gate.get('experiment')}` goes to production: "
                   f"`.specs/features/{slug}-mlops/spec.md`, for agent-spec-router."), ""]
    for name in ("Climb", "Ledger", "Next round"):
        section = report.section(name)
        if section and section.text:
            lines += [f"## {name}", "", section.text, ""]
    lines += ["## Gate", "", f"`{gate['command']}` exited {gate['exit']}", "", results]
    (folder / "delivery.md").write_text("\n".join(lines), encoding="utf-8")
    if decision == "promote":
        _promote(root, slug, gate.get("experiment"), question)
    return folder / "delivery.md"


def _promote(root: Path, slug: str, experiment: str | None, question: str) -> None:
    build = round_md.round_dir(root, f"{slug}-mlops")
    if (build / "spec.md").exists():
        return
    build.mkdir(parents=True, exist_ok=True)
    lines = [f"# {slug} - to production", "", "**Profile**: model", "**Lane**: build", f"**Round**: {slug}",
             f"**Experiment**: {experiment}", "", "## Goal", "",
             (f"Experiment `{experiment}` of round `{slug}` runs in production to the team's standard and "
              "reproduces its valid metric."), "", f"The round asked: {question}", "",
             "## Proof", "", f"`validate_prod.py {slug}-mlops` (D1-D10), then `promote.py gate {slug}-mlops`.", ""]
    (build / "spec.md").write_text("\n".join(lines), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="deliver.py", description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--root", default=".")
    parser.add_argument("slug")
    parser.add_argument("--decision", choices=DECISIONS, required=True)
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()
    try:
        print(f"delivered: {deliver(root, args.slug, args.decision).relative_to(root)}")
        return round_md.PASS
    except DeliverError as exc:
        print(f"ERROR {exc}")
        return round_md.INVALID


if __name__ == "__main__":
    sys.exit(main())
