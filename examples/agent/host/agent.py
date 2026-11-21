"""A scripted stand-in for the agent: its behavior on each question follows the history prompt."""
import argparse
import json

CASES = {"q01": "history", "q02": "history", "q03": "equipment"}


def answer(case: str, prompt: str) -> dict:
    full_read = "in full" in prompt
    if CASES[case] == "equipment":
        return {"cited_recall": 1.0, "correctness": 1, "input_tokens": 30000}
    tokens = 50000 + (100000 if full_read else 0)
    if case == "q01":  # many records: cites only some unless told to cite ids
        return {"cited_recall": 1.0 if "cite the id" in prompt else 0.33, "correctness": 1, "input_tokens": tokens}
    return {"cited_recall": 1.0, "correctness": 0 if full_read else 1, "input_tokens": tokens}  # q02 overflows


parser = argparse.ArgumentParser()
parser.add_argument("--selection")
parser.add_argument("--tier")
parser.add_argument("--all", type=int)
parser.add_argument("--out", required=True)
args = parser.parse_args()
prompt = open("prompts/history.md").read().lower()
if args.all:
    plan = {case: args.all for case in CASES}
else:
    selection = json.load(open(args.selection))
    plan = {}
    for case, spec in selection["cases"].items():
        if args.tier:
            if spec["tier"] == args.tier:
                plan[case] = selection["k_stable"] if args.tier == "stable" else spec["k"]
        elif spec["k"] > 0:
            plan[case] = spec["k"]
touched = {"history": ["skill:history"], "equipment": ["tool:resolve_equipment"]}
runs = [{"case": case, "run": n, "touched": touched[CASES[case]], "trace": f"local-{case}-{n}",
         "metrics": answer(case, prompt)} for case, k in plan.items() for n in range(1, k + 1)]
json.dump({"runs": runs}, open(args.out, "w"), indent=2)
