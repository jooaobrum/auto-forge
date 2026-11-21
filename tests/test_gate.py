import pytest
from conftest import frozen_experiment, run

from lanes.gate import case_passes, run_passes

THRESHOLDS = {"cited_recall": 0.8, "correctness": 1}


def test_majority_rule():
    good = {"cited_recall": 0.9, "correctness": 1}
    low_recall = {"cited_recall": 0.5, "correctness": 1}
    wrong = {"cited_recall": 0.9, "correctness": 0}
    assert run_passes(good, THRESHOLDS)
    assert not run_passes(low_recall, THRESHOLDS)
    assert not run_passes(wrong, THRESHOLDS)
    assert not run_passes({"cited_recall": 0.9}, THRESHOLDS)
    assert run_passes({"cited_recall": 0.8, "correctness": 1}, THRESHOLDS)
    assert case_passes([good, good, wrong], THRESHOLDS)
    assert not case_passes([good, wrong, low_recall], THRESHOLDS)
    assert case_passes([good], THRESHOLDS)
    assert not case_passes([good, wrong], THRESHOLDS)


def base_q01_q07():
    return [run("q01", n, recall=0.5, touched=["skill:history"]) for n in (1, 2, 3)] + \
           [run("q07", touched=["skill:history"])]


def improved_q01(host, variant="v1"):
    host.runs("exp", variant, "q01", [run("q01", n, recall=1.0) for n in (1, 2, 3)])


def test_regression_is_named(host):
    frozen_experiment(host, base_q01_q07())
    host.rl("select", "exp", "--variant", "v1")
    improved_q01(host)
    host.runs("exp", "v1", "q07", [run("q07", recall=0.2)])
    code, out = host.rl("gate", "exp", "--variant", "v1")
    assert code == 1
    assert "FAIL q07: regressed" in out
    host.runs("exp", "v1", "q07", [run("q07", recall=1.0)])
    code, out = host.rl("gate", "exp", "--variant", "v1")
    assert code == 0, out


@pytest.mark.parametrize("tokens, passes", [(57_500, True), (57_501, False), (150_000, False)])
def test_guardrail_budget_boundary(host, tokens, passes):
    frozen_experiment(host, base_q01_q07())
    host.rl("select", "exp", "--variant", "v1")
    improved_q01(host)
    host.runs("exp", "v1", "q07", [run("q07", tokens=tokens)])
    code, out = host.rl("gate", "exp", "--variant", "v1")
    assert code == (0 if passes else 1), out
    assert ("FAIL q07: guardrail input_tokens" in out) is not passes


@pytest.mark.parametrize("after, passes", [(0.59, False), (0.6, True), (1.0, True)])
def test_target_must_improve(host, after, passes):
    frozen_experiment(host, base_q01_q07())
    host.rl("select", "exp", "--variant", "v1")
    host.runs("exp", "v1", "q01", [run("q01", n, recall=after) for n in (1, 2, 3)])
    host.runs("exp", "v1", "q07", [run("q07")])
    code, out = host.rl("gate", "exp", "--variant", "v1")
    assert code == (0 if passes else 1), out
    assert ("FAIL target cited_recall" in out) is not passes


def test_missing_runs_fail(host):
    frozen_experiment(host, base_q01_q07())
    host.rl("select", "exp", "--variant", "v1")
    host.runs("exp", "v1", "q01", [run("q01", 1, recall=1.0)])
    code, out = host.rl("gate", "exp", "--variant", "v1")
    assert code == 1
    assert "FAIL q01: 2 of 3 runs missing" in out
    assert "FAIL q07: 1 of 1 runs missing" in out


def test_confirm_requires_stable(host):
    base = base_q01_q07() + [run("q09", touched=["tool:resolve_equipment"])]
    frozen_experiment(host, base)
    host.rl("select", "exp", "--variant", "v1")
    improved_q01(host)
    host.runs("exp", "v1", "q07", [run("q07")])
    code, out = host.rl("gate", "exp", "--variant", "v1")
    assert code == 0, out
    code, out = host.rl("gate", "exp", "--variant", "v1", "--confirm")
    assert code == 1
    assert "FAIL q09: 1 of 1 runs missing" in out
    host.runs("exp", "v1", "q09", [run("q09")])
    code, out = host.rl("gate", "exp", "--variant", "v1", "--confirm")
    assert code == 0, out


def test_results_table(host):
    frozen_experiment(host, base_q01_q07())
    host.rl("select", "exp", "--variant", "v1")
    improved_q01(host)
    host.runs("exp", "v1", "q07", [run("q07", tokens=60_000)])
    host.rl("gate", "exp", "--variant", "v1")
    text = (host.root / ".lanes/work/exp/results.md").read_text()
    assert "| Case | Tier | Baseline | Variant | cited_recall before → after | input_tokens before → after |" in text
    assert "| q01 | target | fail | pass | 0.5 → 1 | 50000 → 50000 |" in text
    assert "| q07 | affected | pass | pass | 1 → 1 | 50000 → 60000 |" in text


def test_regression_only(host):
    frozen_experiment(host, base_q01_q07())
    host.rl("select", "exp", "--variant", "v1")
    host.runs("exp", "v1", "q01", [run("q01", n, recall=0.5) for n in (1, 2, 3)])
    host.runs("exp", "v1", "q07", [run("q07")])
    code, out = host.rl("gate", "exp", "--variant", "v1", "--regression-only")
    assert code == 0, out
    host.runs("exp", "v1", "q07", [run("q07", recall=0.1, tokens=99_000)])
    host.write("tools/resolve.py", "def resolve(): return 1\n")
    (host.root / ".lanes/work/exp/runs/v1/q01.json").unlink()
    code, out = host.rl("gate", "exp", "--variant", "v1", "--regression-only")
    assert code == 1
    assert "FAIL q07: regressed" in out
    assert "FAIL q07: guardrail input_tokens" in out
    assert "FAIL q01: 3 of 3 runs missing" in out
    assert "FAIL outside Edit Scope: tools/resolve.py" in out
    assert "target cited_recall" not in out


def test_malformed_results_file_exits_2(host):
    frozen_experiment(host, base_q01_q07())
    host.rl("select", "exp", "--variant", "v1")
    host.write(".lanes/work/exp/runs/v1/broken.json", "{not json")
    code, out = host.rl("gate", "exp", "--variant", "v1")
    assert code == 2
    assert "broken.json" in out
    (host.root / ".lanes/work/exp/runs/v1/broken.json").unlink()
    host.write(".lanes/work/exp/runs/v1/notes.txt", "hello")
    code, out = host.rl("gate", "exp", "--variant", "v1")
    assert code == 2
    assert "notes.txt" in out


@pytest.mark.parametrize("q02_after, passes", [(0.39, False), (0.4, True)])
def test_target_mean_over_several_cases(host, q02_after, passes):
    base = [run("q01", n, recall=0.5) for n in (1, 2, 3)] + [run("q02", n, recall=0.5) for n in (1, 2, 3)]
    frozen_experiment(host, base, target_cases=["q01", "q02"], min_delta=0.2)
    host.rl("select", "exp", "--variant", "v1")
    host.runs("exp", "v1", "q01", [run("q01", n, recall=1.0) for n in (1, 2, 3)])
    host.runs("exp", "v1", "q02", [run("q02", n, recall=q02_after) for n in (1, 2, 3)])
    code, out = host.rl("gate", "exp", "--variant", "v1")
    assert code == (0 if passes else 1), out
    assert ("FAIL target cited_recall" in out) is not passes, out
