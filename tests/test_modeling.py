"""The modeling lane's gates, ported from ds-factory's exp-hillclimb selftest: the fixture round passes every
gate, and each mutant breaks one thing a rule exists to catch, so the gate fails with that rule's code."""

from __future__ import annotations

import json
import re
import shutil

import pytest
from conftest import ROOT, SKILLS, load

FIX = ROOT / "tests" / "fixtures" / "modeling"
SLUG = "secom"
R = f".specs/features/{SLUG}"
P, RP, V, LAB = f"{R}/plan.md", f"{R}/report.md", f"{R}/verification.md", ".specs/LAB.md"

validate_plan = load("agent-spec-modeling", "validate_plan")
validate_round = load("agent-spec-modeling", "validate_round")
validate_verification = load("agent-spec-modeling", "validate_verification")
round_report = load("agent-spec-modeling", "round_report")
deliver = load("agent-spec-modeling", "deliver")


def gate(name: str, root):
    if name == "plan":
        return validate_plan.validate(root, SLUG)[0]
    if name == "round":
        return validate_round.validate(root, SLUG)[0]
    return validate_verification.validate(root, SLUG)[0]


@pytest.fixture
def root(tmp_path):
    shutil.copytree(FIX, tmp_path / "host")
    return tmp_path / "host"


def edit(root, rel: str, old: str, new: str) -> None:
    path = root / rel
    text = path.read_text()
    assert old in text, f"anchor not found in {rel}: {old!r}"
    path.write_text(text.replace(old, new, 1))


def edit_json(root, rel: str, change) -> None:
    path = root / rel
    data = json.loads(path.read_text())
    change(data)
    path.write_text(json.dumps(data))


def ledger(change):
    return lambda root: edit_json(root, f"{R}/ledger.json", change)


def lock(change):
    return lambda root: edit_json(root, ".specs/split.lock", change)


def text(rel, old, new):
    return lambda root: edit(root, rel, old, new)


def write(rel, body):
    def mutate(root):
        (root / rel).parent.mkdir(parents=True, exist_ok=True)
        (root / rel).write_text(body)
    return mutate


def remove_last(kind: str, ext: str):
    def mutate(root):
        best = json.loads((root / R / "ledger.json").read_text())["entries"][-1]["id"]
        (root / R / kind / f"{best}.{ext}").unlink()
    return mutate


def oot_dates(root):
    first = json.loads((root / ".specs/split.lock").read_text())["windows"]["oot"][0]
    write("notebooks/peek.py", f"df = df[df.ts >= '{first}']\n")(root)


MUTANTS = [
    ("bad profile", text(P, "**Profile**: model", "**Profile**: vibes"), "plan", "P1"),
    ("bad data kind", text(P, "**Data kind**: tabular", "**Data kind**: audio"), "plan", "P1"),
    ("no question", text(P, "## Question\nDo the", "## Question\n\n## Old\nDo the"), "plan", "P2"),
    ("short question", text(P, "Do the sensor signals predict a lot's failure before the final test, with PR-AUC "
                               "above the baseline in future periods?", "Predict failure."), "plan", "P3"),
    ("target file missing", text(P, "`.specs/LAB.md`", "`.specs/nope.md`"), "plan", "P4"),
    ("target not confirmed", text(LAB, '**Confirmed**: 2026-11-18 - user: "that\'s it, failure = rejected at the '
                                       'final functional test"', "**Confirmed**: later"), "plan", "P4"),
    ("target without label rule", text(LAB, "**Label rule**:", "**Label**:"), "plan", "P4"),
    ("target without exclusions", text(LAB, "**Exclusions**:", "**Excluded**:"), "plan", "P4"),
    ("no problem section", text(LAB, "## Problem", "## Other"), "plan", "P4"),
    ("lessons not queried", text(P, "none (no lesson applies)", "will look later"), "plan", "P5"),
    ("table without catalog", text(P, "`workspace.curated.secom`", "`secom`"), "plan", "P6"),
    ("no split lock", text(P, "- Lock: `.specs/split.lock`", "- Lock: `.specs/nothing.lock`"), "plan", "P6"),
    ("lock windows overlap", lock(lambda lk: lk["windows"].update(valid=[lk["windows"]["train"][1],
                                                                         lk["windows"]["valid"][1]])), "plan", "P6"),
    ("lock without counts", lock(lambda lk: lk.pop("counts")), "plan", "P6"),
    ("lock with an empty split", lock(lambda lk: lk["counts"].update(oot=0)), "plan", "P6"),
    ("unknown metric", text(P, "- Primary: pr_auc", "- Primary: vibes"), "plan", "P7"),
    ("no min gain", text(P, "- Min gain: 0.01", "- Min gain: some"), "plan", "P7"),
    ("no period", text(P, "- Period: week", "- Period: often"), "plan", "P7"),
    ("no budget", text(P, "- Iterations: 10", "- Iterations: many"), "plan", "P8"),
    ("no max drop", text(P, "- Valid to OOT: 0.30", "- Valid to OOT: little"), "plan", "P9"),
    ("max drop above one", text(P, "- Valid to OOT: 0.30", "- Valid to OOT: 1.5"), "plan", "P9"),
    ("idea without why", text(P, "- Why: measures the evaluator's noise; the gain must be zero", "- Why: yes"),
     "plan", "P10"),
    ("idea without source", text(P, "- Source: eda\n", ""), "plan", "P10"),
    ("duplicate idea", text(P, "### H2 -", "### H1 -"), "plan", "P10"),
    ("no out of scope", text(P, "## Out of scope", "## Excluded"), "plan", "P11"),
    ("no assumptions", text(P, "## Assumptions", "## Defaults"), "plan", "P11"),
    ("approval invented", text(P, '**Approved**: 2026-11-20 - user: "approved, 10 iterations"', "**Approved**: ok"),
     "plan", "A1"),
    ("plan not approved", text(P, '**Approved**: 2026-11-20 - user: "approved, 10 iterations"\n', ""), "round", "R0"),
    ("no ledger", lambda root: (root / R / "ledger.json").unlink(), "round", "R1"),
    ("empty ledger", ledger(lambda led: led.update(entries=[])), "round", "R1"),
    ("no baseline first", ledger(lambda led: led["entries"][0].update(hypothesis="H1: everything")), "round", "R2"),
    ("budget below iterations", text(P, "- Iterations: 10", "- Iterations: 2"), "round", "R3"),
    ("idea not in backlog", text(P, "### H2 - Use sensor s000", "### H7 - Use sensor s000"), "round", "R4"),
    ("ungrounded hypothesis", ledger(lambda led: led["entries"][1].update(hypothesis="tried something")),
     "round", "R4"),
    ("experiment file missing", remove_last("experiments", "py"), "round", "R5"),
    ("error analysis missing", remove_last("error_analysis", "json"), "round", "R5"),
    ("kept inside the noise", ledger(lambda led: led["entries"][-1].update(ci=[-0.01, 0.5])), "round", "R6"),
    ("kept below min gain", ledger(lambda led: led["entries"][-1].update(delta=0.001)), "round", "R6"),
    ("best is not last kept", ledger(lambda led: led.update(best=led["entries"][0]["id"])), "round", "R6"),
    ("untracked iteration", ledger(lambda led: led["entries"][1].pop("mlflow_run_id")), "round", "R7"),
    ("report not filled", text(RP, "## What worked\n- H2", "## What worked\n<\n- H2"), "round", "R8"),
    ("report missing section", text(RP, "## Domain findings\n", "## Other\n"), "round", "R8"),
    ("leak check not reported", ledger(lambda led: led["entries"][-1]["checks"].pop("CHK-LEAK-003")),
     "round", "R9"),
    ("binary check not reported", ledger(lambda led: led["entries"][-1]["checks"].pop("CHK-LEAK-001")),
     "round", "R9"),
    ("kept despite a failed check", ledger(lambda led: led["entries"][-1]["checks"]["CHK-DUP-001"].update(ok=False)),
     "round", "R10"),
    ("infeasible without a reason", ledger(lambda led: led["entries"][1].update(status="infeasible")),
     "round", "R10"),
    ("unknown status", ledger(lambda led: led["entries"][1].update(status="maybe")), "round", "R10"),
    ("code reads the holdout", write("src/proj/train.py", "best = df[df.split == 'oot']\n"), "round", "R11"),
    ("notebook filters the holdout dates", oot_dates, "round", "R11"),
    ("experiment snapshot reads the holdout", write(f"{R}/experiments/zz.py", "x = load('out_of_time')\n"),
     "round", "R11"),
    ("no verification", lambda root: (root / V).unlink(), "verify", "V1"),
    ("bad verifier", text(V, "**Verifier**: subagent", "**Verifier**: me"), "verify", "V1"),
    ("the author verified", text(V, "**Verifier**: subagent", "**Verifier**: self-verified"), "verify", "V1"),
    ("new chat without a declared fallback", text(V, "**Verifier**: subagent", "**Verifier**: fresh-context"),
     "verify", "V1"),
    ("no head", text(V, "**HEAD**: 7441053", "**HEAD**: latest"), "verify", "V1"),
    ("judged another experiment", text(V, "**Experiment**: `", "**Experiment**: `0000"), "verify", "V2"),
    ("no OOT by period", text(V, "| 2008-10-03/2008-10-09 | 78 | 4 | 0.512 |\n| 2008-10-10/2008-10-16 | 79 | 6 | "
                                 "0.471 |\n", ""), "verify", "V3"),
    ("drop above limit", text(V, "- OOT: 0.480\n- Drop: 0.091", "- OOT: 0.200\n- Drop: 0.371"), "verify", "V4"),
    ("drop misreported", text(V, "- Drop: 0.091", "- Drop: 0.010"), "verify", "V4"),
    ("mutation survived", text(V, "- CHK-MUT-001: killed", "- CHK-MUT-001: survived"), "verify", "V5"),
    ("mutation skipped without reason", text(V, "- CHK-MUT-002: killed - CHK-LEAK-001 rejected `__future_label` "
                                                "with AUC 1.00", "- CHK-MUT-002: n/a - no"), "verify", "V5"),
    ("open finding", text(V, "## Findings\n- none", "## Findings\n- F1: threshold chosen on the OOT"),
     "verify", "V6"),
    ("verdict not pass", text(V, "## Verdict\nPASS", "## Verdict\nalmost"), "verify", "V7"),
    ("round broken under the verification", ledger(lambda led: led["entries"][1].pop("mlflow_run_id")),
     "verify", "V0"),
]


def test_fixture_passes_every_gate(root):
    for name in ("plan", "round", "verify"):
        rep = gate(name, root)
        assert rep.ok, (name, rep.errors)


@pytest.mark.parametrize("name, mutate, gate_name, code", MUTANTS, ids=[m[0] for m in MUTANTS])
def test_mutant_is_killed(root, name, mutate, gate_name, code):
    mutate(root)
    rep = gate(gate_name, root)
    assert not rep.ok, f"mutant '{name}' survived the {gate_name} gate"
    assert code in rep.codes(), (name, sorted(rep.codes()), rep.errors)


def test_offline_round_needs_no_mlflow(root):
    ledger(lambda led: [e.pop("mlflow_run_id") for e in led["entries"]])(root)
    assert "R7" in validate_round.validate(root, SLUG)[0].codes()
    assert validate_round.validate(root, SLUG, offline=True)[0].ok


def test_regression_metric_drop_is_reversed(root):
    edit(root, P, "- Primary: pr_auc", "- Primary: rmse")
    edit(root, V, "- Valid: 0.571\n- OOT: 0.480\n- Drop: 0.091", "- Valid: 0.400\n- OOT: 0.480\n- Drop: 0.080")
    assert validate_verification.validate(root, SLUG)[0].ok


def test_subagent_passes_without_a_warning(root):
    rep = validate_verification.validate(root, SLUG)[0]
    assert rep.ok and not any("[V1]" in w for w in rep.warnings)


def test_declared_fallback_passes_and_warns(root):
    edit(root, V, "**Verifier**: subagent", "**Verifier**: fresh-context\n"
         "**Fallback**: Databricks Genie Code - no subagents; a new chat with only the verify-model skill")
    rep = validate_verification.validate(root, SLUG)[0]
    assert rep.ok, rep.errors
    assert any("[V1]" in w and "Genie Code" in w for w in rep.warnings)
    validate_verification.write_gate(root, SLUG, *validate_verification.validate(root, SLUG), offline=False)
    assert "Verifier fallback: Databricks Genie Code" in (root / R / "results.md").read_text()


def test_self_verified_fails_even_with_a_fallback(root):
    edit(root, V, "**Verifier**: subagent", "**Verifier**: self-verified\n**Fallback**: Databricks Genie Code")
    rep = validate_verification.validate(root, SLUG)[0]
    assert not rep.ok and "V1" in rep.codes()


def test_cli_exit_codes_and_gate_file(root, capsys):
    assert validate_plan.main(["--root", str(root), SLUG, "--approved"]) == 0
    assert validate_round.main(["--root", str(root), SLUG]) == 0
    assert validate_verification.main(["--root", str(root), SLUG]) == 0
    out = capsys.readouterr().out
    assert "validate_verification secom: pass" in out
    gate_json = json.loads((root / R / "gate.json").read_text())
    assert gate_json["exit"] == 0 and gate_json["experiment"] == "dfdee50fa862a2c3"
    assert "| dfdee50fa862a2c3 | subagent | 7441053 | pr_auc | 0.571 | 0.48 | 0.091 | 0.3 |" in \
        (root / R / "results.md").read_text()
    edit(root, V, "## Verdict\nPASS", "## Verdict\nalmost")
    assert validate_verification.main(["--root", str(root), SLUG]) == 1
    assert "FAIL [V7]" in capsys.readouterr().out
    assert json.loads((root / R / "gate.json").read_text())["exit"] == 1


def test_round_report_keeps_the_prose(root):
    edit_json(root, f"{R}/ledger.json", lambda led: led["entries"][1].update(value=0.2))
    round_report.build(root, SLUG)
    report = (root / RP).read_text()
    assert "| 01 | rejected | H1: nothing changes | 0.2000 |" in report
    assert "- Best: it02 `dfdee50fa862a2c3` pr_auc=0.5714 (+0.4630 vs baseline)" in report
    assert "H2 (s000 back): the sensor carries the main failure signal" in report
    (root / RP).unlink()
    round_report.build(root, SLUG)
    assert "## Next round\n<ideas" in (root / RP).read_text()


def test_deliver_promote_hands_over_to_mlops(root, capsys):
    assert deliver.main(["--root", str(root), SLUG, "--decision", "promote"]) == 2
    assert "no gate has run" in capsys.readouterr().out
    edit(root, V, "## Verdict\nPASS", "## Verdict\nalmost")
    validate_verification.main(["--root", str(root), SLUG])
    assert deliver.main(["--root", str(root), SLUG, "--decision", "promote"]) == 2
    assert "did not pass" in capsys.readouterr().out
    assert deliver.main(["--root", str(root), SLUG, "--decision", "reject"]) == 0
    assert not (root / ".specs/features/secom-mlops").exists()
    edit(root, V, "## Verdict\nalmost", "## Verdict\nPASS")
    validate_verification.main(["--root", str(root), SLUG])
    assert deliver.main(["--root", str(root), SLUG, "--decision", "promote"]) == 0
    delivery = (root / R / "delivery.md").read_text()
    assert "## Decision\n\npromote" in delivery and "Do the sensor signals predict" in delivery
    assert "z-score of s000" in delivery and "validate_verification.py secom` exited 0" in delivery
    spec = (root / ".specs/features/secom-mlops/plan.md").read_text()
    assert "**Lane**: build" in spec and "**Round**: secom" in spec and "dfdee50fa862a2c3" in spec
    assert "validate_prod.py secom-mlops" in spec


def test_plan_template_validates_as_shown(root):
    reference = (SKILLS / "agent-spec-modeling" / "references" / "plan.md").read_text()
    plan = re.search(r"`````markdown\n(.*?)\n`````", reference, re.DOTALL).group(1)
    plan = re.sub(r"(?m)^\*\*Approved\*\*:.*$", '**Approved**: 2026-11-22 - user: "go"', plan)
    (root / P).write_text(plan)
    (root / ".specs/split.lock").write_text(re.search(r"```json\n(.*?)\n```", reference, re.DOTALL).group(1))
    rep = validate_plan.validate(root, SLUG, approved=True)[0]
    assert rep.ok, rep.errors
