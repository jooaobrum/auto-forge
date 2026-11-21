"""Delivery: the goal, the gate evidence and the Decision in one file."""

from __future__ import annotations

from lanes import brief as briefs
from lanes.work import LanesError, Work, git

DECISIONS = ("adopt", "promote", "reject")


def deliver(work: Work, decision: str | None) -> str:
    frozen = work.frozen()
    if decision is not None and decision not in DECISIONS:
        raise LanesError(f"decision must be one of {', '.join(DECISIONS)}")
    if frozen["lane"] == "research" and decision is None:
        raise LanesError("an Experiment ends in a decision: --decision adopt|promote|reject")
    if not work.path("gate.json").exists():
        raise LanesError(f"no gate has run - run `rl gate {work.slug}` first")
    last = work.read_json("gate.json")
    if last["exit"] != 0 and decision != "reject":
        raise LanesError(f"the last gate failed - fix it, or end the Experiment with --decision reject: "
                         f"{'; '.join(last['findings'])}")
    brief = briefs.load(work)
    commits = git(work.root, "log", "--oneline", f"{frozen['commit']}..HEAD").strip() or "none"
    results = work.path("results.md").read_text() if work.path("results.md").exists() else ""
    lines = [f"# Delivery - {work.slug}", "", "## Goal", "", brief.goal, ""]
    if decision:
        lines += ["## Decision", "", decision, ""]
    lines += ["## Gate", "", f"`{last['command']}` exited {last['exit']}", "", results,
              "## Commits since freeze", "", "```", commits, "```", ""]
    work.path("delivery.md").write_text("\n".join(lines))
    if decision == "promote":
        _promote(work, brief, frozen)
    return str(work.path("delivery.md").relative_to(work.root))


def _promote(work: Work, brief: briefs.Brief, frozen: dict) -> None:
    experiment = work.experiment() or {}
    failure_mode = experiment.get("failure_mode", "(not named in experiment.json)")
    targets = experiment.get("target_cases", [])
    build = Work(work.root, f"{work.slug}-build")
    build.dir.mkdir(parents=True, exist_ok=True)
    gate_cmd = f"rl gate {build.slug} --regression-only"
    lines = [
        f"# {work.slug} - build", "",
        f"**Profile**: {frozen['profile']}", "**Lane**: build", "",
        "## Goal", "", f"Fix in code the Failure Mode the Experiment `{work.slug}` showed: {failure_mode}", "",
        "## Failure Mode", "", failure_mode, "",
        "## Target Cases", "", *[f"- {case}" for case in targets], "",
        "## Proof", "", f"`{gate_cmd}`", "",
        "## Readiness", "", "| Item | State | Why |", "| --- | --- | --- |",
        f"| Failure Mode | ready | shown by Experiment {work.slug} |",
        "| Code path | needs attention | Diagnosis named the cause; the build plan locates it |", "",
    ]
    build.path("brief.md").write_text("\n".join(lines))
