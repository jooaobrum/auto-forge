from conftest import frozen_experiment, run


def test_budget_spent_exits_4(host):
    frozen_experiment(host, [run("q01")], budget_tokens=100_000)
    host.runs("exp", "v1", "a", [run("q01", tokens=60_000), run("q01", 2, tokens=39_999)])
    code, out = host.rl("budget", "exp")
    assert code == 0, out
    assert "99999 of 100000" in out
    code, _ = host.rl("select", "exp", "--variant", "v1")
    assert code == 0
    host.runs("exp", "v1", "a", [run("q01", tokens=60_000), run("q01", 2, tokens=40_000)])
    code, out = host.rl("budget", "exp")
    assert code == 4
    assert "100000 of 100000" in out and "ask the user" in out
    code, out = host.rl("select", "exp", "--variant", "v2")
    assert code == 4
    assert "ask the user" in out


def test_add_records_user_words(host):
    frozen_experiment(host, [run("q01")], budget_tokens=100_000)
    host.runs("exp", "v1", "a", [run("q01", tokens=100_000)])
    code, out = host.rl("budget", "exp", "--add", "50000", "--user", "yes, 50k more")
    assert code == 0, out
    code, out = host.rl("budget", "exp", "--add", "10000", "--user", "last 10k")
    assert code == 0
    code, out = host.rl("budget", "exp")
    assert code == 0
    assert "100000 of 160000" in out
    lines = (host.root / ".lanes/work/exp/budget.md").read_text().splitlines()
    added = [line for line in lines if line.startswith("- ")]
    assert len(added) == 2
    assert '+50000 input tokens - user: "yes, 50k more"' in added[0]
    assert '+10000 input tokens - user: "last 10k"' in added[1]
    assert added[0].startswith("- 20")


def test_add_without_user_is_refused(host):
    frozen_experiment(host, [run("q01")], budget_tokens=100_000)
    host.runs("exp", "v1", "a", [run("q01", tokens=100_000)])
    code, out = host.rl("budget", "exp", "--add", "50000")
    assert code == 2
    assert "--user" in out
    code, out = host.rl("budget", "exp", "--add", "50000", "--user", "  ")
    assert code == 2
    code, out = host.rl("budget", "exp")
    assert code == 4
    assert "100000 of 100000" in out
