import pytest
from conftest import frozen, run, sh

TIERED = ("| Case | Question | Rubric | Tier |\n| --- | --- | --- | --- |\n"
          "| q01 | Why? | cause | capability |\n| q07 | History? | events | {tier} |")


def base_q01_q07():
    return [run("q01", n, recall=0.5, touched=["skill:history"]) for n in (1, 2, 3)] + \
           [run("q07", n, touched=["skill:history"]) for n in (1, 2, 3)]


def improved(host, variant="v1"):
    host.runs("exp", variant, "q01", [run("q01", n, recall=1.0) for n in (1, 2, 3)])


@pytest.mark.parametrize("passing, ok", [(3, True), (2, False)])
def test_regression_tier_is_pass_hat_k(host, passing, ok):
    frozen(host, base_q01_q07(), cases=TIERED.format(tier="regression"), extra="**k**: affected 3")
    host.exp("select", "exp", "--variant", "v1")
    improved(host)
    host.runs("exp", "v1", "q07", [run("q07", n, recall=1.0 if n <= passing else 0.1) for n in (1, 2, 3)])
    code, out = host.exp("gate", "exp", "--variant", "v1")
    assert code == (0 if ok else 1), out
    assert ("FAIL q07: regressed" in out) is not ok


@pytest.mark.parametrize("tier", ["capability", ""])
@pytest.mark.parametrize("runs_, passing, ok", [(3, 2, True), (2, 1, False)])
def test_capability_tier_is_majority(host, tier, runs_, passing, ok):
    frozen(host, base_q01_q07(), cases=TIERED.format(tier=tier), extra=f"**k**: affected {runs_}")
    host.exp("select", "exp", "--variant", "v1")
    improved(host)
    host.runs("exp", "v1", "q07", [run("q07", n, recall=1.0 if n <= passing else 0.1) for n in range(1, runs_ + 1)])
    code, out = host.exp("gate", "exp", "--variant", "v1")
    assert code == (0 if ok else 1), out


def test_regression_is_named(host):
    frozen(host, base_q01_q07())
    host.exp("select", "exp", "--variant", "v1")
    improved(host)
    host.runs("exp", "v1", "q07", [run("q07", recall=0.2)])
    code, out = host.exp("gate", "exp", "--variant", "v1")
    assert code == 1
    assert "FAIL q07: regressed - passed the Baseline, fails in v1" in out


@pytest.mark.parametrize("tokens, ok", [(57_500, True), (57_501, False), (150_000, False)])
def test_guardrail_budget_boundary(host, tokens, ok):
    frozen(host, base_q01_q07())
    host.exp("select", "exp", "--variant", "v1")
    improved(host)
    host.runs("exp", "v1", "q07", [run("q07", tokens=tokens)])
    code, out = host.exp("gate", "exp", "--variant", "v1")
    assert code == (0 if ok else 1), out
    assert ("FAIL q07: guardrail input_tokens" in out) is not ok


@pytest.mark.parametrize("q02_after, ok", [(0.39, False), (0.4, True), (1.0, True)])
def test_target_mean_over_target_cases(host, q02_after, ok):
    base = [run("q01", n, recall=0.5) for n in (1, 2, 3)] + [run("q02", n, recall=0.5) for n in (1, 2, 3)]
    cases = "| q01 | a | r |\n| q02 | b | r |"
    frozen(host, base, cases=cases, targets="q01, q02", target="+0.2")
    host.exp("select", "exp", "--variant", "v1")
    host.runs("exp", "v1", "q01", [run("q01", n, recall=1.0) for n in (1, 2, 3)])
    host.runs("exp", "v1", "q02", [run("q02", n, recall=q02_after) for n in (1, 2, 3)])
    code, out = host.exp("gate", "exp", "--variant", "v1")
    assert code == (0 if ok else 1), out
    assert ("FAIL target cited_recall" in out) is not ok


def test_missing_runs_and_confirm(host):
    base = base_q01_q07() + [run("q09", touched=["tool:resolve_equipment"])]
    frozen(host, base)
    host.exp("select", "exp", "--variant", "v1")
    host.runs("exp", "v1", "q01", [run("q01", 1, recall=1.0)])
    code, out = host.exp("gate", "exp", "--variant", "v1")
    assert code == 1
    assert "FAIL q01: 2 of 3 runs missing" in out
    assert "FAIL q07: 1 of 1 runs missing" in out
    improved(host)
    host.runs("exp", "v1", "q07", [run("q07")])
    code, out = host.exp("gate", "exp", "--variant", "v1")
    assert code == 0, out
    code, out = host.exp("gate", "exp", "--variant", "v1", "--confirm")
    assert code == 1
    assert "FAIL q09: 1 of 1 runs missing" in out
    host.runs("exp", "v1", "q09", [run("q09")])
    code, out = host.exp("gate", "exp", "--variant", "v1", "--confirm")
    assert code == 0, out


def test_regression_only(host):
    frozen(host, base_q01_q07())
    host.exp("select", "exp", "--variant", "v1")
    host.runs("exp", "v1", "q01", [run("q01", n, recall=0.5) for n in (1, 2, 3)])
    host.runs("exp", "v1", "q07", [run("q07")])
    code, out = host.exp("gate", "exp", "--variant", "v1", "--regression-only")
    assert code == 0, out
    host.runs("exp", "v1", "q07", [run("q07", recall=0.1, tokens=99_000)])
    host.write("tools/resolve.py", "def resolve(): return 1\n")
    (host.root / ".specs/features/exp/runs/v1/q01.json").unlink()
    code, out = host.exp("gate", "exp", "--variant", "v1", "--regression-only")
    assert code == 1
    assert "FAIL q07: regressed" in out
    assert "FAIL q07: guardrail input_tokens" in out
    assert "FAIL q01: 3 of 3 runs missing" in out
    assert "FAIL outside Edit Scope: tools/resolve.py" in out
    assert "target cited_recall" not in out


def test_edit_scope(host):
    frozen(host, [run("q01", n, recall=0.5) for n in (1, 2, 3)] + [run("q07")], scope="- prompts/")
    host.exp("select", "exp", "--variant", "v1")
    improved(host)
    host.runs("exp", "v1", "q07", [run("q07")])  # prompts/ holds the system prompt, so every Case is affected
    host.write("prompts/history.md", "cite every record you read\n")
    host.write("prompts/my notes.md", "a path with a space, in scope\n")
    host.write(".specs/baseline/agent/q99.json", '{"case": "q99", "runs": [], "touched": []}')
    code, out = host.exp("gate", "exp", "--variant", "v1")
    assert code == 0, out
    sh(host.root, "git", "mv", "tools/resolve.py", "prompts/resolve.py")
    host.commit("move a tool into scope")
    host.write("notes/new file.md", "untracked, outside\n")
    host.write(".specs/features/other/plan.md", "another piece of work\n")
    code, out = host.exp("gate", "exp", "--variant", "v1")
    assert code == 1
    assert "FAIL outside Edit Scope: tools/resolve.py" in out
    assert "FAIL outside Edit Scope: notes/new file.md" in out
    assert "FAIL outside Edit Scope: .specs/features/other/plan.md" in out
    assert "prompts/my notes.md" not in out and "prompts/history.md" not in out


def test_select_tiers_affects_all_and_stale(host):
    base = [run("q01", touched=["skill:history"]), run("q07", touched=["skill:history"]),
            run("q09", touched=["tool:resolve_equipment"])]
    frozen(host, base)
    code, out = host.exp("select", "exp", "--variant", "v1")
    assert code == 0, out
    selection = __import__("json").loads((host.root / ".specs/features/exp/selection.json").read_text())
    assert selection["cases"]["q01"] == {"tier": "target", "k": 3}
    assert selection["cases"]["q07"] == {"tier": "affected", "k": 1}
    assert selection["cases"]["q09"] == {"tier": "stable", "k": 0}
    assert selection["stale"] == []
    host.write("tools/resolve.py", "def resolve(): return 'changed'\n")
    host.commit("tool changes")
    host.exp("freeze", "exp")
    host.exp("select", "exp", "--variant", "v1")
    selection = __import__("json").loads((host.root / ".specs/features/exp/selection.json").read_text())
    assert selection["stale"] == ["q09"]
    host.spec("exp", scope="- prompts/system.md")
    host.exp("select", "exp", "--variant", "v1")
    selection = __import__("json").loads((host.root / ".specs/features/exp/selection.json").read_text())
    assert selection["cases"]["q09"] == {"tier": "affected", "k": 1}


def test_malformed_results_file_exits_2(host):
    frozen(host, base_q01_q07())
    host.exp("select", "exp", "--variant", "v1")
    host.write(".specs/features/exp/runs/v1/broken.json", "{not json")
    code, out = host.exp("gate", "exp", "--variant", "v1")
    assert code == 2
    assert "broken.json" in out
