"""validate_verification.py - the completion gate of a round. The round is done when this exits 0.

Usage: python3 <skill-dir>/scripts/validate_verification.py [--root <repo>] <slug> [--offline]

Reads .specs/features/<slug>/verification.md, written by the Verifier:
  V0  the round validates (validate_round)
  V1  a named Verifier (fresh-context or subagent; self-verified only warns) at a commit sha
  V2  it judges the ledger's best experiment
  V3  the OOT metric per period
  V4  the valid-to-OOT drop is stated right and within the plan's Max drop
  V5  both mutations killed, or n/a with a reason
  V6  every finding closed by a commit
  V7  the verdict is PASS
Writes gate.json and results.md next to it, for deliver.py.
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
import validate_round

VERIFIERS = {"fresh-context", "subagent", "self-verified"}
MUTATIONS = ("CHK-MUT-001", "CHK-MUT-002")
SHA = re.compile(r"[0-9a-f]{7,40}")


def validate(root: Path, slug: str, offline: bool = False) -> tuple[round_md.Report, dict]:
    rep = round_md.Report(f"validate_verification {slug}")
    summary: dict = {}
    round_rep, ledger = validate_round.validate(root, slug, offline=offline)
    if not round_rep.ok:
        rep.fail("V0", "the round does not validate; run validate_round.py")
        for error in round_rep.errors:
            rep.fail("V0", f"  round: {error}")
    text, _ = round_md.read_round_file(root, slug, "verification.md")
    if text is None:
        rep.fail("V1", f".specs/features/{slug}/verification.md not found; the Verifier writes it "
                       "(references/verify.md)")
        return rep, summary
    doc = round_md.parse(text)
    verifier = doc.h("verifier").strip("` ").lower()
    if verifier not in VERIFIERS:
        rep.fail("V1", f"**Verifier** must be one of {sorted(VERIFIERS)}")
    elif verifier == "self-verified":
        rep.warn("V1", "self-verified: not a fresh context; say so in the delivery")
    head = doc.h("head").strip("` ")
    if not SHA.fullmatch(head):
        rep.fail("V1", "**HEAD**: <commit sha> the Verifier judged")
    best = (ledger or {}).get("best")
    experiment = doc.h("experiment").strip("` ")
    if not best or experiment != best:
        rep.fail("V2", f"**Experiment** must be the ledger's best ({best})")

    periods = doc.section("OOT by period")
    rows = [r for r in (round_md.table_rows(periods) if periods else [])
            if len(r) >= 2 and round_md.number(r[-1]) is not None]
    if not rows:
        rep.fail("V3", "## OOT by period: one row per period, the metric in the last column")

    _, plan = validate_round.validate_plan.validate(root, slug, approved=True)
    limit = validate_round.validate_plan.max_drop(plan)
    primary = plan.section("Metric").get("primary").strip("` ").lower() if plan and plan.section("Metric") else ""
    section = doc.section("Valid vs OOT")
    valid, oot = (round_md.number(section.get("valid")), round_md.number(section.get("oot"))) if section else (None, None)
    if valid is None or oot is None:
        rep.fail("V4", "## Valid vs OOT needs '- Valid:' and '- OOT:'")
    else:
        drop = round((oot - valid) if primary in spec_md.LOWER_IS_BETTER else (valid - oot), 6)
        stated = round_md.number(section.get("drop"))
        if stated is not None and abs(stated - drop) > 1e-3:
            rep.fail("V4", f"stated drop {stated:g} does not match {drop:g}")
        if limit is not None and drop > limit + 1e-12:
            rep.fail("V4", f"valid-to-OOT drop {drop:g} above the plan's limit {limit:g}")
        summary.update(metric=primary, valid=valid, oot=oot, drop=drop, limit=limit)

    mutations = doc.section("Mutations")
    for mutation in MUTATIONS:
        line = mutations.get(mutation) if mutations else ""
        if not re.match(r"(killed\b|n/a\s+[-—–]\s+.{8,})", line, re.IGNORECASE):
            rep.fail("V5", f"{mutation} must read 'killed' (or 'n/a - <reason>')")

    findings = doc.section("Findings")
    items = [line.strip() for line in (findings.lines if findings else []) if line.strip().startswith("- ")]
    if not items:
        rep.fail("V6", "## Findings: list them, or '- none'")
    for item in items:
        if not re.fullmatch(r"-\s+none\.?", item, re.IGNORECASE) and not re.search(r"closed:\s*[0-9a-f]{7,40}\b", item):
            rep.fail("V6", f"open finding: {item[:80]!r} (close it with a commit: '| closed: <sha>')")

    verdict = doc.section("Verdict")
    if not verdict or verdict.text.split()[:1] != ["PASS"]:
        rep.fail("V7", "## Verdict must read PASS")
    summary.update(verifier=verifier, head=head, experiment=experiment, periods=rows)
    return rep, summary


def write_gate(root: Path, slug: str, rep: round_md.Report, summary: dict, offline: bool) -> None:
    folder = round_md.round_dir(root, slug)
    if not folder.exists():
        return
    command = f"validate_verification.py {slug}" + (" --offline" if offline else "")
    code = round_md.PASS if rep.ok else round_md.FAIL
    lines = [f"# Results - {slug}", "", f"Gate: `{command}` - **{'pass' if rep.ok else 'fail'}**", ""]
    if summary.get("valid") is not None:
        lines += ["| Experiment | Verifier | HEAD | Metric | Valid | OOT | Drop | Max drop |",
                  "| --- | --- | --- | --- | --- | --- | --- | --- |",
                  (f"| {summary.get('experiment')} | {summary.get('verifier')} | {summary.get('head')} | "
                   f"{summary.get('metric')} | {summary['valid']:g} | {summary['oot']:g} | {summary['drop']:g} | "
                   f"{summary['limit'] if summary.get('limit') is not None else '-'} |"), ""]
    if summary.get("periods"):
        lines += ["| OOT period | " + summary.get("metric", "metric") + " |", "| --- | --- |"]
        lines += [f"| {row[0]} | {row[-1]} |" for row in summary["periods"]] + [""]
    if not rep.ok:
        lines += ["## Findings", ""] + [f"- {e}" for e in rep.errors] + [""]
    (folder / "results.md").write_text("\n".join(lines))
    (folder / "gate.json").write_text(json.dumps({"exit": code, "command": command, "findings": rep.errors,
                                                  "experiment": summary.get("experiment")}, indent=2) + "\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="validate_verification.py", description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--root", default=".")
    parser.add_argument("slug")
    parser.add_argument("--offline", action="store_true")
    args = parser.parse_args(argv)
    halt = spec_md.halted(args.root)
    if halt:
        print(halt)
        return spec_md.HALT_EXIT
    root = Path(args.root).resolve()
    rep, summary = validate(root, args.slug, offline=args.offline)
    write_gate(root, args.slug, rep, summary, args.offline)
    rep.print()
    return round_md.PASS if rep.ok else round_md.FAIL


if __name__ == "__main__":
    sys.exit(main())
