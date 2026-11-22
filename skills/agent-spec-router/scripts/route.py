"""agent-spec-router: check the Problem, freeze a build-lane piece of work, judge an app's e2e JUnit, deliver it.

Usage: python3 route.py [--root <repo>] problem             # .specs/LAB.md ## Problem, before any model work
       python3 route.py [--root <repo>] freeze <slug>
       python3 route.py [--root <repo>] junit <slug>      # judges runs/main/*.xml
       python3 route.py [--root <repo>] deliver <slug>    # a passing gate.json, and lean's validate_verification.py
Research work is frozen, gated and delivered by agent-spec-experiment's experiment.py.
Exit: 0 ok, 1 gate fail, 2 invalid input, 5 halted (.specs/HALT exists).
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import spec_md

OK, GATE_FAIL, INVALID = 0, 1, 2


class RouteError(Exception):
    """Invalid or missing input; exit 2."""


def folder(root: Path, slug: str) -> Path:
    return root / ".specs" / "features" / slug


LEAN = Path(__file__).resolve().parents[2] / "agent-spec-lean" / "scripts"
LEAN_PLAN = LEAN / "validate_plan.py"
LEAN_VERIFICATION = LEAN / "validate_verification.py"


def _plan_text(root: Path, slug: str) -> str:
    path = folder(root, slug) / "plan.md"
    if not path.exists():
        raise RouteError(f".specs/features/{slug}/plan.md is missing - agent-spec-writer drafts it")
    return path.read_text()


def _git(root: Path, *args: str) -> str:
    done = subprocess.run(["git", *args], check=False, cwd=root, capture_output=True, text=True)
    if done.returncode != 0:
        raise RouteError(f"git {' '.join(args)} failed: {done.stderr.strip()}")
    return done.stdout


def _label_check(path: Path) -> tuple[int, int]:
    """Rows and mismatches from the label rule's result: JSON {"rows", "mismatches"} or a CSV with those columns."""
    try:
        if path.suffix.lower() == ".csv":
            with path.open(newline="") as handle:
                data = next(csv.DictReader(handle))
        else:
            data = json.loads(path.read_text())
        return int(data["rows"]), int(data["mismatches"])
    except (OSError, ValueError, KeyError, TypeError, StopIteration) as exc:
        raise RouteError(f"{path.name}: expected rows and mismatches - {exc}") from exc


def problem(root: Path) -> tuple[list[str], list[str]]:
    """Findings and warnings on `## Problem`: the five facts, the user's confirmation, the label reproduced in SQL."""
    lab = root / ".specs" / "LAB.md"
    if not lab.exists():
        raise RouteError(".specs/LAB.md is missing - write it first")
    text = lab.read_text()
    body = spec_md.section(text, "Problem")
    if not body:
        raise RouteError("no ## Problem section in .specs/LAB.md - interview the user and write it")
    findings, warnings = spec_md.problem_findings(text), []
    exclusions = spec_md.field(body, "Exclusions")
    if not exclusions or exclusions.startswith("<"):
        warnings.append('**Exclusions**: missing - the modeling plan needs it (write "none" when there are none)')
    if not re.search(r"^```sql\s*\n\s*\S.*?^```", body, re.MULTILINE | re.DOTALL):
        findings.append("no ```sql block: write the label rule as SQL over the source")
    check = spec_md.field(body, "Label check").split(" ")[0].strip("`")
    if not check or check.startswith("<"):
        findings.append("**Label check**: the file holding the label rule's result (rows, mismatches)")
    elif not (root / check).exists():
        findings.append(f"{check} is missing - run the label rule's SQL against the source and save rows, mismatches")
    else:
        rows, mismatches = _label_check(root / check)
        if rows <= 0:
            findings.append(f"{check}: the label rule ran on no rows")
        elif mismatches:
            findings.append(f"label rule disagrees with the stored label on {mismatches} of {rows} rows - "
                            "ask the user, never round it away")
    return findings, warnings


def lean(script: Path, root: Path, slug: str) -> tuple[int, str]:
    """Build-lane work goes through agent-spec-lean: its validate_plan.py and validate_verification.py judge it."""
    if not script.exists():
        raise RouteError(f"{script} is missing - install agent-spec-lean next to agent-spec-router")
    done = subprocess.run([sys.executable, str(script), slug, "--root", str(root)], check=False,
                          capture_output=True, text=True)
    return done.returncode, (done.stdout + done.stderr).strip()


def freeze(root: Path, slug: str) -> str:
    text = _plan_text(root, slug)
    if not spec_md.APPROVED.search(text):
        raise RouteError("no **Approved**: line - the user approves the plan first")
    if spec_md.field(text, "Lane").lower() == "build":
        code, out = lean(LEAN_PLAN, root, slug)
        if code != 0:
            raise RouteError(f"the plan does not pass agent-spec-lean's validate_plan.py:\n{out}")
    commit = _git(root, "rev-parse", "HEAD").strip()
    (folder(root, slug) / "frozen.json").write_text(json.dumps({"commit": commit}, indent=2))
    return commit


def junit(root: Path, slug: str) -> tuple[int, list[str]]:
    findings, rows, ran = [], [], 0
    for path in sorted((folder(root, slug) / "runs" / "main").glob("*.xml")):
        try:
            cases = ET.parse(path).getroot().iter("testcase")
            for case in cases:
                if case.find("skipped") is not None:
                    continue
                ran += 1
                name = ".".join(p for p in (case.get("classname"), case.get("name")) if p)
                failed = case.find("failure") is not None or case.find("error") is not None
                rows.append(f"| {name} | {'fail' if failed else 'pass'} |")
                if failed:
                    findings.append(f"{name}: failed")
        except ET.ParseError as exc:
            raise RouteError(f"{path.name}: malformed JUnit - {exc}") from exc
    if ran == 0:
        findings.append("no test ran")
    code = GATE_FAIL if findings else OK
    command = f"route.py junit {slug}"
    lines = [f"# Results - {slug}", "", f"Gate: `{command}` - **{'pass' if code == OK else 'fail'}**", "",
             "| Test | Result |", "| --- | --- |", *rows]
    if findings:
        lines += ["", "## Findings", ""] + [f"- {f}" for f in findings]
    (folder(root, slug) / "results.md").write_text("\n".join(lines) + "\n")
    (folder(root, slug) / "gate.json").write_text(json.dumps({"exit": code, "command": command,
                                                              "findings": findings}, indent=2))
    return code, findings


def deliver(root: Path, slug: str) -> str:
    work = folder(root, slug)
    if not (work / "gate.json").exists():
        raise RouteError("no gate has run - judge the proof first")
    last = json.loads((work / "gate.json").read_text())
    if last["exit"] != 0:
        raise RouteError("the last gate failed: " + "; ".join(last["findings"]))
    text = _plan_text(root, slug)
    if spec_md.field(text, "Lane").lower() == "build":
        code, out = lean(LEAN_VERIFICATION, root, slug)
        if code != 0:
            raise RouteError("the work is not verified - agent-spec-lean's checks, proofs and Verifier "
                             f"(references/verify.md) first; validate_verification.py says:\n{out}")
    goal = spec_md.section(text, "Goal") or spec_md.section(text, "Problem")
    since = json.loads((work / "frozen.json").read_text())["commit"] if (work / "frozen.json").exists() else None
    commits = _git(root, "log", "--oneline", f"{since}..HEAD").strip() if since else "not frozen"
    results = (work / "results.md").read_text() if (work / "results.md").exists() else ""
    lines = [f"# Delivery - {slug}", "", "## Goal", "", goal, "", "## Gate", "",
             f"`{last['command']}` exited 0", "", results, "## Commits since freeze", "", "```", commits or "none",
             "```", ""]
    (work / "delivery.md").write_text("\n".join(lines))
    return str((work / "delivery.md").relative_to(root))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="route.py", description=__doc__)
    parser.add_argument("--root", default=".")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("problem")
    for name in ("freeze", "junit", "deliver"):
        sub.add_parser(name).add_argument("slug")
    args = parser.parse_args(argv)
    halt = spec_md.halted(args.root)
    if halt:
        print(halt)
        return spec_md.HALT_EXIT
    root = Path(args.root).resolve()
    try:
        if args.command == "problem":
            findings, warnings = problem(root)
            for line in warnings:
                print(f"WARN {line}")
            for line in findings:
                print(f"FAIL {line}")
            print(f"problem: {'fail' if findings else 'pass'}")
            return GATE_FAIL if findings else OK
        if args.command == "freeze":
            print(f"frozen {args.slug} at {freeze(root, args.slug)[:12]}")
            return OK
        if args.command == "junit":
            code, findings = junit(root, args.slug)
            for line in findings:
                print(f"FAIL {line}")
            print(f"gate {args.slug}: {'pass' if code == OK else 'fail'}")
            return code
        print(f"delivered: {deliver(root, args.slug)}")
        return OK
    except RouteError as exc:
        print(f"ERROR {exc}")
        return INVALID


if __name__ == "__main__":
    sys.exit(main())
