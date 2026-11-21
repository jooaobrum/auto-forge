"""`python -m lanes` / `rl`: every command reads and writes files; none runs the work itself."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from lanes import baseline, brief, budget, contract, deliver, freeze, gate, selection
from lanes.work import BUDGET_SPENT, GATE_FAIL, INVALID, OK, VARIANT_CAP, LanesError, Work


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="rl", description=__doc__)
    parser.add_argument("--root", default=".", help="host repo root (default: current directory)")
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("brief", "freeze"):
        sub.add_parser(name).add_argument("slug")
    p = sub.add_parser("baseline")
    p.add_argument("slug")
    p.add_argument("--from", dest="source", required=True, help="a Results file of the current agent or model")
    p = sub.add_parser("select")
    p.add_argument("slug")
    p.add_argument("--variant", required=True)
    p = sub.add_parser("contract")
    p.add_argument("slug")
    p.add_argument("contract")
    p.add_argument("--golden")
    p.add_argument("--dialect", default="spark", choices=contract.DIALECTS)
    p = sub.add_parser("gate")
    p.add_argument("slug")
    p.add_argument("--variant", default="main")
    p.add_argument("--confirm", action="store_true")
    p.add_argument("--regression-only", action="store_true")
    p = sub.add_parser("budget")
    p.add_argument("slug")
    p.add_argument("--add", type=int)
    p.add_argument("--user")
    p = sub.add_parser("deliver")
    p.add_argument("slug")
    p.add_argument("--decision", choices=deliver.DECISIONS)
    return parser


def _run(args) -> int:
    root = Path(args.root).resolve()
    work = Work(root, args.slug)
    if args.command == "brief":
        code, errors, warnings = brief.check(work)
        for line in errors:
            print(f"ERROR {line}")
        for line in warnings:
            print(f"WARN  {line}")
        print(f"brief {work.slug}: {'ready' if code == OK else 'not ready'}")
        return code
    if args.command == "freeze":
        frozen = freeze.freeze(work)
        print(f"frozen {work.slug} at {frozen['commit'][:12]} ({frozen['profile']}, {frozen['lane']} lane)")
        return OK
    if args.command == "baseline":
        cases = baseline.record(work, (root / args.source) if not Path(args.source).is_absolute() else Path(args.source))
        print(f"baseline recorded for {len(cases)} cases: {', '.join(cases)}")
        return OK
    if args.command == "select":
        spent, used, total = budget.is_spent(work)
        if spent:
            print(budget.spent_message(used, total))
            return BUDGET_SPENT
        if selection.cap_reached(work, args.variant):
            print(f"variant cap reached: {', '.join(selection.variants(work))} - deliver with a decision")
            return VARIANT_CAP
        chosen = selection.select(work, args.variant)
        print(f"{'case':<24} {'tier':<9} k")
        for case, spec in chosen["cases"].items():
            print(f"{case:<24} {spec['tier']:<9} {spec['k']}")
        if chosen["stale"]:
            print(f"stale or missing Baseline - rerun these first: {', '.join(chosen['stale'])}")
        return OK
    if args.command == "contract":
        golden = root / args.golden if args.golden else None
        cases = contract.write(work, root / args.contract, golden, args.dialect)
        print(f"contract.sql: {len(cases)} cases - run it on the output and save it as runs/main/contract.csv")
        return OK
    if args.command == "gate":
        verdict = gate.gate(work, args.variant, args.confirm, args.regression_only)
        for line in verdict.findings:
            print(f"FAIL {line}")
        print(f"gate {work.slug} {args.variant}: {'pass' if verdict.code == OK else 'fail'}")
        return GATE_FAIL if verdict.code else OK
    if args.command == "budget":
        if args.add is not None or args.user is not None:
            total = budget.add(work, args.add or 0, args.user)
            print(f"budget raised to {total} input tokens")
            return OK
        spent, used, total = budget.is_spent(work)
        if spent:
            print(budget.spent_message(used, total))
            return BUDGET_SPENT
        print(f"budget: {used} of {total} input tokens spent")
        return OK
    if args.command == "deliver":
        print(f"delivered: {deliver.deliver(work, args.decision)}")
        return OK
    raise LanesError(f"unknown command {args.command}")


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        return _run(args)
    except LanesError as exc:
        print(f"ERROR {exc}")
        return INVALID


def entry() -> None:
    sys.exit(main())
