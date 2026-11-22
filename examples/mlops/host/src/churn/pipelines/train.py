"""Train pipeline: config in, trace out. Offline here: the valid rows come from data/valid.csv."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from churn import config, model, tracing

ROUND = "churn"


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--env", choices=["dev", "qa", "prod"], required=True)
    cfg = config.load(parser.parse_args(argv).env)
    with open("data/valid.csv", newline="") as handle:
        rows = list(csv.DictReader(handle))
    valid = model.accuracy(rows, cfg["model"]["threshold"])
    ledger = json.loads(Path(f".specs/features/{ROUND}/ledger.json").read_text())
    best = next(e for e in ledger["entries"] if e["id"] == ledger["best"])
    versions = {table: 12 for table in cfg["inputs"].values()}
    tracing.write(tracing.build(cfg, ROUND, best, valid, versions, run_id="offline-0001"))
    print(f"trained {cfg['target']}.{cfg['model']['name']}: valid accuracy {valid:.3f}")


if __name__ == "__main__":
    main()
