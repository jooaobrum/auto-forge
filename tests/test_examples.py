import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(script: str) -> subprocess.CompletedProcess:
    env = {**os.environ, "PYTHON": sys.executable}
    return subprocess.run(["bash", str(ROOT / script)], check=False, capture_output=True, text=True, env=env)


def test_run_all():
    done = run("examples/run_all.sh")
    assert done.returncode == 0, done.stdout + done.stderr
    for profile in ("app", "pipeline", "model", "agent"):
        assert f"=== {profile}" in done.stdout
    assert done.stdout.count("delivered: .lanes/work/") == 4
    assert "all profiles delivered" in done.stdout


def test_agent_regression_is_named():
    done = run("examples/agent/run.sh")
    assert done.returncode == 0, done.stdout + done.stderr
    failing = done.stdout.split("gate cite-history full-read: fail")[0]
    assert "FAIL q02: regressed - passed the Baseline, fails in full-read" in failing
    assert "FAIL q02: guardrail input_tokens 150000 exceeds Baseline 50000 by more than 15%" in failing
