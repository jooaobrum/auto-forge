"""validate_prod.py - is the production standard implemented? (references/standard.md)

Usage: python3 <skill-dir>/scripts/validate_prod.py [--root <repo>] <slug>

Validates the pattern and the stack, never writes code. <slug> is the mlops piece of work; its JUnit results
are read from .specs/features/<slug>/runs/main/*.xml, and gate.json and results.md are written there.
  D1  config/project.yml: environments dev, qa and prod, each writing to its own catalog.schema
  D2  no write target or input table hardcoded in src/ (they come from the config)
  D3  every pipeline in the config, at least train and score, exists in src/<pkg>/pipelines/ with a main()
      that loads the config
  D4  every module of src/<pkg>/ has tests/test_<module>.py, and the tests pass (JUnit)
  D5  (platform: databricks) databricks.yml targets dev, qa and prod; jobs in resources/*.yml pass --env
  D6  monitoring declared: inference table, metrics, drift baseline and threshold, schedule, alert
  D7  .specs/prod/trace.json names a verified round and its best experiment, and the production valid metric
      matches the experiment's within the tolerance
  D8  MODEL_CARD.md has its sections and carries the trace: model and version, commit, run, round, every table
      read with its version
  D9  dependencies locked: the lock file's sha256 and the seed recorded in the trace
  D10 MLflow standard: registry (databricks-uc on Databricks), required tags, model named under the
      environment's catalog.schema, an integer version, a commit sha
Without `platform: databricks` in the config, D5 is skipped with a warning and D10 accepts any registry.
Exit: 0 pass, 1 fail. Standard library only (PyYAML used when installed).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import yaml_lite

ENVS = ("dev", "qa", "prod")
BASE_TAGS = {"git_commit", "config_env", "round", "experiment_id", "training_tables"}
CARD_SECTIONS = ["Model", "Traceability", "Data", "Metrics", "Intended use", "Limitations", "Monitoring"]
SHA = re.compile(r"[0-9a-f]{7,40}")
TRACE = Path(".specs") / "prod" / "trace.json"
PASS, FAIL = 0, 1


class Report:
    def __init__(self, name: str):
        self.name = name
        self.errors: list = []
        self.warnings: list = []

    def fail(self, code: str, msg: str) -> None:
        self.errors.append(f"[{code}] {msg}")

    def warn(self, code: str, msg: str) -> None:
        self.warnings.append(f"[{code}] {msg}")

    def codes(self) -> set:
        return {e[1:e.index("]")] for e in self.errors}

    @property
    def ok(self) -> bool:
        return not self.errors


def sections(markdown: str) -> dict:
    out, current = {}, None
    for line in markdown.splitlines():
        match = re.match(r"^##\s+(.+?)\s*$", line)
        if match:
            current = match.group(1).strip().lower()
            out[current] = []
        elif current is not None:
            out[current].append(line)
    return {k: "\n".join(v).strip() for k, v in out.items()}


def load_config(root: Path) -> dict:
    return yaml_lite.load((root / "config" / "project.yml").read_text(encoding="utf-8")) or {}


def targets_of(cfg: dict) -> dict:
    envs = cfg.get("environments") or {}
    return {e: f"{envs[e]['catalog']}.{envs[e]['schema']}" for e in ENVS
            if isinstance(envs.get(e), dict) and envs[e].get("catalog") and envs[e].get("schema")}


def _junit(paths: list[Path]) -> tuple[int, list[str]]:
    ran, failed = 0, []
    for path in paths:
        try:
            for case in ET.parse(path).getroot().iter("testcase"):
                if case.find("skipped") is not None:
                    continue
                ran += 1
                if case.find("failure") is not None or case.find("error") is not None:
                    failed.append(".".join(p for p in (case.get("classname"), case.get("name")) if p))
        except ET.ParseError as exc:
            failed.append(f"{path.name}: malformed JUnit ({exc})")
    return ran, failed


def _config_rules(rep: Report, root: Path, cfg: dict, slug: str) -> tuple[dict, Path | None]:
    targets = targets_of(cfg)
    for env in ENVS:
        if env not in targets:
            rep.fail("D1", f"environments.{env} needs catalog and schema (where this environment writes)")
    if len(set(targets.values())) < len(targets):
        rep.fail("D1", f"environments must write to distinct catalog.schema: {targets}")

    packages = sorted(p for p in (root / "src").glob("*") if (p / "__init__.py").is_file())
    if not packages:
        rep.fail("D3", "no package under src/ (src/<pkg>/__init__.py)")
    package = packages[0] if packages else None

    literals = list(targets.values()) + [str(v) for v in (cfg.get("inputs") or {}).values()]
    for path in sorted((root / "src").rglob("*.py")):
        text = path.read_text(encoding="utf-8")
        for literal in literals:
            if literal and re.search(rf"(?<![\w.]){re.escape(literal)}(?!\w)", text):
                rep.fail("D2", f"{path.relative_to(root)} hardcodes '{literal}'; read it from the config")

    pipelines = cfg.get("pipelines") or []
    if not {"train", "score"} <= set(pipelines):
        rep.fail("D3", "config pipelines must include at least train and score")
    for name in pipelines:
        path = (package or root / "src" / "<pkg>") / "pipelines" / f"{name}.py"
        if not path.exists():
            rep.fail("D3", f"pipeline '{name}' declared but {path.relative_to(root)} is missing")
            continue
        text = path.read_text(encoding="utf-8")
        if not re.search(r"^def main\(", text, re.MULTILINE):
            rep.fail("D3", f"{path.relative_to(root)} needs a def main(...) entry point")
        if not re.search(r"\bconfig\b", text):
            rep.fail("D3", f"{path.relative_to(root)} must load the config (no settings inline)")

    if package:
        for module in sorted(package.glob("*.py")):
            if module.stem != "__init__" and not (root / "tests" / f"test_{module.stem}.py").exists():
                rep.fail("D4", f"src module '{module.stem}' has no tests/test_{module.stem}.py")
    reports = sorted((root / ".specs" / "features" / slug / "runs" / "main").glob("*.xml"))
    ran, failed = _junit(reports)
    if not reports:
        rep.fail("D4", f"no test results: run the tests with --junitxml .specs/features/{slug}/runs/main/tests.xml")
    elif ran == 0:
        rep.fail("D4", "no test ran")
    for name in failed:
        rep.fail("D4", f"test failed: {name}")

    if str(cfg.get("platform", "")).lower() == "databricks":
        bundle = root / "databricks.yml"
        if not bundle.exists():
            rep.fail("D5", "databricks.yml not found")
        else:
            match = re.search(r"^targets:\s*\n((?:[ \t]+.*\n?|\s*\n)*)", bundle.read_text(encoding="utf-8"),
                              re.MULTILINE)
            names = set(re.findall(r"^  ([A-Za-z0-9_-]+):", match.group(1), re.MULTILINE)) if match else set()
            missing = [e for e in ENVS if e not in names]
            if missing:
                rep.fail("D5", f"databricks.yml targets missing: {missing}")
        jobs = "".join(p.read_text(encoding="utf-8") for p in sorted((root / "resources").glob("*.yml")))
        if not jobs:
            rep.fail("D5", "no jobs in resources/*.yml")
        elif "--env" not in jobs:
            rep.fail("D5", "jobs in resources/ must pass --env to the pipelines")
    else:
        rep.warn("D5", "skipped: the config declares no platform (`platform: databricks` turns on the bundle rules)")

    monitoring = cfg.get("monitoring") or {}
    for key in ("inference_table", "metrics", "drift", "schedule", "alert"):
        if not monitoring.get(key):
            rep.fail("D6", f"monitoring.{key} missing")
    drift = monitoring.get("drift") or {}
    if drift and not (isinstance(drift, dict) and drift.get("baseline")
                      and isinstance(drift.get("threshold"), (int, float))):
        rep.fail("D6", "monitoring.drift needs a baseline and a numeric threshold")

    mlflow = cfg.get("mlflow")
    databricks = str(cfg.get("platform", "")).lower() == "databricks"
    if mlflow or databricks:
        mlflow = mlflow or {}
        if databricks and mlflow.get("registry") != "databricks-uc":
            rep.fail("D10", "mlflow.registry must be databricks-uc on Databricks")
        elif not mlflow.get("registry"):
            rep.fail("D10", "mlflow.registry missing")
        if not mlflow.get("experiment"):
            rep.fail("D10", "mlflow.experiment missing")
        missing_tags = BASE_TAGS - set(mlflow.get("required_tags") or [])
        if missing_tags:
            rep.fail("D10", f"mlflow.required_tags missing {sorted(missing_tags)}")
    else:
        rep.warn("D10", "no mlflow section: registry and tags not checked")
    return targets, package


def _trace_rules(rep: Report, root: Path, cfg: dict, targets: dict) -> None:
    path = root / TRACE
    if not path.exists():
        rep.fail("D7", ".specs/prod/trace.json not found (the train pipeline writes it)")
        return
    try:
        trace = json.loads(path.read_text(encoding="utf-8"))
    except ValueError as exc:
        rep.fail("D7", f"trace.json does not parse: {exc}")
        return

    experiment = trace.get("experiment") or {}
    round_slug = str(experiment.get("round", ""))
    folder = root / ".specs" / "features" / round_slug
    verification = folder / "verification.md"
    if (not round_slug or not verification.exists()
            or sections(verification.read_text(encoding="utf-8")).get("verdict", "").split()[:1] != ["PASS"]):
        rep.fail("D7", f"experiment.round '{round_slug}' has no verification.md with Verdict PASS")
    ledger = folder / "ledger.json"
    if round_slug and (not ledger.exists() or json.loads(ledger.read_text(encoding="utf-8")).get("best")
                       != experiment.get("id")):
        rep.fail("D7", f"experiment.id is not the best of {round_slug}'s ledger")
    repro = trace.get("reproducibility") or {}
    try:
        diff = abs(float(repro["prod_valid_metric"]) - float(experiment["valid_metric"]))
        tolerance = float(repro["tolerance"])
        if tolerance <= 0:
            rep.fail("D7", "reproducibility.tolerance must be > 0")
        elif diff > tolerance + 1e-12:
            rep.fail("D7", f"production valid {repro['prod_valid_metric']} vs experiment {experiment['valid_metric']}: "
                           f"diff {diff:.4f} above tolerance {tolerance:g}; the pipeline does not reproduce the "
                           "experiment")
    except (KeyError, TypeError, ValueError):
        rep.fail("D7", "trace.json needs experiment.valid_metric and reproducibility.prod_valid_metric and tolerance")

    lock_name = str(repro.get("lockfile", "uv.lock"))
    lock = root / lock_name
    if not lock.exists():
        rep.fail("D9", f"{lock_name} not found; lock the dependencies")
    elif hashlib.sha256(lock.read_bytes()).hexdigest() != repro.get("lockfile_sha256"):
        rep.fail("D9", f"reproducibility.lockfile_sha256 does not match {lock_name}; retrain with the committed lock")
    if repro.get("seed") is None:
        rep.fail("D9", "reproducibility.seed missing")

    if not SHA.fullmatch(str(trace.get("git_commit", ""))):
        rep.fail("D10", "trace.json git_commit must be a commit sha")
    model = trace.get("model") or {}
    env = trace.get("config_env")
    if env not in targets:
        rep.fail("D10", f"trace.json config_env must be one of {list(targets)}")
    elif model.get("name") != f"{targets[env]}.{(cfg.get('model') or {}).get('name')}":
        rep.fail("D10", f"model name must be {targets[env]}.<model.name from the config>, got {model.get('name')}")
    if not isinstance(model.get("version"), int) or isinstance(model.get("version"), bool):
        rep.fail("D10", "trace.json model.version must be the registry's model version (an integer)")
    data = trace.get("data") or []
    if not data or any("table" not in d or "version" not in d for d in data):
        rep.fail("D8", "trace.json data must list every table read with its version")

    card = root / "MODEL_CARD.md"
    if not card.exists():
        rep.fail("D8", "MODEL_CARD.md not found (generate it with model_card.py, then review)")
        return
    text = card.read_text(encoding="utf-8")
    found = sections(text)
    for name in CARD_SECTIONS:
        body = found.get(name.lower(), "")
        if len(body) < 10 or body.startswith("<"):
            rep.fail("D8", f"MODEL_CARD.md: '## {name}' missing or not filled")
    needles = [str(model.get("name")), f"version {model.get('version')}", str(trace.get("git_commit")),
               str(trace.get("mlflow_run_id")), round_slug]
    needles += [str(d.get("table")) for d in data] + [f"v{d.get('version')}" for d in data]
    for needle in needles:
        if needle and needle != "None" and needle not in text:
            rep.fail("D8", f"MODEL_CARD.md does not carry '{needle}' from trace.json (regenerate it)")


def validate(root: Path, slug: str) -> Report:
    rep = Report(f"validate_prod {slug}")
    if not (root / "config" / "project.yml").exists():
        rep.fail("D1", "config/project.yml not found (the single source of truth, references/standard.md)")
        return rep
    try:
        cfg = load_config(root)
    except ValueError as exc:
        rep.fail("D1", f"config/project.yml does not parse: {exc}")
        return rep
    targets, _ = _config_rules(rep, root, cfg, slug)
    _trace_rules(rep, root, cfg, targets)
    return rep


def write_gate(root: Path, slug: str, rep: Report) -> None:
    folder = root / ".specs" / "features" / slug
    folder.mkdir(parents=True, exist_ok=True)
    command = f"validate_prod.py {slug}"
    failed, skipped = rep.codes(), {w[1:w.index("]")] for w in rep.warnings if "] skipped" in w}
    rows = []
    for n in range(1, 11):
        rule = f"D{n}"
        rows.append(f"| {rule} | {'fail' if rule in failed else 'skipped' if rule in skipped else 'pass'} |")
    lines = [f"# Results - {slug}", "", f"Gate: `{command}` - **{'pass' if rep.ok else 'fail'}**", "",
             "| Rule | Result |", "| --- | --- |", *rows]
    if rep.errors:
        lines += ["", "## Findings", ""] + [f"- {e}" for e in rep.errors]
    (folder / "results.md").write_text("\n".join(lines) + "\n")
    (folder / "gate.json").write_text(json.dumps({"exit": PASS if rep.ok else FAIL, "command": command,
                                                  "findings": rep.errors}, indent=2) + "\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="validate_prod.py", description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--root", default=".")
    parser.add_argument("slug")
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()
    rep = validate(root, args.slug)
    write_gate(root, args.slug, rep)
    for line in rep.warnings:
        print(f"WARN {line}")
    for line in rep.errors:
        print(f"FAIL {line}")
    count = len(rep.errors)
    print(f"validate_prod {args.slug}: " + ("pass" if rep.ok else f"fail ({count} problem{'' if count == 1 else 's'})"))
    return PASS if rep.ok else FAIL


if __name__ == "__main__":
    sys.exit(main())
