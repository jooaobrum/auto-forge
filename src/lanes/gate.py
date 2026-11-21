"""The gate: a per-Case verdict from Results files, the Baseline and the git diff since freeze."""

from __future__ import annotations

from dataclasses import dataclass, field
from fractions import Fraction

from lanes import baseline as baselines
from lanes.results import Run, by_case, read_dir
from lanes.selection import STABLE, TARGET, edit_scope
from lanes.surface import in_scope
from lanes.work import Work, git, load_config, profile_config


@dataclass
class Verdict:
    findings: list = field(default_factory=list)
    rows: list = field(default_factory=list)  # (columns...) for results.md
    header: list = field(default_factory=list)

    @property
    def code(self) -> int:
        return 1 if self.findings else 0


def _frac(value) -> Fraction:
    return Fraction(str(value))


def _mean(values: list) -> Fraction | None:
    values = [_frac(v) for v in values if v is not None]
    return sum(values, Fraction(0)) / len(values) if values else None


def run_passes(metrics: dict, thresholds: dict) -> bool:
    for name, pass_at in thresholds.items():
        value = metrics.get(name)
        if value is None or _frac(value) < _frac(pass_at):
            return False
    return True


def case_passes(runs: list[dict], thresholds: dict) -> bool:
    passed = sum(1 for metrics in runs if run_passes(metrics, thresholds))
    return passed * 2 > len(runs)


def _fmt(value) -> str:
    if value is None:
        return "-"
    number = float(value)
    return str(int(number)) if number.is_integer() else f"{number:.3g}"


def out_of_scope(work: Work, commit: str, scope: list[str]) -> list[str]:
    changed = set(git(work.root, "diff", "--name-only", commit).split())
    changed |= set(git(work.root, "ls-files", "--others", "--exclude-standard").split())
    own = f".lanes/work/{work.slug}/"
    return sorted(p for p in changed
                  if not p.startswith(own) and not p.startswith(".lanes/baseline/") and not in_scope(p, scope))


def judge_cases(work: Work, variant: str, confirm: bool, regression_only: bool) -> Verdict:
    frozen = work.frozen()
    config = load_config(work.root)
    profile = profile_config(config, frozen["profile"])
    metrics_cfg = config.get("metrics", {})
    declared = profile.get("metrics", [])
    thresholds = {m: metrics_cfg[m]["pass_at"] for m in declared if "pass_at" in metrics_cfg.get(m, {})}
    guardrails = {m: metrics_cfg[m]["budget_pct"] for m in declared if "budget_pct" in metrics_cfg.get(m, {})}
    experiment = work.experiment() or {}
    selection = work.read_json("selection.json")
    runs = by_case(read_dir(work.runs_dir / variant))
    stored = baselines.load_all(work.root, frozen["profile"])
    target_metric = experiment.get("target_metric")
    verdict = Verdict()
    verdict.header = ["Case", "Tier", "Baseline", "Variant"]
    if target_metric:
        verdict.header.append(f"{target_metric} before → after")
    verdict.header += [f"{g} before → after" for g in guardrails]

    target_before, target_after = [], []
    for case, spec in selection["cases"].items():
        tier, k = spec["tier"], int(spec["k"])
        if tier == STABLE and confirm:
            k = max(1, int(selection.get("k_stable", 1)))
        have: list[Run] = runs.get(case, [])
        if k == 0 and not have:
            continue
        if len(have) < k:
            verdict.findings.append(f"{case}: {k - len(have)} of {k} runs missing")
        base = stored.get(case)
        base_runs = base["runs"] if base else []
        variant_runs = [r.metrics for r in have]
        base_ok = case_passes(base_runs, thresholds) if base_runs else None
        now_ok = case_passes(variant_runs, thresholds) if variant_runs else None
        if base_ok and now_ok is False:
            verdict.findings.append(f"{case}: regressed - passed the Baseline, fails in {variant}")
        cells = [case, tier, {True: "pass", False: "fail", None: "-"}[base_ok],
                 {True: "pass", False: "fail", None: "-"}[now_ok]]
        if target_metric:
            before = _mean([m.get(target_metric) for m in base_runs])
            after = _mean([m.get(target_metric) for m in variant_runs])
            cells.append(f"{_fmt(before)} → {_fmt(after)}")
            if tier == TARGET:
                if before is None:
                    verdict.findings.append(f"{case}: Target Case has no Baseline")
                else:
                    target_before.append(before)
                if after is not None:
                    target_after.append(after)
        for name, pct in guardrails.items():
            before = _mean([m.get(name) for m in base_runs])
            after = _mean([m.get(name) for m in variant_runs])
            cells.append(f"{_fmt(before)} → {_fmt(after)}")
            if before is not None and after is not None and after * 100 > before * (100 + _frac(pct)):
                verdict.findings.append(
                    f"{case}: guardrail {name} {_fmt(after)} exceeds Baseline {_fmt(before)} by more than {pct}%"
                )
        verdict.rows.append(cells)

    if target_metric and not regression_only:
        min_delta = _frac(experiment.get("min_delta", 0))
        before, after = _mean(target_before), _mean(target_after)
        if before is None or after is None:
            verdict.findings.append(f"target {target_metric}: no Target Case has both a Baseline and runs")
        elif after - before < min_delta:
            verdict.findings.append(
                f"target {target_metric}: mean over Target Cases moved {_fmt(before)} → {_fmt(after)}, "
                f"needs +{_fmt(min_delta)}"
            )
    for path in out_of_scope(work, frozen["commit"], edit_scope(experiment, profile)):
        verdict.findings.append(f"outside Edit Scope: {path}")
    return verdict


def judge_contract(work: Work, variant: str) -> Verdict:
    cases = work.read_json("contract.json")["cases"]
    runs = by_case(read_dir(work.runs_dir / variant))
    verdict = Verdict(header=["Case", "Violations"])
    for case in cases:
        have = runs.get(case, [])
        if not have:
            verdict.findings.append(f"{case}: no result")
            verdict.rows.append([case, "-"])
            continue
        violations = max(int(float(r.metrics.get("violations", 0) or 0)) for r in have)
        verdict.rows.append([case, str(violations)])
        if violations > 0:
            label = "golden row missing" if ".golden." in case else f"{violations} violations"
            verdict.findings.append(f"{case}: {label}")
    return verdict


def judge_junit(work: Work, variant: str) -> Verdict:
    runs = read_dir(work.runs_dir / variant)
    verdict = Verdict(header=["Test", "Result"])
    if not runs:
        verdict.findings.append("no test ran")
    for run in runs:
        ok = run.metrics.get("passed") == 1
        verdict.rows.append([run.case, "pass" if ok else "fail"])
        if not ok:
            verdict.findings.append(f"{run.case}: failed")
    return verdict


def gate(work: Work, variant: str = "main", confirm: bool = False, regression_only: bool = False) -> Verdict:
    frozen = work.frozen()
    if frozen["lane"] == "build" and frozen["profile"] == "pipeline":
        verdict = judge_contract(work, variant)
    elif frozen["lane"] == "build" and frozen["profile"] == "app":
        verdict = judge_junit(work, variant)
    else:
        verdict = judge_cases(work, variant, confirm, regression_only or frozen["lane"] == "build")
    command = " ".join(["rl", "gate", work.slug, "--variant", variant]
                       + (["--confirm"] if confirm else []) + (["--regression-only"] if regression_only else []))
    lines = [f"# Results - {work.slug}", "", f"Gate: `{command}` - **{'pass' if verdict.code == 0 else 'fail'}**",
             "", "| " + " | ".join(verdict.header) + " |", "|" + " --- |" * len(verdict.header)]
    lines += ["| " + " | ".join(row) + " |" for row in verdict.rows]
    if verdict.findings:
        lines += ["", "## Findings", ""] + [f"- {f}" for f in verdict.findings]
    work.path("results.md").write_text("\n".join(lines) + "\n")
    work.write_json("gate.json", {"exit": verdict.code, "command": command, "variant": variant,
                                  "findings": verdict.findings})
    return verdict
