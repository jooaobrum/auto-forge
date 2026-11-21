import os
import subprocess
import sys

from conftest import ROOT


def run(script: str) -> subprocess.CompletedProcess:
    env = {**os.environ, "PYTHON": sys.executable}
    return subprocess.run(["bash", str(ROOT / script)], capture_output=True, text=True, env=env, check=False)


def test_run_all():
    done = run("examples/run_all.sh")
    assert done.returncode == 0, done.stdout + done.stderr
    for profile in ("app", "pipeline", "model", "agent", "modeling", "mlops"):
        assert f"=== {profile}" in done.stdout
    assert done.stdout.count("delivered: .specs/features/") == 6
    for path in (ROOT / "examples").rglob("*"):
        assert path.name != "lanes.json", path
        if path.suffix == ".sh":
            assert " rl " not in path.read_text() and "-m lanes" not in path.read_text(), path


def test_agent_regression_is_named():
    done = run("examples/agent/run.sh")
    assert done.returncode == 0, done.stdout + done.stderr
    failing = done.stdout.split("gate cite-history full-read: fail")[0]
    assert "FAIL q02: regressed - passed the Baseline, fails in full-read" in failing
    assert "FAIL q02: guardrail input_tokens 150000 exceeds Baseline 50000 by more than 15%" in failing


def test_modeling_gates_catch_the_oot_shortcut():
    done = run("examples/modeling/run.sh")
    assert done.returncode == 0, done.stdout + done.stderr
    assert "FAIL [R11] the round's code references the OOT period" in done.stdout
    assert "validate_verification secom: pass" in done.stdout


def test_mlops_gate_names_what_production_lacks():
    done = run("examples/mlops/run.sh")
    assert done.returncode == 0, done.stdout + done.stderr
    assert "FAIL [D7] .specs/prod/trace.json not found" in done.stdout
    assert "validate_prod churn-mlops: pass" in done.stdout
