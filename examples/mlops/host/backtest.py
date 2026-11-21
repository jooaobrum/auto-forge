"""Backtest on the recent period: champion and challenger score the same bootstrap resamples, slice by slice.

Writes the Results files promote.py reads: runs/champion/backtest.json and runs/challenger/backtest.json.
"""

from __future__ import annotations

import csv
import json
import random
import sys
from pathlib import Path

from churn import model

RESAMPLES = 40
SLICES = {"all": lambda r: True, "new": lambda r: int(r["tenure_months"]) < 6,
          "long": lambda r: int(r["tenure_months"]) >= 6}


def champion(rows: list) -> list:
    """Version 1, in production today: flags three support calls or more."""
    return [1 if int(r["support_calls"]) >= 3 else 0 for r in rows]


def challenger(rows: list) -> list:
    return model.predict(rows, 0.5)


def accuracy(predictions: list, rows: list) -> float:
    return sum(int(p == int(r["churned"])) for p, r in zip(predictions, rows)) / len(rows)


def main(out: str) -> None:
    with open("data/recent.csv", newline="") as handle:
        rows = list(csv.DictReader(handle))
    results = {"champion": [], "challenger": []}
    for name, keep in SLICES.items():
        part = [r for r in rows if keep(r)]
        for i in range(RESAMPLES):
            sample = random.Random(f"{name}-{i}").choices(part, k=len(part))
            for label, predict in (("champion", champion), ("challenger", challenger)):
                results[label].append({"case": name, "run": i, "metrics": {"accuracy": accuracy(predict(sample), sample)}})
    for label, runs in results.items():
        path = Path(out) / label / "backtest.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"runs": runs}) + "\n")


if __name__ == "__main__":
    main(sys.argv[1])
