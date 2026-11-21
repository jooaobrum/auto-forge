"""Selection: which Cases a variant runs, and how many times."""

from __future__ import annotations

from lanes import baseline as baselines
from lanes.surface import content_hash, item_paths, overlaps
from lanes.work import Work, load_config, profile_config

TARGET, AFFECTED, STABLE = "target", "affected", "stable"


def edit_scope(experiment: dict, profile: dict) -> list[str]:
    scope = experiment.get("edit_scope")
    return list(scope) if scope else list(profile.get("default_edit_scope", []))


def variants(work: Work) -> list[str]:
    path = work.path("variants.json")
    return work.read_json("variants.json")["variants"] if path.exists() else []


def cap_reached(work: Work, variant: str) -> bool:
    known = variants(work)
    return variant not in known and len(known) >= int(load_config(work.root).get("max_variants", 3))


def register(work: Work, variant: str) -> None:
    known = variants(work)
    if variant not in known:
        work.write_json("variants.json", {"variants": known + [variant]})


def select(work: Work, variant: str) -> dict:
    frozen = work.frozen()
    config = load_config(work.root)
    profile = profile_config(config, frozen["profile"])
    experiment = work.experiment() or {}
    surface = profile.get("surface", {})
    k = {TARGET: 3, AFFECTED: 1, STABLE: 1, **profile.get("k", {})}
    scope = edit_scope(experiment, profile)
    targets = list(dict.fromkeys(experiment.get("target_cases", [])))
    stored = baselines.load_all(work.root, frozen["profile"])
    everything = any(
        spec.get("affects_all") and any(overlaps(p, scope) for p in spec.get("paths", []))
        for spec in surface.values()
    )
    cases: dict[str, dict] = {}
    for case in targets:
        cases[case] = {"tier": TARGET, "k": int(k[TARGET])}
    for case, base in stored.items():
        if case in cases:
            continue
        touched_paths = item_paths(surface, base.get("touched", []))
        hit = everything or any(overlaps(p, scope) for p in touched_paths)
        cases[case] = {"tier": AFFECTED, "k": int(k[AFFECTED])} if hit else {"tier": STABLE, "k": 0}
    stale = []
    for case in cases:
        base = stored.get(case)
        if base is None:
            stale.append(case)
            continue
        now = content_hash(work.root, item_paths(surface, base.get("touched", [])), frozen["commit"])
        if now != base.get("surface_hash"):
            stale.append(case)
    selection = {"variant": variant, "edit_scope": scope, "k_stable": int(k[STABLE]),
                 "cases": cases, "stale": sorted(stale)}
    register(work, variant)
    work.write_json("selection.json", selection)
    return selection
