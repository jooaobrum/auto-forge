"""model_card.py - write MODEL_CARD.md from the evidence: config/project.yml and .specs/prod/trace.json.

Usage: python3 <skill-dir>/scripts/model_card.py [--root <repo>]

Fills Model, Traceability, Data, Metrics and Monitoring; keeps the Intended use and Limitations already written
(they need a person). Run it again after every retrain. Exit: 0 ok, 2 invalid input. Standard library only.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import yaml_lite

KEEP = {
    "Intended use": "<who uses it, for which decision, at what moment; what is not an intended use>",
    "Limitations": "<where the model errs most (the Verification's error analysis), weak periods and segments, "
                   "data it depends on>",
}


def kept(path: Path) -> dict:
    if not path.exists():
        return {}
    text, out = path.read_text(encoding="utf-8"), {}
    for name in KEEP:
        match = re.search(rf"^## {re.escape(name)}\n(.*?)(?=^## |\Z)", text, re.DOTALL | re.MULTILINE)
        if match and match.group(1).strip() and not match.group(1).strip().startswith("<"):
            out[name] = match.group(1).strip()
    return out


def build(root: Path) -> Path:
    cfg = yaml_lite.load((root / "config" / "project.yml").read_text(encoding="utf-8")) or {}
    trace = json.loads((root / ".specs" / "prod" / "trace.json").read_text(encoding="utf-8"))
    card = root / "MODEL_CARD.md"
    written = kept(card)
    model, experiment, repro = trace["model"], trace["experiment"], trace["reproducibility"]
    metrics, monitoring, settings = trace.get("metrics", {}), cfg.get("monitoring") or {}, cfg.get("model") or {}
    drift = monitoring.get("drift") or {}
    lines = [
        f"# Model card - {model['name']}", "",
        "## Model",
        (f"- `{model['name']}` version {model['version']} (alias `{model.get('alias', '-')}`), task "
        f"{settings.get('task', '-')}, threshold {settings.get('threshold', '-')}"),
        f"- Environment: `{trace['config_env']}`", "",
        "## Traceability",
        f"- Git commit: `{trace['git_commit']}`",
        f"- Run: `{trace.get('mlflow_run_id', '-')}`",
        (f"- Source experiment: round `{experiment['round']}`, experiment `{experiment['id']}` "
        f"(`.specs/features/{experiment['round']}/verification.md`)"),
        (f"- Reproducibility: production valid {repro['metric']} {repro['prod_valid_metric']} vs experiment "
        f"{experiment['valid_metric']} (tolerance {repro['tolerance']}), seed {repro['seed']}, "
        f"{repro.get('lockfile', 'uv.lock')} sha256 `{str(repro['lockfile_sha256'])[:12]}...`"), "",
        "## Data",
        *[f"- `{d['table']}` v{d['version']}" for d in trace["data"]], "",
        "## Metrics",
        f"- Valid {repro['metric']}: {metrics.get('valid', repro['prod_valid_metric'])}",
        f"- OOT {repro['metric']}: {metrics.get('oot', '-')} (from the round's Verification)", "",
        "## Intended use", written.get("Intended use", KEEP["Intended use"]), "",
        "## Limitations", written.get("Limitations", KEEP["Limitations"]), "",
        "## Monitoring",
        (f"- Inference table: `{monitoring.get('inference_table', '-')}`; metrics: "
        f"{', '.join(map(str, monitoring.get('metrics') or []))}"),
        (f"- Drift vs {drift.get('baseline', '-')}, threshold {drift.get('threshold', '-')}; schedule "
        f"{monitoring.get('schedule', '-')}; alert `{monitoring.get('alert', '-')}`"), "",
    ]
    card.write_text("\n".join(lines), encoding="utf-8")
    return card


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="model_card.py", description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--root", default=".")
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()
    try:
        print(f"wrote {build(root).relative_to(root)}")
        return 0
    except (OSError, KeyError, TypeError, ValueError) as exc:
        print(f"ERROR model_card.py needs config/project.yml and a complete .specs/prod/trace.json - {exc!r}")
        return 2


if __name__ == "__main__":
    sys.exit(main())
