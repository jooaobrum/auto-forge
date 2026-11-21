"""Data contracts: a subset of ODCS v3 compiled into one SQL query returning (case, violations)."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

from lanes.work import LanesError, Work

COLUMN_RULES = ("required", "unique", "nullValues", "invalidValues", "duplicateValues")
TABLE_RULES = ("rowCount", "freshness", "sql")
DIALECTS = ("spark", "sqlite")


@dataclass
class Dialect:
    name: str

    def ident(self, name: str) -> str:
        if self.name == "spark":
            return "`" + name.replace("`", "``") + "`"
        return '"' + name.replace('"', '""') + '"'

    def age_hours(self, column: str) -> str:
        if self.name == "spark":
            return f"(unix_timestamp(current_timestamp()) - unix_timestamp(MAX({column}))) / 3600.0"
        return f"(julianday('now') - julianday(MAX({column}))) * 24.0"


def literal(value) -> str:
    if isinstance(value, bool):
        return "1" if value else "0"
    if isinstance(value, (int, float)):
        return repr(value)
    text = str(value)
    try:
        float(text)
        return text
    except ValueError:
        return "'" + text.replace("'", "''") + "'"


def _rule_kind(rule: dict) -> str:
    if rule.get("type") == "sql":
        return "sql"
    kind = rule.get("metric") or rule.get("rule")
    if not kind:
        raise LanesError(f"quality rule {rule} names no `metric` or `rule`")
    return str(kind)


def _arg(rule: dict, name: str):
    return rule.get(name, (rule.get("arguments") or {}).get(name))


def _duplicates(table: str, col: str) -> str:
    return (f"(SELECT COALESCE(SUM(n), 0) FROM (SELECT COUNT(*) AS n FROM {table} "
            f"WHERE {col} IS NOT NULL GROUP BY {col} HAVING COUNT(*) > 1) AS d)")


def _column_rule(kind: str, rule: dict, table: str, col: str) -> str:
    if kind in ("required", "nullValues"):
        return f"(SELECT COUNT(*) FROM {table} WHERE {col} IS NULL)"
    if kind in ("unique", "duplicateValues"):
        return _duplicates(table, col)
    if kind == "invalidValues":
        valid = _arg(rule, "validValues")
        if not valid:
            raise LanesError(f"invalidValues on {col} needs validValues")
        values = ", ".join(literal(v) for v in valid)
        return f"(SELECT COUNT(*) FROM {table} WHERE {col} IS NOT NULL AND {col} NOT IN ({values}))"
    raise LanesError(f"unsupported rule `{kind}` - the subset is {', '.join(COLUMN_RULES + TABLE_RULES)}")


def _table_rule(kind: str, rule: dict, table: str, dialect: Dialect) -> str:
    if kind == "rowCount":
        bounds = _arg(rule, "mustBeBetween")
        if not bounds or len(bounds) != 2:
            raise LanesError("rowCount needs mustBeBetween: [min, max]")
        low, high = bounds
        return f"(SELECT CASE WHEN COUNT(*) BETWEEN {int(low)} AND {int(high)} THEN 0 ELSE 1 END FROM {table})"
    if kind == "freshness":
        column, hours = _arg(rule, "column"), _arg(rule, "maxAgeHours")
        if not column or hours is None:
            raise LanesError("freshness needs column and maxAgeHours")
        col = dialect.ident(column)
        return (f"(SELECT CASE WHEN MAX({col}) IS NULL OR {dialect.age_hours(col)} > {float(hours)} "
                f"THEN 1 ELSE 0 END FROM {table})")
    if kind == "sql":
        query = rule.get("query")
        if not query:
            raise LanesError("a sql rule needs a query returning a violation count")
        return f"({str(query).strip().rstrip(';')})"
    raise LanesError(f"unsupported rule `{kind}` - the subset is {', '.join(COLUMN_RULES + TABLE_RULES)}")


def compile_contract(contract: dict, dialect_name: str = "spark", golden: list[dict] | None = None):
    """Return (sql, case ids). Raises LanesError on anything outside the subset."""
    if dialect_name not in DIALECTS:
        raise LanesError(f"unknown dialect `{dialect_name}` - use {', '.join(DIALECTS)}")
    dialect = Dialect(dialect_name)
    datasets = contract.get("schema") or []
    if not datasets:
        raise LanesError("the contract has no `schema` entries")
    parts: list[tuple[str, str]] = []

    def add(case: str, expr: str) -> None:
        if any(case == c for c, _ in parts):
            n = 2
            while any(f"{case}.{n}" == c for c, _ in parts):
                n += 1
            case = f"{case}.{n}"
        parts.append((case, expr))

    for dataset in datasets:
        name = dataset.get("name")
        if not name:
            raise LanesError("every schema entry needs a `name`")
        table = dialect.ident(dataset.get("physicalName") or name)
        for prop in dataset.get("properties") or []:
            col_name = prop.get("name")
            col = dialect.ident(col_name)
            for flag in ("required", "unique"):
                if prop.get(flag):
                    add(f"{name}.{col_name}.{flag}", _column_rule(flag, {}, table, col))
            for rule in prop.get("quality") or []:
                kind = _rule_kind(rule)
                add(f"{name}.{col_name}.{kind}", _column_rule(kind, rule, table, col))
        for index, rule in enumerate(dataset.get("quality") or [], start=1):
            kind = _rule_kind(rule)
            case = f"{name}.sql.{rule.get('name') or index}" if kind == "sql" else f"{name}.{kind}"
            add(case, _table_rule(kind, rule, table, dialect))
    if golden:
        first = datasets[0]
        table = dialect.ident(first.get("physicalName") or first["name"])
        for index, row in enumerate(golden, start=1):
            where = " AND ".join(f"{dialect.ident(k)} = {literal(v)}" for k, v in row.items())
            add(f"{first['name']}.golden.{index}",
                f"(SELECT CASE WHEN EXISTS (SELECT 1 FROM {table} WHERE {where}) THEN 0 ELSE 1 END)")
    case_col = dialect.ident("case")
    selects = [f"SELECT {literal(case)} AS {case_col}, {expr} AS violations" for case, expr in parts]
    return "\nUNION ALL\n".join(selects) + ";\n", [case for case, _ in parts]


def read_golden(path: Path) -> list[dict]:
    with path.open(newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def write(work: Work, contract_path: Path, golden_path: Path | None, dialect: str) -> list[str]:
    import yaml

    if not contract_path.exists():
        raise LanesError(f"{contract_path} is missing")
    try:
        contract = yaml.safe_load(contract_path.read_text()) or {}
    except yaml.YAMLError as exc:
        raise LanesError(f"{contract_path.name} is not valid YAML: {exc}") from exc
    golden = read_golden(golden_path) if golden_path else None
    sql, cases = compile_contract(contract, dialect, golden)
    work.dir.mkdir(parents=True, exist_ok=True)
    work.path("contract.sql").write_text(sql)
    work.write_json("contract.json", {"contract": str(contract_path), "dialect": dialect, "cases": cases})
    return cases
