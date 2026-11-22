"""agent-spec-experiment: freeze, baseline, select, gate, budget and deliver one Experiment.

Usage: python3 experiment.py [--root <repo>] <command> <slug> [options]
Exit: 0 ok, 1 gate fail, 2 invalid input, 3 variant cap, 4 budget spent - stop and ask the user,
5 halted (.specs/HALT exists).
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from fractions import Fraction
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import lab
import spec_md
from lab import BUDGET_SPENT, GATE_FAIL, INVALID, OK, VARIANT_CAP, LabError, Work

DECISIONS = ("adopt", "promote", "reject")
GRADUATE_AFTER = 3


# --- freeze ---------------------------------------------------------------------------------------------------

def freeze(work: Work) -> dict:
    spec = lab.load_spec(work)
    missing = []
    if not spec.approved:
        missing.append("no **Approved**: line - the user approves the plan first")
    if not spec.profile:
        missing.append("no **Profile**:")
    if spec.lane != "research":
        missing.append("**Lane**: must be research for an Experiment")
    if not spec.cases and not spec.dataset:
        missing.append("no Cases: add a ## Cases table or a **Dataset**: line")
    unknown = [case for case in spec.target_cases if spec.cases and case not in spec.cases]
    if unknown:
        missing.append(f"Target cases not in the Cases table: {', '.join(unknown)}")
    if spec.lane == "research" and not target_cases(spec):
        missing.append("no Target cases: list them in **Target cases**: or by Failure mode in the Cases table")
    target = spec.target_metric
    if target is None:
        missing.append("no Target Metric: give one metric a Target delta in ## Metrics (here or in .specs/LAB.md)")
    missing += plan_findings(spec.text)
    if not spec.edit_scope:
        missing.append("no Edit Scope: list the paths in ## Edit Scope (here or in .specs/LAB.md)")
    if missing:
        raise LabError("; ".join(missing))
    commit = lab.git(work.root, "rev-parse", "HEAD").strip()
    frozen = {"commit": commit, "profile": spec.profile, "lane": spec.lane}
    work.write_json("frozen.json", frozen)
    return frozen


RESEARCH_SECTIONS = ("Problem", "Diagnosis", "Hypotheses")
ADVISORY_SECTIONS = ("Behavior", "Shape", "Out of scope", "Assumptions", "Sources")


def plan_findings(text: str) -> list[str]:
    """The research half of the plan (references/plan.md): what is wrong, why, and what each variant tries."""
    out = [f"no ## {name}: references/plan.md says what it holds" for name in RESEARCH_SECTIONS
           if not spec_md.section(text, name)]
    hypotheses = spec_md.subsections(spec_md.section(text, "Hypotheses"))
    if spec_md.section(text, "Hypotheses") and not hypotheses:
        out.append("## Hypotheses needs at least one '### H1 - <variant>' with '- Idea:' and '- Why:'")
    for name, block in hypotheses.items():
        fields = {k.lower(): v for k, v in (re.findall(r"^-\s*([A-Za-z ]+):\s*(.*\S)", block, re.MULTILINE))}
        if len(fields.get("idea", "")) < 8 or len(fields.get("why", "")) < 8:
            out.append(f"{name}: '- Idea:' and '- Why:' must both say something concrete")
    return out


def plan_warnings(text: str) -> list[str]:
    return [f"no ## {name} - references/plan.md" for name in ADVISORY_SECTIONS if not spec_md.section(text, name)]


# --- grading --------------------------------------------------------------------------------------------------

def effective(run: dict, row: dict) -> tuple[dict, set]:
    """The run's metrics plus what the Case row asks to grade, and the set of metrics graded on this Case.

    A `Read`, `Cite` or `Route` cell defines that metric for the Case; the column present with the cell empty
    means "not graded on it here", even when the run reports it."""
    metrics = dict(run.get("metrics", {}))
    graded = set(metrics)
    for column, key, name in (("Cite", "cited", "cited_recall"), ("Read", "read", "read_recall")):
        expected = set(spec_md.split_list(row.get(column, "")))
        if expected:
            graded.add(name)
            if key in run:
                metrics[name] = Fraction(len(expected & set(run[key])), len(expected))
        elif column in row:
            graded.discard(name)
    if row.get("Route"):
        graded.add("route_match")
        if "route" in run:
            metrics["route_match"] = 1 if str(run["route"]) == row["Route"] else 0
    elif "Route" in row:
        graded.discard("route_match")
    return metrics, graded


def run_passes(run: dict, row: dict, thresholds: dict) -> bool:
    metrics, graded = effective(run, row)
    for name, bar in thresholds.items():
        if name not in graded:
            continue
        value = metrics.get(name)
        if value is None or lab.frac(value) < lab.frac(bar):
            return False
    return True


def case_passes(runs: list[dict], row: dict, thresholds: dict) -> bool | None:
    if not runs:
        return None
    passed = sum(1 for run in runs if run_passes(run, row, thresholds))
    if row.get("Tier", "").strip().lower() == "regression":
        return passed == len(runs)
    return passed * 2 > len(runs)


def _as_dict(run: lab.Run) -> dict:
    return {"metrics": run.metrics, **run.extra}


def _mean(values: list) -> Fraction | None:
    values = [lab.frac(v) for v in values if v is not None]
    return sum(values, Fraction(0)) / len(values) if values else None


def _fmt(value) -> str:
    if value is None:
        return "-"
    number = float(value)
    return str(int(number)) if number.is_integer() else f"{number:.3g}"


# --- baseline -------------------------------------------------------------------------------------------------

def baseline(work: Work, source: Path) -> list[str]:
    spec = lab.load_spec(work)
    commit = work.frozen()["commit"] if work.path("frozen.json").exists() else None
    if not source.exists():
        raise LabError(f"{source} is missing")
    directory = lab.baseline_dir(work.root, spec.profile)
    directory.mkdir(parents=True, exist_ok=True)
    written = []
    for case, runs in sorted(lab.by_case(lab.read_file(source)).items()):
        touched = sorted({item for run in runs for item in run.touched})
        data = {"case": case, "runs": [_as_dict(r) for r in runs], "touched": touched,
                "surface_hash": lab.content_hash(work.root, lab.item_paths(spec.surface, touched), commit)}
        (directory / f"{case}.json").write_text(json.dumps(data, indent=2, default=str) + "\n")
        written.append(case)
    return written


# --- select ---------------------------------------------------------------------------------------------------

def variants(work: Work) -> list[str]:
    return work.read_json("variants.json")["variants"] if work.path("variants.json").exists() else []


def target_cases(spec: lab.Spec) -> list[str]:
    if spec.target_cases:
        return list(dict.fromkeys(spec.target_cases))
    mode = spec.failure_mode.strip().lower()
    return [case for case, row in spec.cases.items() if mode and row.get("Failure mode", "").strip().lower() == mode]


def select(work: Work, variant: str) -> dict:
    frozen = work.frozen()
    spec = lab.load_spec(work)
    scope = spec.edit_scope
    stored = lab.load_baselines(work.root, frozen["profile"])
    everything = any(s.get("affects_all") and any(lab.overlaps(p, scope) for p in s.get("paths", []))
                     for s in spec.surface.values())
    cases: dict = {}
    for case in target_cases(spec):
        cases[case] = {"tier": "target", "k": spec.k["target"]}
    for case in list(spec.cases) + [c for c in stored if c not in spec.cases]:
        if case in cases:
            continue
        touched = stored.get(case, {}).get("touched", [])
        hit = everything or any(lab.overlaps(p, scope) for p in lab.item_paths(spec.surface, touched))
        cases[case] = {"tier": "affected", "k": spec.k["affected"]} if hit else {"tier": "stable", "k": 0}
    stale = []
    for case in cases:
        base = stored.get(case)
        now = lab.content_hash(work.root, lab.item_paths(spec.surface, (base or {}).get("touched", [])),
                               frozen["commit"])
        if base is None or now != base.get("surface_hash"):
            stale.append(case)
    selection = {"variant": variant, "edit_scope": scope, "k_stable": spec.k["stable"], "cases": cases,
                 "stale": sorted(stale)}
    known = variants(work)
    if variant not in known:
        work.write_json("variants.json", {"variants": known + [variant]})
    work.write_json("selection.json", selection)
    return selection


# --- gate -----------------------------------------------------------------------------------------------------

def gate(work: Work, variant: str, confirm: bool, regression_only: bool) -> tuple[int, list[str]]:
    frozen = work.frozen()
    spec = lab.load_spec(work)
    thresholds, guardrails = spec.thresholds(), spec.guardrails()
    target = spec.target_metric
    selection = work.read_json("selection.json")
    runs = lab.by_case(lab.read_dir(work.runs_dir / variant))
    stored = lab.load_baselines(work.root, frozen["profile"])
    findings: list[str] = []
    header = ["Case", "Tier", "Baseline", "Variant"]
    if target:
        header.append(f"{target.name} before → after")
    header += [f"{g} before → after" for g in guardrails]
    rows, before_t, after_t, verdicts = [], [], [], {}
    for case, pick in selection["cases"].items():
        k = int(pick["k"])
        if pick["tier"] == "stable" and confirm:
            k = max(1, int(selection.get("k_stable", 1)))
        have = [_as_dict(r) for r in runs.get(case, [])]
        if k == 0 and not have:
            continue
        if len(have) < k:
            findings.append(f"{case}: {k - len(have)} of {k} runs missing")
        row = spec.cases.get(case, {})
        base_runs = stored.get(case, {}).get("runs", [])
        base_ok, now_ok = case_passes(base_runs, row, thresholds), case_passes(have, row, thresholds)
        verdicts[case] = now_ok
        if base_ok and now_ok is False:
            findings.append(f"{case}: regressed - passed the Baseline, fails in {variant}")
        label = {True: "pass", False: "fail", None: "-"}
        tier = row.get("Tier", "") or "capability"
        cells = [case, f"{pick['tier']}, {tier}", label[base_ok], label[now_ok]]
        if target:
            before = _mean([effective(r, row)[0].get(target.name) for r in base_runs])
            after = _mean([effective(r, row)[0].get(target.name) for r in have])
            cells.append(f"{_fmt(before)} → {_fmt(after)}")
            if pick["tier"] == "target":
                if before is None:
                    findings.append(f"{case}: Target Case has no Baseline")
                else:
                    before_t.append(before)
                if after is not None:
                    after_t.append(after)
        for name, pct in guardrails.items():
            before = _mean([r.get("metrics", {}).get(name) for r in base_runs])
            after = _mean([r.get("metrics", {}).get(name) for r in have])
            cells.append(f"{_fmt(before)} → {_fmt(after)}")
            if before is not None and after is not None and after * 100 > before * (100 + pct):
                findings.append(f"{case}: guardrail {name} {_fmt(after)} exceeds Baseline {_fmt(before)} "
                                f"by more than {_fmt(pct)}%")
        rows.append(cells)
    if target and not regression_only:
        delta = lab.frac(target.target)
        before, after = _mean(before_t), _mean(after_t)
        if before is None or after is None:
            findings.append(f"target {target.name}: no Target Case has both a Baseline and runs")
        elif after - before < delta:
            findings.append(f"target {target.name}: mean over Target Cases moved {_fmt(before)} → {_fmt(after)}, "
                            f"needs +{_fmt(delta)}")
    for path in lab.out_of_scope(work, frozen["commit"], spec.edit_scope):
        findings.append(f"outside Edit Scope: {path}")
    code = GATE_FAIL if findings else OK
    command = " ".join(["experiment.py gate", work.slug, "--variant", variant]
                       + (["--confirm"] if confirm else []) + (["--regression-only"] if regression_only else []))
    lines = [f"# Results - {work.slug}", "", f"Gate: `{command}` - **{'pass' if code == OK else 'fail'}**", "",
             "| " + " | ".join(header) + " |", "|" + " --- |" * len(header)]
    lines += ["| " + " | ".join(r) + " |" for r in rows]
    if findings:
        lines += ["", "## Findings", ""] + [f"- {f}" for f in findings]
    work.path("results.md").write_text("\n".join(lines) + "\n")
    work.write_json("gate.json", {"exit": code, "command": command, "variant": variant, "findings": findings,
                                  "verdicts": verdicts})
    return code, findings


# --- budget ---------------------------------------------------------------------------------------------------

def _added(work: Work) -> list[dict]:
    return work.read_json("budget.json")["added"] if work.path("budget.json").exists() else []


def budget_status(work: Work) -> tuple[bool, int, int]:
    spec = lab.load_spec(work)
    total = spec.budget + sum(int(a["tokens"]) for a in _added(work))
    spent = sum(int(r.metrics.get("input_tokens", 0) or 0) for r in lab.read_dir(work.runs_dir))
    return (total > 0 and spent >= total), spent, total


def spent_message(spent: int, total: int) -> str:
    return (f"budget spent: {spent} of {total} input tokens - stop and ask the user whether to continue; on "
            "their yes run `experiment.py budget <slug> --add <tokens> --user \"<their words>\"`")


def budget_add(work: Work, tokens: int, user: str | None) -> int:
    if not user or not user.strip():
        raise LabError("--add needs --user with the user's own words approving it")
    if tokens <= 0:
        raise LabError("--add needs a positive number of tokens")
    today = dt.date.today().isoformat()
    work.write_json("budget.json", {"added": _added(work) + [{"tokens": tokens, "date": today, "user": user}]})
    text = work.path("budget.md").read_text() if work.path("budget.md").exists() else "# Budget\n\n"
    work.path("budget.md").write_text(text + f"- {today}: +{tokens} input tokens - user: \"{user}\"\n")
    return budget_status(work)[2]


# --- deliver --------------------------------------------------------------------------------------------------

def _streaks_path(work: Work, profile: str) -> Path:
    return lab.baseline_dir(work.root, profile) / "streaks.json"


def update_streaks(work: Work, spec: lab.Spec, profile: str, verdicts: dict) -> list[str]:
    path = _streaks_path(work, profile)
    streaks = json.loads(path.read_text()) if path.exists() else {}
    graduates = []
    for case, ok in verdicts.items():
        if spec.cases.get(case, {}).get("Tier", "").strip().lower() == "regression" or ok is None:
            continue
        streaks[case] = streaks.get(case, 0) + 1 if ok else 0
        if streaks[case] >= GRADUATE_AFTER:
            graduates.append(case)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(streaks, indent=2, sort_keys=True) + "\n")
    return sorted(graduates)


def deliver(work: Work, decision: str | None) -> str:
    frozen = work.frozen()
    if decision not in DECISIONS:
        raise LabError("an Experiment ends in a decision: --decision adopt|promote|reject")
    if not work.path("gate.json").exists():
        raise LabError(f"no gate has run - run `experiment.py gate {work.slug}` first")
    last = work.read_json("gate.json")
    if last["exit"] != 0 and decision != "reject":
        raise LabError("the last gate failed - fix it, or end with --decision reject: " + "; ".join(last["findings"]))
    spec = lab.load_spec(work)
    graduates = update_streaks(work, spec, frozen["profile"], last.get("verdicts", {})) if decision == "adopt" else []
    commits = lab.git(work.root, "log", "--oneline", f"{frozen['commit']}..HEAD").strip() or "none"
    goal = spec_md.section(spec.text, "Goal") or spec_md.section(spec.text, "Problem")
    results = work.path("results.md").read_text() if work.path("results.md").exists() else ""
    lines = [f"# Delivery - {work.slug}", "", "## Goal", "", goal, "", "## Decision", "", decision, ""]
    if graduates:
        lines += ["## Proposed for regression", "",
                  f"Passed {GRADUATE_AFTER} adopted Experiments in a row - mark them `regression` in the Cases:", ""]
        lines += [f"- {case}" for case in graduates] + [""]
    lines += ["## Gate", "", f"`{last['command']}` exited {last['exit']}", "", results,
              "## Commits since freeze", "", "```", commits, "```", ""]
    work.path("delivery.md").write_text("\n".join(lines))
    if decision == "promote":
        _promote(work, spec, frozen)
    return str(work.path("delivery.md").relative_to(work.root))


def _promote(work: Work, spec: lab.Spec, frozen: dict) -> None:
    build = Work(work.root, f"{work.slug}-build")
    build.dir.mkdir(parents=True, exist_ok=True)
    cases = target_cases(spec)
    problem = spec_md.section(spec.text, "Problem") or spec_md.section(spec.text, "Goal")
    lines = [f"# {work.slug} - build", "", f"**Profile**: {frozen['profile']}", "**Lane**: build",
             f"**Failure mode**: {spec.failure_mode or '(not named)'}", "",
             "<!-- Seeded by experiment.py deliver --decision promote. agent-spec-writer completes it as a lean plan",
             "     (agent-spec-lean/references/plan.md): Shape, Surface, Landing, Criteria, Out of scope, Assumptions. -->",
             "", "## Problem", "", problem, "",
             f"Experiment `{work.slug}` showed the fix belongs in code: it holds on every run, not on a rate.", "",
             "## Target Cases", "", *[f"- {c}" for c in cases], "",
             "## Proof", "", f"`experiment.py gate {work.slug} --regression-only`, and the plan's own checks", "",
             "## Sources", "", f"- `.specs/features/{work.slug}/plan.md` and `delivery.md` - binding - the Experiment", ""]
    build.path("plan.md").write_text("\n".join(lines))


# --- CLI ------------------------------------------------------------------------------------------------------

def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="experiment.py", description=__doc__)
    parser.add_argument("--root", default=".")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("freeze").add_argument("slug")
    p = sub.add_parser("baseline")
    p.add_argument("slug")
    p.add_argument("--from", dest="source", required=True)
    p = sub.add_parser("select")
    p.add_argument("slug")
    p.add_argument("--variant", required=True)
    p = sub.add_parser("gate")
    p.add_argument("slug")
    p.add_argument("--variant", required=True)
    p.add_argument("--confirm", action="store_true")
    p.add_argument("--regression-only", action="store_true")
    p = sub.add_parser("budget")
    p.add_argument("slug")
    p.add_argument("--add", type=int)
    p.add_argument("--user")
    p = sub.add_parser("deliver")
    p.add_argument("slug")
    p.add_argument("--decision", choices=DECISIONS)
    return parser


def _run(args) -> int:
    root = Path(args.root).resolve()
    work = Work(root, args.slug)
    if args.command == "freeze":
        frozen = freeze(work)
        for line in plan_warnings(lab.load_spec(work).text):
            print(f"WARN {line}")
        print(f"frozen {work.slug} at {frozen['commit'][:12]} ({frozen['profile']})")
        return OK
    if args.command == "baseline":
        source = Path(args.source) if Path(args.source).is_absolute() else root / args.source
        cases = baseline(work, source)
        print(f"baseline recorded for {len(cases)} cases: {', '.join(cases)}")
        return OK
    if args.command == "select":
        spent, used, total = budget_status(work)
        if spent:
            print(spent_message(used, total))
            return BUDGET_SPENT
        known, spec = variants(work), lab.load_spec(work)
        if args.variant not in known and len(known) >= spec.variants:
            print(f"variant cap reached ({', '.join(known)}) - deliver with a decision")
            return VARIANT_CAP
        chosen = select(work, args.variant)
        print(f"{'case':<24} {'tier':<9} k")
        for case, pick in chosen["cases"].items():
            print(f"{case:<24} {pick['tier']:<9} {pick['k']}")
        if chosen["stale"]:
            print(f"stale or missing Baseline - rerun these first: {', '.join(chosen['stale'])}")
        return OK
    if args.command == "gate":
        code, findings = gate(work, args.variant, args.confirm, args.regression_only)
        for line in findings:
            print(f"FAIL {line}")
        print(f"gate {work.slug} {args.variant}: {'pass' if code == OK else 'fail'}")
        return code
    if args.command == "budget":
        if args.add is not None or args.user is not None:
            print(f"budget raised to {budget_add(work, args.add or 0, args.user)} input tokens")
            return OK
        spent, used, total = budget_status(work)
        if spent:
            print(spent_message(used, total))
            return BUDGET_SPENT
        print(f"budget: {used} of {total or 'no limit'} input tokens spent")
        return OK
    print(f"delivered: {deliver(work, args.decision)}")
    return OK


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    halt = spec_md.halted(args.root)
    if halt:
        print(halt)
        return spec_md.HALT_EXIT
    try:
        return _run(args)
    except LabError as exc:
        print(f"ERROR {exc}")
        return INVALID


if __name__ == "__main__":
    sys.exit(main())
