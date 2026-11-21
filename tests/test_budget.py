from conftest import frozen, run


def test_budget_stop_and_add(host):
    frozen(host, [run("q01")], extra="**Budget**: 100000")
    host.runs("exp", "v1", "a", [run("q01", tokens=60_000), run("q01", 2, tokens=39_999)])
    code, out = host.exp("budget", "exp")
    assert code == 0 and "99999 of 100000" in out
    code, _ = host.exp("select", "exp", "--variant", "v1")
    assert code == 0
    host.runs("exp", "v1", "a", [run("q01", tokens=60_000), run("q01", 2, tokens=40_000)])
    code, out = host.exp("budget", "exp")
    assert code == 4 and "100000 of 100000" in out and "ask the user" in out
    code, out = host.exp("select", "exp", "--variant", "v2")
    assert code == 4 and "ask the user" in out
    code, out = host.exp("budget", "exp", "--add", "50000")
    assert code == 2 and "--user" in out
    code, out = host.exp("budget", "exp", "--add", "50000", "--user", "  ")
    assert code == 2
    assert host.exp("budget", "exp")[0] == 4
    code, out = host.exp("budget", "exp", "--add", "50000", "--user", "yes, 50k more")
    assert code == 0, out
    host.exp("budget", "exp", "--add", "10000", "--user", "last 10k")
    code, out = host.exp("budget", "exp")
    assert code == 0 and "100000 of 160000" in out
    added = [ln for ln in (host.root / ".specs/features/exp/budget.md").read_text().splitlines() if ln.startswith("- ")]
    assert len(added) == 2
    assert '+50000 input tokens - user: "yes, 50k more"' in added[0]
    assert '+10000 input tokens - user: "last 10k"' in added[1]


def test_lab_budget_is_the_default(host):
    frozen(host, [run("q01")])
    host.runs("exp", "v1", "a", [run("q01", tokens=1_000_000)])
    code, out = host.exp("budget", "exp")
    assert code == 4 and "of 1000000" in out


def test_variant_cap(host):
    frozen(host, [run("q01")])
    for name in ("v1", "v2", "v3", "v3"):
        assert host.exp("select", "exp", "--variant", name)[0] == 0
    code, out = host.exp("select", "exp", "--variant", "v4")
    assert code == 3 and "variant cap reached" in out
