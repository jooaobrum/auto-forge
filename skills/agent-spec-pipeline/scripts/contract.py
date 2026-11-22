"""agent-spec-pipeline: compile the plan's data contract into one SQL query, and gate its results.

Usage: python3 contract.py [--root <repo>] compile <slug> [--dialect spark|sqlite]
       python3 contract.py [--root <repo>] gate <slug>
The query returns one row (case, violations) per rule; run it on the pipeline's output and save it as
`.specs/features/<slug>/runs/main/contract.csv`. Exit: 0 ok, 1 gate fail, 2 invalid input,
5 halted (.specs/HALT exists).
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import spec_md

OK, GATE_FAIL, INVALID = 0, 1, 2
COLUMN_RULES = ("required", "unique", "nullValues", "invalidValues", "duplicateValues")
TABLE_RULES = ("rowCount", "freshness", "sql")
DIALECTS = ("spark", "sqlite")


class ContractError(Exception):
    """Invalid or missing input; exit 2."""


# --- reading the contract -------------------------------------------------------------------------------------

def _rule(text: str) -> dict:
    match = re.match(r"rowCount\s+between\s+(\d+)\s+and\s+(\d+)$", text, re.IGNORECASE)
    if match:
        return {"metric": "rowCount", "mustBeBetween": [int(match.group(1)), int(match.group(2))]}
    match = re.match(r"freshness\s+(\S+)\s+(\d+(?:\.\d+)?)\s*h$", text, re.IGNORECASE)
    if match:
        return {"metric": "freshness", "column": match.group(1).strip("`"), "maxAgeHours": float(match.group(2))}
    match = re.match(r"sql\s+([\w.-]+)\s*:\s*(.+)$", text, re.IGNORECASE)
    if match:
        return {"type": "sql", "name": match.group(1), "query": match.group(2).strip().strip("`")}
    raise ContractError(f"unsupported rule `{text}` - use `rowCount between <a> and <b>`, "
                        "`freshness <column> <hours>h` or `sql <name>: <query>`")


def from_spec(text: str) -> dict:
    """The `## Data contract` section as the ODCS-shaped dict the compiler reads; {} when there is none."""
    body = spec_md.section(text, "Data contract")
    if not body:
        return {}
    datasets = []
    for name, block in spec_md.subsections(body).items():
        properties = []
        for row in spec_md.table(block):
            column = row.get("Column", "")
            if not column:
                continue
            prop = {"name": column, "logicalType": row.get("Type", ""),
                    "required": spec_md.is_yes(row.get("Required", "")),
                    "unique": spec_md.is_yes(row.get("Unique", "")), "quality": []}
            accepted = spec_md.split_list(row.get("Accepted values", ""))
            if accepted:
                prop["quality"].append({"metric": "invalidValues", "validValues": accepted})
            properties.append(prop)
        table_name = spec_md.field(block, "Table")
        datasets.append({"name": name, "physicalName": table_name or None, "properties": properties,
                         "quality": [_rule(item) for item in spec_md.bullets(block)]})
    return {"schema": datasets}


def from_odcs(root: Path) -> dict:
    files = sorted((root / "contracts").glob("*.yaml")) + sorted((root / "contracts").glob("*.yml"))
    if not files:
        return {}
    try:
        import yaml
    except ImportError as exc:
        raise ContractError(f"{files[0].name} is ODCS YAML and pyyaml is not installed - install pyyaml, "
                            "or put the contract in the plan's ## Data contract section") from exc
    try:
        return yaml.safe_load(files[0].read_text()) or {}
    except yaml.YAMLError as exc:
        raise ContractError(f"{files[0].name} is not valid YAML: {exc}") from exc


# --- compiling ------------------------------------------------------------------------------------------------

def ident(name: str, dialect: str) -> str:
    if dialect == "spark":
        return ".".join("`" + part.replace("`", "``") + "`" for part in name.split("."))
    return ".".join('"' + part.replace('"', '""') + '"' for part in name.split("."))


def literal(value) -> str:
    if isinstance(value, bool):
        return "1" if value else "0"
    if isinstance(value, (int, float)):
        return repr(value)
    return text_literal(value)


def text_literal(value) -> str:
    """A text literal: golden rows come from a table of text, so `007` stays text and the engine coerces it."""
    return "'" + str(value).replace("'", "''") + "'"


def _kind(rule: dict) -> str:
    if rule.get("type") == "sql":
        return "sql"
    kind = rule.get("metric") or rule.get("rule")
    if not kind:
        raise ContractError(f"quality rule {rule} names no `metric` or `rule`")
    return str(kind)


def _arg(rule: dict, name: str):
    return rule.get(name, (rule.get("arguments") or {}).get(name))


def _column_rule(kind: str, rule: dict, table: str, col: str) -> str:
    if kind in ("required", "nullValues"):
        return f"(SELECT COUNT(*) FROM {table} WHERE {col} IS NULL)"
    if kind in ("unique", "duplicateValues"):
        return (f"(SELECT COALESCE(SUM(n), 0) FROM (SELECT COUNT(*) AS n FROM {table} "
                f"WHERE {col} IS NOT NULL GROUP BY {col} HAVING COUNT(*) > 1) AS d)")
    if kind == "invalidValues":
        valid = _arg(rule, "validValues")
        if not valid:
            raise ContractError(f"invalidValues on {col} needs validValues")
        values = ", ".join(literal(v) for v in valid)
        return f"(SELECT COUNT(*) FROM {table} WHERE {col} IS NOT NULL AND {col} NOT IN ({values}))"
    raise ContractError(f"unsupported rule `{kind}` - the subset is {', '.join(COLUMN_RULES + TABLE_RULES)}")


def _table_rule(kind: str, rule: dict, table: str, dialect: str) -> str:
    if kind == "rowCount":
        bounds = _arg(rule, "mustBeBetween")
        if not bounds or len(bounds) != 2:
            raise ContractError("rowCount needs two bounds")
        return (f"(SELECT CASE WHEN COUNT(*) BETWEEN {int(bounds[0])} AND {int(bounds[1])} THEN 0 ELSE 1 END "
                f"FROM {table})")
    if kind == "freshness":
        column, hours = _arg(rule, "column"), _arg(rule, "maxAgeHours")
        if not column or hours is None:
            raise ContractError("freshness needs a column and hours")
        col = ident(column, dialect)
        if dialect == "spark":
            age = f"(unix_timestamp(current_timestamp()) - unix_timestamp(MAX({col}))) / 3600.0"
        else:
            age = f"(julianday('now') - julianday(MAX({col}))) * 24.0"
        return f"(SELECT CASE WHEN MAX({col}) IS NULL OR {age} > {float(hours)} THEN 1 ELSE 0 END FROM {table})"
    if kind == "sql":
        query = rule.get("query")
        if not query:
            raise ContractError("a sql rule needs a query returning a violation count")
        return f"({str(query).strip().rstrip(';')})"
    raise ContractError(f"unsupported rule `{kind}` - the subset is {', '.join(COLUMN_RULES + TABLE_RULES)}")


def compile_contract(contract: dict, dialect: str = "spark", golden: list | None = None) -> tuple[str, list]:
    if dialect not in DIALECTS:
        raise ContractError(f"unknown dialect `{dialect}` - use {', '.join(DIALECTS)}")
    datasets = contract.get("schema") or []
    if not datasets:
        raise ContractError("the contract names no dataset")
    parts: list = []

    def add(case: str, expr: str) -> None:
        taken = {c for c, _ in parts}
        n, base = 2, case
        while case in taken:
            case, n = f"{base}.{n}", n + 1
        parts.append((case, expr))

    for dataset in datasets:
        name = dataset.get("name")
        if not name:
            raise ContractError("every dataset needs a name")
        table = ident(dataset.get("physicalName") or name, dialect)
        for prop in dataset.get("properties") or []:
            col_name = prop.get("name")
            col = ident(col_name, dialect)
            for flag in ("required", "unique"):
                if prop.get(flag):
                    add(f"{name}.{col_name}.{flag}", _column_rule(flag, {}, table, col))
            for rule in prop.get("quality") or []:
                kind = _kind(rule)
                add(f"{name}.{col_name}.{kind}", _column_rule(kind, rule, table, col))
        for index, rule in enumerate(dataset.get("quality") or [], start=1):
            kind = _kind(rule)
            case = f"{name}.sql.{rule.get('name') or index}" if kind == "sql" else f"{name}.{kind}"
            add(case, _table_rule(kind, rule, table, dialect))
    if golden:
        first = datasets[0]
        table = ident(first.get("physicalName") or first["name"], dialect)
        for index, row in enumerate(golden, start=1):
            where = " AND ".join(f"{ident(k, dialect)} = {text_literal(v)}" for k, v in row.items())
            add(f"{first['name']}.golden.{index}",
                f"(SELECT CASE WHEN EXISTS (SELECT 1 FROM {table} WHERE {where}) THEN 0 ELSE 1 END)")
    case_col = ident("case", dialect)
    selects = [f"SELECT {text_literal(case)} AS {case_col}, {expr} AS violations" for case, expr in parts]
    return "\nUNION ALL\n".join(selects) + ";\n", [case for case, _ in parts]


# --- commands -------------------------------------------------------------------------------------------------

def work_dir(root: Path, slug: str) -> Path:
    return root / ".specs" / "features" / slug


def compile_work(root: Path, slug: str, dialect: str) -> list[str]:
    spec_path = work_dir(root, slug) / "plan.md"
    if not spec_path.exists():
        raise ContractError(f".specs/features/{slug}/plan.md is missing")
    text = spec_path.read_text()
    contract = from_spec(text) or from_odcs(root)
    if not contract:
        raise ContractError("no contract: add a ## Data contract section to the plan, or an ODCS file in contracts/")
    golden = [row for row in spec_md.table(spec_md.section(text, "Golden rows")) if any(row.values())]
    sql, cases = compile_contract(contract, dialect, golden)
    (work_dir(root, slug) / "contract.sql").write_text(sql)
    (work_dir(root, slug) / "contract.json").write_text(json.dumps({"dialect": dialect, "cases": cases}, indent=2))
    return cases


def gate_work(root: Path, slug: str) -> tuple[int, list[str]]:
    folder = work_dir(root, slug)
    if not (folder / "contract.json").exists():
        raise ContractError("no contract.json - compile the contract first")
    cases = json.loads((folder / "contract.json").read_text())["cases"]
    results: dict = {}
    for path in sorted((folder / "runs" / "main").glob("*.csv")):
        try:
            with path.open(newline="") as handle:
                reader = csv.DictReader(handle)
                if not reader.fieldnames or "case" not in reader.fieldnames:
                    raise ContractError(f"{path.name}: expected `case` and `violations` columns")
                for row in reader:
                    results[row["case"]] = int(float(row.get("violations") or 0))
        except (ValueError, csv.Error) as exc:
            raise ContractError(f"{path.name}: malformed - {exc}") from exc
    findings, rows = [], []
    for case in cases:
        if case not in results:
            findings.append(f"{case}: no result")
            rows.append(f"| {case} | - |")
            continue
        rows.append(f"| {case} | {results[case]} |")
        if results[case] > 0:
            findings.append(f"{case}: " + ("golden row missing" if ".golden." in case else f"{results[case]} violations"))
    code = GATE_FAIL if findings else OK
    command = f"contract.py gate {slug}"
    lines = [f"# Results - {slug}", "", f"Gate: `{command}` - **{'pass' if code == OK else 'fail'}**", "",
             "| Case | Violations |", "| --- | --- |", *rows]
    if findings:
        lines += ["", "## Findings", ""] + [f"- {f}" for f in findings]
    (folder / "results.md").write_text("\n".join(lines) + "\n")
    (folder / "gate.json").write_text(json.dumps({"exit": code, "command": command, "findings": findings}, indent=2))
    return code, findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="contract.py", description=__doc__)
    parser.add_argument("--root", default=".")
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("compile")
    p.add_argument("slug")
    p.add_argument("--dialect", default="spark", choices=DIALECTS)
    sub.add_parser("gate").add_argument("slug")
    args = parser.parse_args(argv)
    halt = spec_md.halted(args.root)
    if halt:
        print(halt)
        return spec_md.HALT_EXIT
    root = Path(args.root).resolve()
    try:
        if args.command == "compile":
            cases = compile_work(root, args.slug, args.dialect)
            print(f"contract.sql: {len(cases)} cases - run it on the output, save as runs/main/contract.csv")
            return OK
        code, findings = gate_work(root, args.slug)
        for line in findings:
            print(f"FAIL {line}")
        print(f"gate {args.slug}: {'pass' if code == OK else 'fail'}")
        return code
    except ContractError as exc:
        print(f"ERROR {exc}")
        return INVALID


if __name__ == "__main__":
    sys.exit(main())
