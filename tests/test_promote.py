from __future__ import annotations

import json
import random

import pytest
from conftest import load

promote = load("agent-spec-mlops", "promote")

SLUG = "churn-mlops"
SPEC = """# churn - to production

**Profile**: model
**Lane**: build

## Promotion

**Champion**: version 2
**Challenger**: version 3
**Period**: 2026-10-01..2026-10-31
**Metric**: {metric}
**Min gain**: {min_gain}
**Tolerance**: {tolerance}

| Slice | Description | Target |
| --- | --- | --- |
| all | every account scored in October | yes |
| new | tenure under 6 months | |
| long | tenure of 6 months or more | |
"""


@pytest.fixture
def work(tmp_path, capsys):
    folder = tmp_path / ".specs/features" / SLUG
    folder.mkdir(parents=True)

    class Work:
        root = tmp_path

        def spec(self, metric="accuracy", min_gain="0.01", tolerance="0", text=None):
            (folder / "spec.md").write_text(text or SPEC.format(metric=metric, min_gain=min_gain, tolerance=tolerance))

        def prod(self, code=0):
            (folder / "gate.json").write_text(json.dumps({"exit": code, "command": f"validate_prod.py {SLUG}",
                                                          "findings": []}))

        def runs(self, model, means, n=30, noise=0.01, seed=1):
            rng = random.Random(seed)
            rows = [{"case": name, "run": i, "metrics": {"accuracy": mean + rng.uniform(-noise, noise),
                                                         "rmse": mean + rng.uniform(-noise, noise)}}
                    for name, mean in means.items() for i in range(n)]
            (folder / "runs" / model).mkdir(parents=True, exist_ok=True)
            (folder / "runs" / model / "backtest.json").write_text(json.dumps({"runs": rows}))

        def call(self, *args):
            capsys.readouterr()
            code = promote.main(["--root", str(tmp_path), *args])
            return code, capsys.readouterr().out

    w = Work()
    w.spec()
    w.prod()
    return w


CHAMPION = {"all": 0.80, "new": 0.70, "long": 0.85}


def test_challenger_wins_without_a_regressed_slice(work):
    work.runs("champion", CHAMPION, seed=1)
    work.runs("challenger", {"all": 0.84, "new": 0.76, "long": 0.86}, seed=2)
    code, out = work.call("gate", SLUG)
    assert code == 0, out
    report = (work.root / ".specs/features" / SLUG / "promotion.md").read_text()
    assert "Gate: `promote.py gate churn-mlops` - **pass**" in report
    assert "| all | yes | 30 |" in report and "Target gain over all: +0.04" in report
    code, out = work.call("approve", SLUG)
    assert code == 2 and "--user needs" in out
    code, out = work.call("approve", SLUG, "--user", "ok, swap it")
    assert code == 0 and "move the champion alias to version 3" in out and "back to version 2" in out
    log = (work.root / ".specs/prod/promotions.md").read_text()
    assert 'challenger version 3 replaces champion version 2 - user: "ok, swap it"' in log
    approved = json.loads((work.root / ".specs/features" / SLUG / "promotion.json").read_text())["approved"]
    assert approved["user"] == "ok, swap it"


def test_a_slice_that_regresses_fails_even_when_the_mean_wins(work):
    work.runs("champion", CHAMPION, seed=1)
    work.runs("challenger", {"all": 0.86, "new": 0.64, "long": 0.90}, seed=2)
    code, out = work.call("gate", SLUG)
    assert code == 1 and "FAIL new: regressed - accuracy 0.70" in out
    code, out = work.call("approve", SLUG, "--user", "ok")
    assert code == 2 and "the promotion gate failed" in out
    work.spec(tolerance="0.1")
    assert work.call("gate", SLUG)[0] == 0


def test_the_target_gain_needs_a_ci_above_zero_and_the_min_gain(work):
    work.runs("champion", CHAMPION, seed=1, noise=0.05)
    work.runs("challenger", {"all": 0.805, "new": 0.70, "long": 0.85}, seed=2, noise=0.05)
    code, out = work.call("gate", SLUG)
    assert code == 1 and "target: the CI of the gain" in out and "does not sit above 0" in out
    work.runs("challenger", {"all": 0.805, "new": 0.70, "long": 0.85}, seed=2, noise=0.0)
    work.runs("champion", CHAMPION, seed=1, noise=0.0)
    code, out = work.call("gate", SLUG)
    assert code == 1 and "below the min gain 0.01" in out and "does not sit above 0" not in out


def test_lower_is_better_metrics_flip_the_sign(work):
    work.spec(metric="rmse", min_gain="0")
    work.runs("champion", {"all": 10.0, "new": 12.0, "long": 9.0}, seed=1)
    work.runs("challenger", {"all": 9.0, "new": 11.5, "long": 8.9}, seed=2)
    assert work.call("gate", SLUG)[0] == 0
    work.runs("challenger", {"all": 9.0, "new": 13.0, "long": 8.9}, seed=2)
    code, out = work.call("gate", SLUG)
    assert code == 1 and "new: regressed" in out


def test_too_few_resamples_and_missing_runs(work):
    work.runs("champion", CHAMPION, n=5)
    work.runs("challenger", CHAMPION, n=5)
    code, out = work.call("gate", SLUG)
    assert code == 1 and "5 paired resamples, needs at least 20" in out
    work.runs("challenger", {"all": 0.9, "long": 0.9})
    work.runs("champion", CHAMPION)
    code, out = work.call("gate", SLUG)
    assert code == 1 and "new: no runs for the challenger" in out


def test_production_standard_and_spec_come_first(work):
    work.prod(code=1)
    code, out = work.call("gate", SLUG)
    assert code == 2 and "validate_prod.py churn-mlops has not passed" in out
    work.prod()
    work.spec(text="# x\n\n## Goal\n\nnothing\n")
    code, out = work.call("gate", SLUG)
    assert code == 2 and "no ## Promotion section" in out
    work.spec(text=SPEC.format(metric="accuracy", min_gain="0", tolerance="0").replace("| yes |", "| |")
              .replace("| all |", "| everyone |"))
    code, out = work.call("gate", SLUG)
    assert code == 2 and "at least one Target slice" in out


def test_the_first_champion_has_nothing_to_compare(work):
    work.spec(text="# x\n\n## Promotion\n\n**Champion**: none\n**Challenger**: version 1\n**Metric**: accuracy\n")
    code, out = work.call("gate", SLUG)
    assert code == 0, out
    assert "No champion yet" in (work.root / ".specs/features" / SLUG / "promotion.md").read_text()


def test_metric_defaults_to_the_problem(work):
    (work.root / ".specs/LAB.md").write_text("# LAB\n\n## Problem\n\n**Metric**: accuracy\n")
    work.spec(text=SPEC.format(metric="", min_gain="0", tolerance="0").replace("**Metric**: \n", ""))
    work.runs("champion", CHAMPION, seed=1)
    work.runs("challenger", {"all": 0.84, "new": 0.76, "long": 0.86}, seed=2)
    assert work.call("gate", SLUG)[0] == 0


def test_percentile():
    assert promote.percentile([1, 2, 3, 4, 5], 0.5) == 3
    assert promote.percentile([0, 10], 0.025) == pytest.approx(0.25)
