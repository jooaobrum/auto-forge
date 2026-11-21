from conftest import frozen_experiment, run


def failed_variant(host):
    frozen_experiment(host, [run("q01", n, recall=0.5) for n in (1, 2, 3)])
    host.rl("select", "exp", "--variant", "v1")
    host.runs("exp", "v1", "q01", [run("q01", n, recall=0.5) for n in (1, 2, 3)])
    code, _ = host.rl("gate", "exp", "--variant", "v1")
    assert code == 1


def passed_variant(host):
    frozen_experiment(host, [run("q01", n, recall=0.5) for n in (1, 2, 3)])
    host.rl("select", "exp", "--variant", "v1")
    host.runs("exp", "v1", "q01", [run("q01", n, recall=1.0) for n in (1, 2, 3)])
    host.write("prompts/history.md", "cite every record you read, by id\n")
    host.commit("fix(prompt): cite what was read")
    code, out = host.rl("gate", "exp", "--variant", "v1")
    assert code == 0, out


def test_deliver_requires_green_gate(host):
    frozen_experiment(host, [run("q01")])
    code, out = host.rl("deliver", "exp", "--decision", "adopt")
    assert code == 2
    assert "no gate has run" in out
    host.rl("select", "exp", "--variant", "v1")
    host.runs("exp", "v1", "q01", [run("q01", n, recall=0.5) for n in (1, 2, 3)])
    host.rl("gate", "exp", "--variant", "v1")
    code, out = host.rl("deliver", "exp", "--decision", "adopt")
    assert code == 2
    assert "the last gate failed" in out
    code, out = host.rl("deliver", "exp", "--decision", "reject")
    assert code == 0, out


def test_research_delivery_needs_a_decision(host):
    passed_variant(host)
    code, out = host.rl("deliver", "exp")
    assert code == 2
    assert "--decision" in out


def test_delivery_contents(host):
    passed_variant(host)
    code, out = host.rl("deliver", "exp", "--decision", "adopt")
    assert code == 0, out
    text = (host.root / ".lanes/work/exp/delivery.md").read_text()
    assert "The agent cites the history records it reads." in text
    assert "`rl gate exp --variant v1` exited 0" in text
    assert "| q01 | target | fail | pass | 0.5 → 1 |" in text
    assert "fix(prompt): cite what was read" in text
    assert "## Decision\n\nadopt" in text


def test_promote_writes_build_brief(host):
    passed_variant(host)
    code, out = host.rl("deliver", "exp", "--decision", "promote")
    assert code == 0, out
    text = (host.root / ".lanes/work/exp-build/brief.md").read_text()
    assert "**Lane**: build" in text
    assert "reads history, does not cite it" in text
    assert "- q01" in text
    assert "`rl gate exp-build --regression-only`" in text
    code, out = host.rl("brief", "exp-build")
    assert code == 0, out
