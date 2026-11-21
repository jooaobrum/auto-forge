"""A stdlib threshold classifier, evaluated per holdout slice; k is the number of seeds."""
import argparse
import json
import random

SLICES = {"short": 0.40, "long": 0.47, "rare": 0.50}  # where the true label flips, per slice


def accuracy(threshold: float, boundary: float, seed: str) -> float:
    rng = random.Random(seed)
    xs = [rng.random() for _ in range(400)]
    return round(sum((x > threshold) == (x > boundary) for x in xs) / len(xs), 4)


parser = argparse.ArgumentParser()
parser.add_argument("--selection")
parser.add_argument("--all", type=int, help="run every slice with this many seeds")
parser.add_argument("--out", required=True)
args = parser.parse_args()
threshold = json.load(open("model/config.json"))["threshold"]
if args.all:
    plan = {name: args.all for name in SLICES}
else:
    selection = json.load(open(args.selection))
    plan = {case: spec["k"] for case, spec in selection["cases"].items() if spec["k"] > 0}
runs = [
    {"case": case, "run": seed, "touched": ["param:threshold"],
     "metrics": {"accuracy": accuracy(threshold, SLICES[case], f"{case}-{seed}"), "train_seconds": 1.0}}
    for case, k in plan.items() for seed in range(1, k + 1)
]
json.dump({"runs": runs}, open(args.out, "w"), indent=2)
