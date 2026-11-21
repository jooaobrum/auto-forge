from conftest import frozen_experiment, run


def ready_variant(host):
    host.rl("select", "exp", "--variant", "v1")
    host.runs("exp", "v1", "q01", [run("q01", n, recall=1.0) for n in (1, 2, 3)])


def test_outside_scope_is_named(host):
    frozen_experiment(host, [run("q01", n, recall=0.5) for n in (1, 2, 3)])
    ready_variant(host)
    host.write("prompts/history.md", "cite every record you read, by id\n")
    host.write(".lanes/baseline/agent/q99.json", '{"case": "q99", "runs": [], "touched": []}')
    code, out = host.rl("gate", "exp", "--variant", "v1")
    assert code == 0, out
    assert "outside Edit Scope" not in out
    host.write("tools/sql.py", "x = 1\n")
    host.commit("variant edits a tool")
    host.write("notes/new_file.md", "untracked\n")
    code, out = host.rl("gate", "exp", "--variant", "v1")
    assert code == 1
    assert "FAIL outside Edit Scope: tools/sql.py" in out
    assert "FAIL outside Edit Scope: notes/new_file.md" in out
    assert "prompts/history.md" not in out


def test_default_edit_scope(host):
    frozen_experiment(host, [run("q01", n, recall=0.5) for n in (1, 2, 3)], edit_scope=None)
    ready_variant(host)
    host.write("prompts/system.md", "changed\n")
    code, out = host.rl("gate", "exp", "--variant", "v1")
    assert code == 0, out
    host.write("tools/resolve.py", "changed\n")
    code, out = host.rl("gate", "exp", "--variant", "v1")
    assert code == 1
    assert "FAIL outside Edit Scope: tools/resolve.py" in out
