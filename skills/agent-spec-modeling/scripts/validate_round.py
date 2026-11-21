"""validate_round.py - did the climb follow the pattern? Run before the Verification.

Usage: python3 <skill-dir>/scripts/validate_round.py [--root <repo>] <slug> [--offline] [--code <path> ...]

Validates the evidence, not the code: you write the split, training and evaluation however the problem needs
(references/patterns/). Reads .specs/features/<slug>/ledger.json and report.md:
  R0  the plan validates as approved
  R1  a ledger with iterations
  R2  the first feasible iteration is the kept baseline
  R3  the iteration budget holds
  R4  every iteration tests the baseline, a backlog hypothesis H<n> or an error-analysis finding EA-it<NN>
  R5  every iteration's code is recoverable (experiments/<id>.* or a `code` commit) and left an error analysis
  R6  every kept gain reaches the min gain with a CI above zero; the best is the last kept
  R7  every iteration has an MLflow run (unless --offline)
  R8  the report's sections are filled
  R9  every feasible iteration reports the required leakage checks
  R10 the status agrees with the checks: a failed check means infeasible
  R11 the code never references the OOT period (src/, notebooks/, the round's experiments/, --code)
Exit: 0 pass, 1 fail. Standard library only.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import round_md
import validate_plan

REPORT_SECTIONS = ["Ledger", "What worked", "What did not", "Error patterns", "Domain findings", "Next round"]
STATUSES = ("kept", "rejected", "infeasible", "failed")
GROUNDED = re.compile(r"^(baseline|H\d+\b|EA\b|EA-it\d+\b)", re.IGNORECASE)
HOLDOUT_WORDS = re.compile(r"(?<![A-Za-z0-9])oot(?![A-Za-z0-9])|out[_\- ]of[_\- ]time", re.IGNORECASE)
CODE_EXTS = (".py", ".sql", ".ipynb", ".yml", ".yaml", ".r", ".scala")
DEFAULT_REQUIRED = {"always": ["CHK-LEAK-003", "CHK-DUP-001"], "binary": ["CHK-LEAK-001"]}


def required_checks(entry: dict) -> list[str]:
    required = round_md.load_catalog().get("iteration_required", DEFAULT_REQUIRED)
    ids = list(required.get("always", []))
    if entry.get("task", "binary") == "binary":
        ids += required.get("binary", [])
    return ids


def holdout_references(root: Path, paths: list[Path], lock: dict | None) -> list[str]:
    patterns = [HOLDOUT_WORDS] + [re.compile(re.escape(day)) for day in (lock or {}).get("windows", {}).get("oot", [])]
    hits = []
    for base in paths:
        if base.is_file():
            files = [base]
        else:
            files = [Path(d) / f for d, _, names in os.walk(base) for f in names if f.lower().endswith(CODE_EXTS)]
        for path in sorted(files):
            for number, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
                if any(p.search(line) for p in patterns):
                    hits.append(f"{path.relative_to(root) if path.is_relative_to(root) else path}:{number}")
    return hits


def _tag(entry: dict) -> str:
    return f"it{entry['iteration']:02d}" if isinstance(entry.get("iteration"), int) else "it??"


def validate(root: Path, slug: str, offline: bool = False,
             code_paths: tuple = ()) -> tuple[round_md.Report, dict | None]:
    rep = round_md.Report(f"validate_round {slug}")
    plan_rep, plan = validate_plan.validate(root, slug, approved=True)
    if not plan_rep.ok:
        rep.fail("R0", "plan.md does not validate as approved; run validate_plan.py --approved")
        if plan is None:
            return rep, None
    folder = round_md.round_dir(root, slug)
    ledger_path = folder / "ledger.json"
    if not ledger_path.exists():
        rep.fail("R1", f".specs/features/{slug}/ledger.json not found; record every iteration there "
                       "(references/patterns/iteration.md)")
        return rep, None
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    entries = ledger.get("entries", [])
    if not entries:
        rep.fail("R1", "the ledger has no iterations")
        return rep, ledger

    metric = plan.section("Metric")
    min_gain = (round_md.number(metric.get("min gain")) or 0.0) if metric else 0.0
    budget_section = plan.section("Budget")
    budget = round_md.number(budget_section.get("iterations")) if budget_section else None

    kept = [e for e in entries if e.get("status") == "kept"]
    feasible = [e for e in entries if e.get("status") not in ("failed", "infeasible")]
    if (not kept or not feasible or kept[0] is not feasible[0]
            or not str(kept[0].get("hypothesis", "")).lower().startswith("baseline")):
        rep.fail("R2", "the first feasible iteration must be the kept baseline (hypothesis 'baseline')")
    if budget and len(entries) > budget:
        rep.fail("R3", f"{len(entries)} iterations above the budget of {int(budget)}")

    backlog_section = plan.section("Backlog")
    backlog = {h.id for h in backlog_section.items} if backlog_section else set()
    for entry in entries:
        tag, hypothesis = _tag(entry), str(entry.get("hypothesis", ""))
        match = GROUNDED.match(hypothesis)
        if not match:
            rep.fail("R4", f"{tag}: hypothesis {hypothesis[:40]!r} must start with baseline, H<n> (backlog) "
                           "or EA-it<NN> (error analysis)")
        elif match.group(1).upper().startswith("H") and match.group(1).upper() not in backlog:
            rep.fail("R4", f"{tag}: {match.group(1)} is not in the plan's backlog; add it there first")
        snapshot = list((folder / "experiments").glob(f"{entry.get('id')}.*"))
        if not snapshot and not re.fullmatch(r"[0-9a-f]{7,40}", str(entry.get("code", ""))):
            rep.fail("R5", f"{tag}: code not recoverable (experiments/{entry.get('id')}.* or a 'code' commit sha)")
        status = entry.get("status")
        if status not in STATUSES:
            rep.fail("R10", f"{tag}: status must be kept, rejected, infeasible or failed")
        if status != "failed" and not list((folder / "error_analysis").glob(f"{entry.get('id')}.*")):
            rep.fail("R5", f"{tag}: error_analysis/{entry.get('id')}.(json|md) missing")
        checks = entry.get("checks", {}) or {}
        if status in ("kept", "rejected"):
            missing = [c for c in required_checks(entry) if c not in checks]
            if missing:
                rep.fail("R9", f"{tag}: leakage checks not reported: {', '.join(missing)} "
                               "(references/patterns/leakage-checks.md)")
            if any(not c.get("ok") for c in checks.values()):
                rep.fail("R10", f"{tag}: a check failed but the status is {status}; it must be infeasible")
        if status == "infeasible" and checks and all(c.get("ok") for c in checks.values()):
            rep.fail("R10", f"{tag}: infeasible without a failed check; say which check failed")
        if status == "kept" and kept and entry is not kept[0]:
            ci = entry.get("ci") or [None, None]
            delta = entry.get("delta")
            if delta is None or delta < min_gain - 1e-12 or ci[0] is None or ci[0] <= 0:
                rep.fail("R6", f"{tag}: kept without delta >= {min_gain:g} and a CI above 0")
        if not offline and not entry.get("mlflow_run_id"):
            rep.fail("R7", f"{tag}: no MLflow run (log every iteration, or pass --offline and say so in the report)")
    if kept and ledger.get("best") != kept[-1].get("id"):
        rep.fail("R6", "the ledger's best is not the last kept iteration")

    report_text, _ = round_md.read_round_file(root, slug, "report.md")
    if report_text is None:
        rep.fail("R8", "report.md missing; start it with round_report.py")
    else:
        report = round_md.parse(report_text)
        for name in REPORT_SECTIONS:
            section = report.section(name)
            if section is None or len(section.text) < 10 or section.text.startswith("<"):
                rep.fail("R8", f"report.md: '## {name}' missing or not filled")

    lock_file = validate_plan.lock_path(root, plan)
    lock = None
    if lock_file is not None and lock_file.exists():
        try:
            lock = json.loads(lock_file.read_text(encoding="utf-8"))
        except ValueError:
            lock = None
    candidates = [Path(root) / "src", Path(root) / "notebooks", folder / "experiments"]
    candidates += [Path(p) if os.path.isabs(p) else Path(root) / p for p in code_paths]
    hits = holdout_references(Path(root), [p for p in candidates if p.exists()], lock)
    if hits:
        rep.fail("R11", f"the round's code references the OOT period (only the Verification reads it): "
                        f"{', '.join(hits[:8])}")
    return rep, ledger


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="validate_round.py", description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--root", default=".")
    parser.add_argument("slug")
    parser.add_argument("--offline", action="store_true")
    parser.add_argument("--code", nargs="*", default=[], help="more code paths to scan for OOT references")
    args = parser.parse_args(argv)
    rep, _ = validate(Path(args.root).resolve(), args.slug, offline=args.offline, code_paths=tuple(args.code))
    rep.print()
    return round_md.PASS if rep.ok else round_md.FAIL


if __name__ == "__main__":
    sys.exit(main())
