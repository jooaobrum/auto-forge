import json

from conftest import frozen_experiment, run


def selection(host, slug="exp"):
    return json.loads((host.root / f".lanes/work/{slug}/selection.json").read_text())


BASE = [
    run("q01", touched=["skill:history"]),
    run("q07", touched=["skill:history", "tool:resolve_equipment"]),
    run("q09", touched=["tool:resolve_equipment"]),
]


def test_tiers(host):
    frozen_experiment(host, BASE, target_cases=["q01", "q01"])
    code, out = host.rl("select", "exp", "--variant", "v1")
    assert code == 0, out
    cases = selection(host)["cases"]
    assert cases["q01"] == {"tier": "target", "k": 3}
    assert cases["q07"] == {"tier": "affected", "k": 1}
    assert cases["q09"] == {"tier": "stable", "k": 0}
    assert list(cases).count("q01") == 1 and len(cases) == 3


def test_affects_all(host):
    frozen_experiment(host, BASE, edit_scope=["prompts/system.md"])
    code, out = host.rl("select", "exp", "--variant", "v1")
    assert code == 0, out
    cases = selection(host)["cases"]
    assert cases["q01"]["tier"] == "target"
    assert cases["q07"] == {"tier": "affected", "k": 1}
    assert cases["q09"] == {"tier": "affected", "k": 1}


def test_stale_baseline(host):
    frozen_experiment(host, BASE)
    code, _ = host.rl("select", "exp", "--variant", "v1")
    assert code == 0
    assert selection(host)["stale"] == []
    # the code behind q09 changes and the Experiment is frozen again on top of it
    host.write("tools/resolve.py", "def resolve(): return 'changed'\n")
    host.commit("change the tool")
    code, _ = host.rl("freeze", "exp")
    assert code == 0
    code, out = host.rl("select", "exp", "--variant", "v1")
    assert code == 0
    # q07 and q09 both ran the changed tool; q01 touched only the unchanged history prompt
    assert selection(host)["stale"] == ["q07", "q09"]
    assert "rerun these first: q07, q09" in out


def test_working_tree_edits_do_not_make_a_baseline_stale(host):
    frozen_experiment(host, BASE)
    host.write("prompts/history.md", "a variant's edit\n")
    host.rl("select", "exp", "--variant", "v1")
    assert selection(host)["stale"] == []


def test_variant_cap(host):
    frozen_experiment(host, BASE)
    for name in ("v1", "v2", "v3"):
        code, _ = host.rl("select", "exp", "--variant", name)
        assert code == 0
    code, out = host.rl("select", "exp", "--variant", "v4")
    assert code == 3
    assert "variant cap reached" in out


def test_reselect_same_variant(host):
    frozen_experiment(host, BASE)
    for name in ("v1", "v1", "v2", "v2", "v3"):
        code, _ = host.rl("select", "exp", "--variant", name)
        assert code == 0
    code, _ = host.rl("select", "exp", "--variant", "v3")
    assert code == 0
