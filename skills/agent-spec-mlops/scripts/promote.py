"""promote.py - challenger against champion, slice by slice, then the user's OK for the alias swap.

Usage: python3 promote.py [--root <repo>] gate <slug>
       python3 promote.py [--root <repo>] approve <slug> --user "<their words>"

The experiment lane's gate, applied to a promotion: the Cases are slices of the recent period, the Baseline is
the champion, the Variant is the challenger. Reads `## Promotion` of .specs/features/<slug>/spec.md and the
Results files in runs/champion/ and runs/challenger/ ({"runs": [{"case": <slice>, "run": <resample>,
"metrics": {...}}]}, or a CSV with case and run columns). Runs are paired bootstrap resamples: run i of both
models scores the same rows. The gate fails when a slice regresses (its mean delta is below -Tolerance) or when
the target gain over the Target slices is below Min gain or its 95% CI does not sit above zero. Needs a
passing validate_prod.py first. Writes promotion.md and promotion.json.
Exit: 0 pass, 1 gate fail, 2 invalid input, 5 halted (.specs/HALT exists).
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import spec_md

PASS, FAIL, INVALID = 0, 1, 2
MIN_RESAMPLES = 20
MODELS = ("champion", "challenger")


class PromoteError(Exception):
    """Invalid or missing input; exit 2."""


def folder(root: Path, slug: str) -> Path:
    return root / ".specs" / "features" / slug


def _number(text: str, default: float) -> float:
    try:
        return float(text.split()[0].lstrip("+")) if text.strip() else default
    except ValueError as exc:
        raise PromoteError(f"not a number: {text!r}") from exc


def settings(root: Path, slug: str) -> dict:
    path = folder(root, slug) / "spec.md"
    if not path.exists():
        raise PromoteError(f".specs/features/{slug}/spec.md is missing")
    body = spec_md.section(path.read_text(), "Promotion")
    if not body:
        raise PromoteError("the spec has no ## Promotion section (references/promote.md)")
    lab = root / ".specs" / "LAB.md"
    problem = spec_md.section(lab.read_text(), "Problem") if lab.exists() else ""
    metric = (spec_md.field(body, "Metric") or spec_md.field(problem, "Metric")).lower()
    if not metric:
        raise PromoteError("no metric: **Metric**: in ## Promotion, or in ## Problem of .specs/LAB.md")
    slices = [row for row in spec_md.table(body) if row.get("Slice")]
    targets = [row["Slice"] for row in slices if spec_md.is_yes(row.get("Target", ""))]
    if not targets and any(row["Slice"] == "all" for row in slices):
        targets = ["all"]
    champion = spec_md.field(body, "Champion")
    if not spec_md.field(body, "Challenger"):
        raise PromoteError("**Challenger**: the model version that would take the champion alias")
    if champion.lower() not in ("", "none") and (not slices or not targets):
        raise PromoteError("## Promotion needs a slices table with at least one Target slice (or a slice `all`)")
    return {"metric": metric, "champion": champion, "challenger": spec_md.field(body, "Challenger"),
            "period": spec_md.field(body, "Period"), "min_gain": _number(spec_md.field(body, "Min gain"), 0.0),
            "tolerance": _number(spec_md.field(body, "Tolerance"), 0.0),
            "slices": [row["Slice"] for row in slices], "targets": targets}


def read_runs(directory: Path, metric: str) -> dict:
    """{slice: {run: value}} from every Results file in a folder."""
    out: dict = {}
    for path in sorted(p for p in directory.rglob("*") if p.is_file()) if directory.exists() else []:
        try:
            if path.suffix.lower() == ".csv":
                with path.open(newline="") as handle:
                    rows = [{"case": r["case"], "run": r.get("run", 1), "metrics": r} for r in csv.DictReader(handle)]
            else:
                rows = json.loads(path.read_text())["runs"]
            for row in rows:
                value = row["metrics"].get(metric)
                if value not in (None, ""):
                    out.setdefault(str(row["case"]), {})[int(row.get("run", 1))] = float(value)
        except (ValueError, KeyError, TypeError) as exc:
            raise PromoteError(f"{path.name}: malformed Results file - {exc}") from exc
    return out


def percentile(values: list, q: float) -> float:
    ordered = sorted(values)
    position = (len(ordered) - 1) * q
    low = int(position)
    high = min(low + 1, len(ordered) - 1)
    return ordered[low] + (ordered[high] - ordered[low]) * (position - low)


def _fmt(value: float) -> str:
    return f"{value:+.4f}"


def gate(root: Path, slug: str) -> tuple[int, list[str]]:
    work = folder(root, slug)
    prod = work / "gate.json"
    last = json.loads(prod.read_text()) if prod.exists() else {}
    if not str(last.get("command", "")).startswith("validate_prod.py") or last.get("exit") != 0:
        raise PromoteError(f"validate_prod.py {slug} has not passed - the production standard comes first")
    conf = settings(root, slug)
    command = f"promote.py gate {slug}"
    findings: list[str] = []
    lines = [f"# Promotion - {slug}", "", f"Champion: {conf['champion'] or 'none'} - Challenger: {conf['challenger']}"
             f" - Metric: {conf['metric']}" + (f" - Period: {conf['period']}" if conf["period"] else ""), ""]
    if conf["champion"].lower() in ("", "none"):
        lines += ["No champion yet: the challenger becomes the first champion; nothing to compare.", ""]
    else:
        sign = -1.0 if conf["metric"] in spec_md.LOWER_IS_BETTER else 1.0
        runs = {model: read_runs(work / "runs" / model, conf["metric"]) for model in MODELS}
        lines += ["| Slice | Target | Resamples | Champion | Challenger | Gain | CI 95% |",
                  "| --- | --- | --- | --- | --- | --- | --- |"]
        gains: dict = {}
        for name in conf["slices"]:
            champ, chall = runs["champion"].get(name, {}), runs["challenger"].get(name, {})
            paired = sorted(set(champ) & set(chall))
            if not champ or not chall:
                findings.append(f"{name}: no runs for the {'champion' if not champ else 'challenger'}")
                continue
            if len(paired) < MIN_RESAMPLES:
                findings.append(f"{name}: {len(paired)} paired resamples, needs at least {MIN_RESAMPLES}")
                continue
            gains[name] = {i: sign * (chall[i] - champ[i]) for i in paired}
            mean = sum(gains[name].values()) / len(paired)
            low, high = percentile(list(gains[name].values()), 0.025), percentile(list(gains[name].values()), 0.975)
            before = sum(champ[i] for i in paired) / len(paired)
            after = sum(chall[i] for i in paired) / len(paired)
            target = "yes" if name in conf["targets"] else ""
            lines.append(f"| {name} | {target} | {len(paired)} | {before:.4f} | {after:.4f} | {_fmt(mean)} | "
                         f"[{_fmt(low)}, {_fmt(high)}] |")
            if mean < -conf["tolerance"] - 1e-12:
                findings.append(f"{name}: regressed - {conf['metric']} {before:.4f} -> {after:.4f} "
                                f"(tolerance {conf['tolerance']:g})")
        targets = [name for name in conf["targets"] if name in gains]
        if targets and len(targets) == len(conf["targets"]):
            shared = sorted(set.intersection(*(set(gains[name]) for name in targets)))
            combined = [sum(gains[name][i] for name in targets) / len(targets) for i in shared]
            if len(combined) < MIN_RESAMPLES:
                findings.append(f"target: {len(combined)} resamples shared by the Target slices, "
                                f"needs at least {MIN_RESAMPLES}")
            else:
                mean, low = sum(combined) / len(combined), percentile(combined, 0.025)
                high = percentile(combined, 0.975)
                lines += ["", (f"Target gain over {', '.join(targets)}: {_fmt(mean)}, CI 95% [{_fmt(low)}, "
                              f"{_fmt(high)}]; needs >= {conf['min_gain']:g} with the CI above 0")]
                if mean < conf["min_gain"] - 1e-12:
                    findings.append(f"target: gain {_fmt(mean)} below the min gain {conf['min_gain']:g}")
                if low <= 0:
                    findings.append(f"target: the CI of the gain [{_fmt(low)}, {_fmt(high)}] does not sit above 0")
        lines.append("")
    code = FAIL if findings else PASS
    lines[2:2] = [f"Gate: `{command}` - **{'pass' if code == PASS else 'fail'}**", ""]
    if findings:
        lines += ["## Findings", ""] + [f"- {f}" for f in findings] + [""]
    (work / "promotion.md").write_text("\n".join(lines))
    (work / "promotion.json").write_text(json.dumps({"exit": code, "command": command, "findings": findings,
                                                     "champion": conf["champion"] or "none",
                                                     "challenger": conf["challenger"]}, indent=2) + "\n")
    return code, findings


def approve(root: Path, slug: str, user: str | None) -> dict:
    if not user or not user.strip():
        raise PromoteError("--user needs the user's own words approving the alias swap")
    path = folder(root, slug) / "promotion.json"
    if not path.exists():
        raise PromoteError(f"no promotion gate has run - run `promote.py gate {slug}` first")
    result = json.loads(path.read_text())
    if result["exit"] != 0:
        raise PromoteError("the promotion gate failed: " + "; ".join(result["findings"][:5]))
    today = dt.date.today().isoformat()
    result["approved"] = {"date": today, "user": user}
    path.write_text(json.dumps(result, indent=2) + "\n")
    log = root / ".specs" / "prod" / "promotions.md"
    log.parent.mkdir(parents=True, exist_ok=True)
    text = log.read_text() if log.exists() else "# Promotions\n\nEach line: the alias swap, the user's words and the evidence.\n\n"
    log.write_text(text + f"- {today}: {slug} - challenger {result['challenger']} replaces champion "
                          f"{result['champion']} - user: \"{user}\" - evidence: .specs/features/{slug}/promotion.md\n")
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="promote.py", description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--root", default=".")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("gate").add_argument("slug")
    p = sub.add_parser("approve")
    p.add_argument("slug")
    p.add_argument("--user")
    args = parser.parse_args(argv)
    halt = spec_md.halted(args.root)
    if halt:
        print(halt)
        return spec_md.HALT_EXIT
    root = Path(args.root).resolve()
    try:
        if args.command == "gate":
            code, findings = gate(root, args.slug)
            for line in findings:
                print(f"FAIL {line}")
            print(f"promotion {args.slug}: {'pass' if code == PASS else 'fail'}")
            return code
        result = approve(root, args.slug, args.user)
        print(f"approved: move the champion alias to {result['challenger']} now; "
              f"rollback: back to {result['champion']} (.specs/prod/promotions.md)")
        return PASS
    except PromoteError as exc:
        print(f"ERROR {exc}")
        return INVALID


if __name__ == "__main__":
    sys.exit(main())
