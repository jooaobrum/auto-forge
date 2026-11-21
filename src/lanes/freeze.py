"""Freeze: the approved plan becomes the fixed start of the work."""

from __future__ import annotations

import re

from lanes import brief as briefs
from lanes.work import LanesError, Work, git, load_config, profile_config

APPROVED = re.compile(r"^\*\*Approved\*\*:\s*(?!<)\S", re.MULTILINE)


def plan_path(work: Work, brief: briefs.Brief):
    if brief.lane == "research":
        return work.path("experiment.md")
    return work.root / brief.plan if brief.plan else work.path("plan.md")


def freeze(work: Work) -> dict:
    code, errors, _ = briefs.check(work)
    if code:
        raise LanesError("the brief is not ready: " + "; ".join(errors))
    brief = briefs.load(work)
    plan = plan_path(work, brief)
    if not plan.exists():
        raise LanesError(f"{plan.relative_to(work.root)} is missing")
    if not APPROVED.search(plan.read_text()):
        raise LanesError(f"{plan.relative_to(work.root)} has no **Approved**: line - a human approves first")
    experiment = work.experiment()
    if brief.lane == "research" and experiment is None:
        raise LanesError("a research Experiment needs experiment.json")
    if experiment is not None:
        declared = profile_config(load_config(work.root), brief.profile).get("metrics", [])
        target = experiment.get("target_metric")
        if target is not None and target not in declared:
            raise LanesError(f"target metric `{target}` is not declared for profile `{brief.profile}`")
    commit = git(work.root, "rev-parse", "HEAD").strip()
    frozen = {"commit": commit, "profile": brief.profile, "lane": brief.lane,
              "plan": str(plan.relative_to(work.root))}
    work.write_json("frozen.json", frozen)
    return frozen
