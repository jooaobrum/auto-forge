import json

from conftest import frozen, run, verified


def passed_variant(host, slug="exp"):
    base = [run("q01", n, recall=0.5) for n in (1, 2, 3)] + [run("q07", touched=["skill:history"])]
    frozen(host, base, slug=slug)
    host.exp("select", slug, "--variant", "v1")
    host.runs(slug, "v1", "q01", [run("q01", n, recall=1.0) for n in (1, 2, 3)])
    host.runs(slug, "v1", "q07", [run("q07")])
    host.write("prompts/history.md", "cite every record you read, by id\n")
    host.commit("fix(prompt): cite what was read")
    code, out = host.exp("gate", slug, "--variant", "v1")
    assert code == 0, out


def streaks(host):
    return json.loads((host.root / ".specs/baseline/agent/streaks.json").read_text())


def test_graduation_streak(host):
    passed_variant(host, "e1")
    verified(host, "e1")
    code, out = host.exp("deliver", "e1", "--decision", "adopt")
    assert code == 0, out
    assert streaks(host) == {"q01": 1, "q07": 1}
    # two more adopted Experiments in which both pass, then one in which q07 fails
    for n in (2, 3):
        slug = f"e{n}"
        host.spec(slug)
        host.commit(slug)
        host.exp("freeze", slug)
        host.exp("select", slug, "--variant", "v1")
        host.runs(slug, "v1", "q01", [run("q01", k, recall=1.0) for k in (1, 2, 3)])
        host.runs(slug, "v1", "q07", [run("q07")])
        host.exp("gate", slug, "--variant", "v1")
        verified(host, slug)
        code, out = host.exp("deliver", slug, "--decision", "adopt")
        assert code == 0, out
    assert streaks(host) == {"q01": 3, "q07": 3}
    text = (host.root / ".specs/features/e3/delivery.md").read_text()
    assert "## Proposed for regression" in text and "- q01" in text and "- q07" in text
    assert "## Proposed for regression" not in (host.root / ".specs/features/e1/delivery.md").read_text()
    # a failing capability Case resets
    gate = json.loads((host.root / ".specs/features/e3/gate.json").read_text())
    gate["verdicts"]["q07"] = False
    (host.root / ".specs/features/e3/gate.json").write_text(json.dumps(gate))
    host.exp("deliver", "e3", "--decision", "adopt")
    assert streaks(host)["q07"] == 0


def test_regression_cases_do_not_count_toward_graduation(host):
    cases = "| Case | Question | Rubric | Tier |\n| --- | --- | --- | --- |\n| q01 | a | r | |\n| q07 | b | r | regression |"
    base = [run("q01", n, recall=0.5) for n in (1, 2, 3)] + [run("q07", touched=["skill:history"])]
    frozen(host, base, cases=cases)
    host.exp("select", "exp", "--variant", "v1")
    host.runs("exp", "v1", "q01", [run("q01", n) for n in (1, 2, 3)])
    host.runs("exp", "v1", "q07", [run("q07")])
    host.exp("gate", "exp", "--variant", "v1")
    verified(host)
    host.exp("deliver", "exp", "--decision", "adopt")
    assert streaks(host) == {"q01": 1}


def test_deliver_rules_and_promote(host):
    frozen(host, [run("q01", n, recall=0.5) for n in (1, 2, 3)])
    code, out = host.exp("deliver", "exp", "--decision", "adopt")
    assert code == 2 and "no gate has run" in out
    host.exp("select", "exp", "--variant", "v1")
    host.runs("exp", "v1", "q01", [run("q01", n, recall=0.5) for n in (1, 2, 3)])
    host.exp("gate", "exp", "--variant", "v1")
    code, out = host.exp("deliver", "exp", "--decision", "adopt")
    assert code == 2 and "the last gate failed" in out
    code, out = host.exp("deliver", "exp")
    assert code == 2 and "--decision" in out
    code, out = host.exp("deliver", "exp", "--decision", "reject")
    assert code == 0, out
    host.runs("exp", "v1", "q01", [run("q01", n, recall=1.0) for n in (1, 2, 3)])
    host.exp("gate", "exp", "--variant", "v1")
    code, out = host.exp("deliver", "exp", "--decision", "promote")
    assert code == 2 and "no verification.md" in out
    verified(host)
    code, out = host.exp("deliver", "exp", "--decision", "promote")
    assert code == 0, out
    text = (host.root / ".specs/features/exp-build/plan.md").read_text()
    assert "**Lane**: build" in text
    assert "**Failure mode**: reads history, does not cite it" in text
    assert "- q01" in text
    assert "experiment.py gate exp --regression-only" in text


def test_adopt_needs_an_independent_passing_verification(host):
    passed_variant(host)
    for kwargs, message in (({"verdict": "FAIL"}, "is not PASS"),
                            ({"variant": "v0"}, "the last gate ran v1"),
                            ({"verifier": "self-verified"}, "never the author"),
                            ({"verifier": "fresh-context"}, "needs **Fallback**"),
                            ({"findings": "| Finding | Evidence | Fix | Closed |\n| --- | --- | --- | --- |\n"
                                          "| games the rubric | t-88 | cite only used | |"}, "finding not closed")):
        verified(host, **kwargs)
        code, out = host.exp("deliver", "exp", "--decision", "adopt")
        assert code == 2 and message in out, (kwargs, out)
    verified(host, verifier="fresh-context\n**Fallback**: genie - no subagents")
    code, out = host.exp("deliver", "exp", "--decision", "adopt")
    assert code == 0, out
    text = (host.root / ".specs/features/exp/delivery.md").read_text()
    assert "## Warnings" in text and "genie - no subagents" in text and "**Verdict**: PASS" in text
