#!/usr/bin/env python3
"""Record a project evaluator run without changing how it evaluates a candidate.

The evaluator command must write one JSON object to stdout containing a top-level
"metrics" object. Additional output belongs on stderr. This helper stores the raw
output and a receipt that identifies the command and run; it never edits datasets,
labels, thresholds, or evaluator code.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", required=True, type=Path)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--phase", choices=("baseline", "dev", "validation", "holdout"), required=True)
    parser.add_argument("--candidate-revision", required=True)
    parser.add_argument("--evaluator-revision", required=True)
    parser.add_argument("--dataset-revision", required=True)
    parser.add_argument("command", nargs=argparse.REMAINDER, help="Evaluator command after --")
    args = parser.parse_args()

    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    if not command:
        parser.error("provide the evaluator command after --")

    args.run_dir.mkdir(parents=True, exist_ok=False)
    completed = subprocess.run(command, text=True, capture_output=True, check=False)
    (args.run_dir / "stderr.log").write_text(completed.stderr, encoding="utf-8")
    (args.run_dir / "raw-evaluator-output.json").write_text(completed.stdout, encoding="utf-8")

    try:
        output = json.loads(completed.stdout)
    except json.JSONDecodeError as error:
        print(f"evaluator stdout was not valid JSON: {error}", file=sys.stderr)
        return 2
    if not isinstance(output, dict) or not isinstance(output.get("metrics"), dict):
        print('evaluator JSON must contain a top-level "metrics" object', file=sys.stderr)
        return 2

    receipt = {
        "run_id": args.run_id,
        "phase": args.phase,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "candidate_revision": args.candidate_revision,
        "evaluator_revision": args.evaluator_revision,
        "dataset_revision": args.dataset_revision,
        "command": command,
        "exit_code": completed.returncode,
        "metrics": output["metrics"],
        "raw_output": "raw-evaluator-output.json",
        "stderr": "stderr.log",
    }
    (args.run_dir / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
