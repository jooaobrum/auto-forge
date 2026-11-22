"""Score pipeline: config in, predictions out (printed here; the inference table on the platform)."""

from __future__ import annotations

import argparse
import csv

from churn import config, model


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--env", choices=["dev", "qa", "prod"], required=True)
    cfg = config.load(parser.parse_args(argv).env)
    with open("data/valid.csv", newline="") as handle:
        rows = list(csv.DictReader(handle))
    flagged = sum(model.predict(rows, cfg["model"]["threshold"]))
    print(f"scored {len(rows)} accounts into {cfg['target']}.{cfg['monitoring']['inference_table']}: {flagged} flagged")


if __name__ == "__main__":
    main()
