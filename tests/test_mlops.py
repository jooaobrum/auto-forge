"""The mlops lane's production gate, ported from ds-factory's deploy-industrialize selftest: the fixture project
passes, and each mutant breaks one rule, so the gate fails with that rule's code."""

from __future__ import annotations

import json
import shutil

import pytest
import yaml
from conftest import ROOT, load

FIX = ROOT / "tests" / "fixtures" / "mlops"
SLUG = "secom-mlops"
CFG, TRACE, CARD = "config/project.yml", ".specs/prod/trace.json", "MODEL_CARD.md"
JUNIT = f".specs/features/{SLUG}/runs/main/tests.xml"

validate_prod = load("agent-spec-mlops", "validate_prod")
model_card = load("agent-spec-mlops", "model_card")
yaml_lite = load("agent-spec-mlops", "yaml_lite")


@pytest.fixture
def root(tmp_path):
    shutil.copytree(FIX, tmp_path / "host")
    return tmp_path / "host"


def text(rel, old, new):
    def mutate(root):
        path = root / rel
        body = path.read_text()
        assert old in body, f"anchor not found in {rel}: {old!r}"
        path.write_text(body.replace(old, new, 1))
    return mutate


def trace(change):
    def mutate(root):
        data = json.loads((root / TRACE).read_text())
        change(data)
        (root / TRACE).write_text(json.dumps(data))
    return mutate


def write(rel, body):
    def mutate(root):
        (root / rel).parent.mkdir(parents=True, exist_ok=True)
        (root / rel).write_text(body)
    return mutate


def remove(rel):
    return lambda root: (root / rel).unlink()


MUTANTS = [
    ("no config", remove(CFG), "D1"),
    ("env without schema", text(CFG, "qa:   {catalog: workspace, schema: poc_secom_qa}", "qa:   {catalog: workspace}"),
     "D1"),
    ("prod writes to dev", text(CFG, "prod: {catalog: workspace, schema: poc_secom}",
                                "prod: {catalog: workspace, schema: poc_secom_dev}"), "D1"),
    ("hardcoded write target", write("src/poc_secom/io.py", "OUT = 'workspace.poc_secom_dev'\n"), "D2"),
    ("hardcoded input table", text("src/poc_secom/features.py", "def build(",
                                   "SRC = 'workspace.curated.secom'\n\ndef build("), "D2"),
    ("no package", lambda root: shutil.rmtree(root / "src"), "D3"),
    ("pipeline missing", remove("src/poc_secom/pipelines/score.py"), "D3"),
    ("pipeline without main", text("src/poc_secom/pipelines/train.py", "def main(", "def run("), "D3"),
    ("pipeline ignores config", write("src/poc_secom/pipelines/monitor.py",
                                      "def main(argv=None):\n    table = 'inference'\n"), "D3"),
    ("no train pipeline declared", text(CFG, "pipelines: [features, train, score, monitor]",
                                        "pipelines: [features, score]"), "D3"),
    ("module without tests", remove("tests/test_model.py"), "D4"),
    ("no test results", remove(JUNIT), "D4"),
    ("a test failed", text(JUNIT, 'name="test_placeholder"/></testsuite>',
                           'name="test_placeholder"><failure/></testcase></testsuite>'), "D4"),
    ("every test skipped", write(JUNIT, '<testsuite><testcase name="x"><skipped/></testcase></testsuite>'), "D4"),
    ("no prod target", text("databricks.yml", "  prod:\n", "  staging:\n"), "D5"),
    ("no bundle", remove("databricks.yml"), "D5"),
    ("jobs without env", text("resources/jobs.yml", '["--env", "${bundle.target}"]', '["--foo"]'), "D5"),
    ("no monitoring alert", text(CFG, "  alert: ds-alerts\n", ""), "D6"),
    ("drift without threshold", text(CFG, "drift: {baseline: training, threshold: 0.2}", "drift: {baseline: training}"),
     "D6"),
    ("no trace", remove(TRACE), "D7"),
    ("round not verified", text(".specs/features/secom/verification.md", "PASS", "FAIL"), "D7"),
    ("not the best experiment", trace(lambda t: t["experiment"].update(id="0000000000000000")), "D7"),
    ("does not reproduce", trace(lambda t: t["reproducibility"].update(prod_valid_metric=0.50)), "D7"),
    ("zero tolerance", trace(lambda t: t["reproducibility"].update(tolerance=0)), "D7"),
    ("no lockfile", remove("uv.lock"), "D9"),
    ("lockfile changed", text("uv.lock", "# fixture lock", "# other lock"), "D9"),
    ("no seed", trace(lambda t: t["reproducibility"].pop("seed")), "D9"),
    ("not UC registry", text(CFG, "registry: databricks-uc", "registry: workspace"), "D10"),
    ("missing required tag", text(CFG, "required_tags: [git_commit, config_env, round, experiment_id, training_tables]",
                                  "required_tags: [round]"), "D10"),
    ("no commit sha", trace(lambda t: t.update(git_commit="latest")), "D10"),
    ("model outside env schema", trace(lambda t: t["model"].update(name="workspace.poc_secom.secom_fail")), "D10"),
    ("model version not integer", trace(lambda t: t["model"].update(version="latest")), "D10"),
    ("table without version", trace(lambda t: t["data"][0].pop("version")), "D8"),
    ("no model card", remove(CARD), "D8"),
    ("card without limitations", text(CARD, "## Limitations\n", "## Notes\n"), "D8"),
    ("card is stale", trace(lambda t: t["model"].update(version=4)), "D8"),
]


def test_fixture_passes(root):
    rep = validate_prod.validate(root, SLUG)
    assert rep.ok, rep.errors
    assert not rep.warnings


@pytest.mark.parametrize("name, mutate, code", MUTANTS, ids=[m[0] for m in MUTANTS])
def test_mutant_is_killed(root, name, mutate, code):
    mutate(root)
    rep = validate_prod.validate(root, SLUG)
    assert not rep.ok, f"mutant '{name}' survived"
    assert code in rep.codes(), (name, sorted(rep.codes()), rep.errors)


def test_without_a_platform_the_databricks_rules_step_aside(root):
    text(CFG, "platform: databricks\n", "")(root)
    remove("databricks.yml")(root)
    text(CFG, "registry: databricks-uc", "registry: mlflow-server")(root)
    rep = validate_prod.validate(root, SLUG)
    assert rep.ok, rep.errors
    assert any(w.startswith("[D5] skipped") for w in rep.warnings)
    text(CFG, "required_tags: [git_commit, config_env, round, experiment_id, training_tables]",
         "required_tags: [round]")(root)
    assert "D10" in validate_prod.validate(root, SLUG).codes()


def test_without_mlflow_the_registry_is_not_checked(root):
    config = yaml.safe_load((root / CFG).read_text())
    config.pop("platform")
    config.pop("mlflow")
    (root / CFG).write_text(yaml.safe_dump(config))
    rep = validate_prod.validate(root, SLUG)
    assert rep.ok, rep.errors
    assert any(w.startswith("[D10]") for w in rep.warnings)


def test_another_lock_file(root):
    (root / "uv.lock").rename(root / "poetry.lock")
    assert "D9" in validate_prod.validate(root, SLUG).codes()
    trace(lambda t: t["reproducibility"].update(lockfile="poetry.lock"))(root)
    model_card.build(root)
    assert validate_prod.validate(root, SLUG).ok


def test_cli_writes_the_gate(root, capsys):
    assert validate_prod.main(["--root", str(root), SLUG]) == 0
    assert "validate_prod secom-mlops: pass" in capsys.readouterr().out
    gate = json.loads((root / f".specs/features/{SLUG}/gate.json").read_text())
    assert gate == {"exit": 0, "command": "validate_prod.py secom-mlops", "findings": []}
    assert "| D5 | pass |" in (root / f".specs/features/{SLUG}/results.md").read_text()
    remove(CARD)(root)
    assert validate_prod.main(["--root", str(root), SLUG]) == 1
    assert "FAIL [D8] MODEL_CARD.md not found" in capsys.readouterr().out
    assert "| D8 | fail |" in (root / f".specs/features/{SLUG}/results.md").read_text()


def test_model_card_keeps_what_a_person_wrote(root, capsys):
    trace(lambda t: t["model"].update(version=4))(root)
    assert "D8" in validate_prod.validate(root, SLUG).codes()
    assert model_card.main(["--root", str(root)]) == 0
    card = (root / CARD).read_text()
    assert "version 4" in card and "Process engineering, before the final test" in card
    assert validate_prod.validate(root, SLUG).ok
    remove(CARD)(root)
    model_card.build(root)
    assert "## Limitations\n<where the model errs most" in (root / CARD).read_text()
    assert "D8" in validate_prod.validate(root, SLUG).codes()
    remove(TRACE)(root)
    assert model_card.main(["--root", str(root)]) == 2


def test_stdlib_yaml_reader_agrees_with_pyyaml():
    raw = (FIX / CFG).read_text()
    assert yaml_lite._Reader(raw).parse() == yaml.safe_load(raw)
