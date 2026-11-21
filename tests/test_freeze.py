import json

from conftest import sh


def test_freeze_requires_approval(host, tmp_path_factory, capsys):
    host.experiment("exp")
    host.write(".lanes/work/exp/experiment.md", "# Experiment\n\n**Approved**: <pending>\n")
    code, out = host.rl("freeze", "exp")
    assert code == 2
    assert "no **Approved**: line" in out
    assert not (host.root / ".lanes/work/exp/frozen.json").exists()
    host.write(".lanes/work/exp/experiment.md", "# Experiment\n\n**Approved**: 2026-11-21 - user: \"ok\"\n")
    host.commit("approved")
    head = sh(host.root, "git", "rev-parse", "HEAD").strip()
    code, out = host.rl("freeze", "exp")
    assert code == 0, out
    frozen = json.loads((host.root / ".lanes/work/exp/frozen.json").read_text())
    assert frozen["commit"] == head
    assert frozen["profile"] == "agent" and frozen["lane"] == "research"


def test_freeze_outside_git_exits_2(host):
    host.experiment("exp")
    (host.root / ".git").rename(host.root / ".git-away")
    code, out = host.rl("freeze", "exp")
    assert code == 2
    assert "git" in out


def test_freeze_refuses_an_undeclared_target_metric(host):
    host.experiment("exp", target_metric="bleu")
    host.commit("exp")
    code, out = host.rl("freeze", "exp")
    assert code == 2
    assert "bleu" in out
