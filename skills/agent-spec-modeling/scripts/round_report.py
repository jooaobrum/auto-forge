"""round_report.py - start, or refresh, the round's report.md from ledger.json.

Usage: python3 <skill-dir>/scripts/round_report.py [--root <repo>] <slug>

Writes the `## Climb` summary and the `## Ledger` table from the ledger; on an existing report it replaces only
those two sections, so the prose you wrote stays. The other sections are yours: What worked, What did not,
Error patterns, Domain findings, Next round.
Exit: 0 ok, 2 invalid input, 5 halted (.specs/HALT exists).
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

PROSE = {
    "What worked": "<the kept changes and the likely mechanism of each>",
    "What did not": "<what was rejected or infeasible, and what that teaches>",
    "Error patterns": "<what the best experiment's error analysis shows: classes, segments, periods>",
    "Domain findings": "<what the data confirmed or contradicted in the ## Problem of .specs/LAB.md>",
    "Next round": "<ideas for the next round's backlog, each with the evidence behind it>",
}


def ledger_md(ledger: dict) -> str:
    rows = ["| it | status | hypothesis | valid | delta vs best | CI 95% | checks failed |",
            "| --- | --- | --- | --- | --- | --- | --- |"]
    for e in ledger["entries"]:
        value = f"{e['value']:.4f}" if e.get("value") is not None else "-"
        delta = f"{e['delta']:+.4f}" if e.get("delta") is not None else "-"
        ci = f"[{e['ci'][0]:+.4f}, {e['ci'][1]:+.4f}]" if e.get("ci") else "-"
        failed = ", ".join(k for k, c in (e.get("checks") or {}).items() if not c.get("ok")) or "-"
        hypothesis = str(e.get("hypothesis", "")).replace("|", "/")[:70]
        mark = "**kept**" if e.get("status") == "kept" else e.get("status")
        rows.append(f"| {e['iteration']:02d} | {mark} | {hypothesis} | {value} | {delta} | {ci} | {failed} |")
    return "\n".join(rows)


def climb_md(ledger: dict) -> str:
    entries = ledger["entries"]
    kept = [e for e in entries if e.get("status") == "kept"]
    count = {s: sum(1 for e in entries if e.get("status") == s) for s in ("kept", "rejected", "infeasible", "failed")}
    lines = [f"- Iterations: {len(entries)} ({', '.join(f'{k} {v}' for k, v in count.items())})"]
    if kept:
        first, best = kept[0], kept[-1]
        lines.append(f"- Baseline: it{first['iteration']:02d} {first.get('metric')}={first['value']:.4f}")
        lines.append(f"- Best: it{best['iteration']:02d} `{best['id']}` {best.get('metric')}={best['value']:.4f} "
                     f"({best['value'] - first['value']:+.4f} vs baseline)")
        if best.get("error_summary"):
            lines.append("- Best's error analysis: " + "; ".join(best["error_summary"]))
    return "\n".join(lines)


def build(root: Path, slug: str) -> Path:
    folder = round_md.round_dir(root, slug)
    ledger = json.loads((folder / "ledger.json").read_text(encoding="utf-8"))
    path = folder / "report.md"
    if path.exists():
        text = path.read_text(encoding="utf-8")
    else:
        text = f"# Report {slug}\n\n## Climb\n\n## Ledger\n\n" + "".join(f"## {k}\n{v}\n\n" for k, v in PROSE.items())
    for name, body in (("Climb", climb_md(ledger)), ("Ledger", ledger_md(ledger))):
        pattern = re.compile(rf"(^## {name}\n)(.*?)(?=^## |\Z)", re.DOTALL | re.MULTILINE)
        text = pattern.sub(lambda m, body=body: m.group(1) + body + "\n\n", text, count=1)
    path.write_text(text, encoding="utf-8")
    return path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="round_report.py", description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--root", default=".")
    parser.add_argument("slug")
    args = parser.parse_args(argv)
    halt = spec_md.halted(args.root)
    if halt:
        print(halt)
        return spec_md.HALT_EXIT
    root = Path(args.root).resolve()
    if not (round_md.round_dir(root, args.slug) / "ledger.json").exists():
        print(f"ERROR .specs/features/{args.slug}/ledger.json is missing")
        return round_md.INVALID
    print(f"wrote {build(root, args.slug).relative_to(root)}")
    return round_md.PASS


if __name__ == "__main__":
    sys.exit(main())
