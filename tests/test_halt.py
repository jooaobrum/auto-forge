"""`.specs/HALT`: when the file exists, every lane script exits 5 before doing anything."""

from __future__ import annotations

import shutil
import subprocess
import sys

import pytest
from conftest import ROOT, SKILLS

SCRIPTS = [
    ("agent-spec-router", "route.py", ["problem"]),
    ("agent-spec-router", "route.py", ["freeze", "x"]),
    ("agent-spec-router", "route.py", ["deliver", "x"]),
    ("agent-spec-experiment", "experiment.py", ["freeze", "x"]),
    ("agent-spec-experiment", "experiment.py", ["budget", "x", "--add", "5", "--user", "yes"]),
    ("agent-spec-pipeline", "contract.py", ["compile", "x"]),
    ("agent-spec-modeling", "validate_plan.py", ["secom"]),
    ("agent-spec-modeling", "validate_round.py", ["secom"]),
    ("agent-spec-modeling", "validate_verification.py", ["secom"]),
    ("agent-spec-modeling", "round_report.py", ["secom"]),
    ("agent-spec-modeling", "deliver.py", ["secom", "--decision", "promote"]),
    ("agent-spec-mlops", "validate_prod.py", ["x"]),
    ("agent-spec-mlops", "model_card.py", []),
    ("agent-spec-mlops", "promote.py", ["gate", "x"]),
    ("agent-spec-mlops", "promote.py", ["approve", "x", "--user", "ok"]),
    ("agent-spec-lean", "validate_plan.py", ["x"]),
    ("agent-spec-lean", "validate_checks.py", ["x"]),
    ("agent-spec-lean", "validate_verification.py", ["x"]),
    ("agent-spec-lean", "check_proofs.py", ["x"]),
    ("agent-spec-lean", "lessons.py", ["status"]),
    ("agent-spec-lean", "mutate.py", ["--spec", "-"]),
]


def snapshot(root):
    return sorted((str(p.relative_to(root)), p.read_bytes() if p.is_file() else b"")
                  for p in root.rglob("*") if ".git" not in p.parts)


@pytest.mark.parametrize("skill, script, args", SCRIPTS, ids=[f"{s[1]} {' '.join(s[2][:1])}" for s in SCRIPTS])
def test_halt_stops_every_lane_script(tmp_path, skill, script, args):
    root = tmp_path / "host"
    shutil.copytree(ROOT / "tests" / "fixtures" / "modeling", root)
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    (root / ".specs" / "HALT").write_text("budget review on Monday\n")
    before = snapshot(root)
    done = subprocess.run([sys.executable, str(SKILLS / skill / "scripts" / script), "--root", str(root), *args],
                          capture_output=True, text=True, check=False, cwd=root, input="[]")
    assert done.returncode == 5, done.stdout + done.stderr
    assert "HALT .specs/HALT exists (budget review on Monday) - nothing ran" in done.stdout
    assert snapshot(root) == before


def test_without_halt_the_scripts_run(tmp_path):
    root = tmp_path / "host"
    shutil.copytree(ROOT / "tests" / "fixtures" / "modeling", root)
    done = subprocess.run([sys.executable, str(SKILLS / "agent-spec-modeling" / "scripts" / "validate_plan.py"),
                           "--root", str(root), "secom"], capture_output=True, text=True, check=False)
    assert done.returncode == 0, done.stdout
