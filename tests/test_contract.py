import datetime as dt
import sqlite3

from lanes.contract import compile_contract

ORDERS = {
    "schema": [{
        "name": "orders",
        "properties": [
            {"name": "order_id", "logicalType": "integer", "required": True, "unique": True},
            {"name": "status", "logicalType": "string"},
            {"name": "updated_at", "logicalType": "timestamp"},
        ],
        "quality": [
            {"metric": "rowCount", "mustBeBetween": [1, 100]},
            {"metric": "freshness", "column": "updated_at", "maxAgeHours": 24},
        ],
    }]
}


def run_sql(sql: str, rows: list[tuple]) -> dict:
    db = sqlite3.connect(":memory:")
    db.execute("CREATE TABLE orders (order_id INTEGER, status TEXT, updated_at TEXT)")
    db.executemany("INSERT INTO orders VALUES (?, ?, ?)", rows)
    return {case: violations for case, violations in db.execute(sql.rstrip().rstrip(";"))}


def ts(hours_ago: float) -> str:
    return (dt.datetime.now(dt.timezone.utc) - dt.timedelta(hours=hours_ago)).strftime("%Y-%m-%d %H:%M:%S")


def test_case_ids(host):
    host.write("contracts/orders.yaml", __import__("yaml").safe_dump(ORDERS))
    code, out = host.rl("contract", "p", "contracts/orders.yaml", "--dialect", "sqlite")
    assert code == 0, out
    sql = (host.root / ".lanes/work/p/contract.sql").read_text()
    result = run_sql(sql, [(1, "open", ts(1))])
    assert list(result) == ["orders.order_id.required", "orders.order_id.unique", "orders.rowCount",
                            "orders.freshness"]


def test_violation_counts_on_sqlite():
    sql, _ = compile_contract(ORDERS, "sqlite")
    fresh = ts(1)
    two_nulls = [(None, "open", fresh), (None, "open", fresh), (3, "open", fresh)]
    assert run_sql(sql, two_nulls)["orders.order_id.required"] == 2
    assert run_sql(sql, [])["orders.rowCount"] == 1
    fifty = [(i, "open", fresh) for i in range(50)]
    assert run_sql(sql, fifty)["orders.rowCount"] == 0
    for n, expected in ((1, 0), (100, 0), (101, 1)):
        assert run_sql(sql, [(i, "open", fresh) for i in range(n)])["orders.rowCount"] == expected, n
    assert run_sql(sql, [(1, "open", ts(25))])["orders.freshness"] == 1
    assert run_sql(sql, [(1, "open", ts(23))])["orders.freshness"] == 0


def test_every_rule_kind_counts():
    contract = {"schema": [{
        "name": "orders",
        "properties": [
            {"name": "order_id", "unique": True, "quality": [
                {"metric": "nullValues"}, {"metric": "duplicateValues"}]},
            {"name": "status", "quality": [
                {"metric": "invalidValues", "arguments": {"validValues": ["open", "closed"]}}]},
        ],
        "quality": [{"type": "sql", "name": "no_open_without_date",
                     "query": "SELECT COUNT(*) FROM orders WHERE status = 'open' AND updated_at IS NULL"}],
    }]}
    sql, cases = compile_contract(contract, "sqlite")
    rows = [(1, "open", None), (1, "closed", "x"), (2, "lost", "x"), (None, "open", "x"), (5, None, "x")]
    result = run_sql(sql, rows)
    assert result == {
        "orders.order_id.unique": 2,
        "orders.order_id.nullValues": 1,
        "orders.order_id.duplicateValues": 2,
        "orders.status.invalidValues": 1,
        "orders.sql.no_open_without_date": 1,
    }
    assert cases == list(result)


def test_unknown_rule_is_refused(host):
    bad = {"schema": [{"name": "orders", "properties": [
        {"name": "order_id", "quality": [{"metric": "zScoreOutliers"}]}]}]}
    host.write("contracts/bad.yaml", __import__("yaml").safe_dump(bad))
    code, out = host.rl("contract", "p", "contracts/bad.yaml")
    assert code == 2
    assert "zScoreOutliers" in out
    assert not (host.root / ".lanes/work/p/contract.sql").exists()


def test_golden_rows_compile_to_cases():
    golden = [{"order_id": "1", "status": "open"}, {"order_id": "2", "status": "closed"}]
    sql, cases = compile_contract(ORDERS, "sqlite", golden)
    assert cases[-2:] == ["orders.golden.1", "orders.golden.2"]
    result = run_sql(sql, [(1, "open", ts(1))])
    assert result["orders.golden.1"] == 0
    assert result["orders.golden.2"] == 1
    sql, _ = compile_contract(ORDERS, "sqlite", [{"order_id": "1", "status": "007"}])
    assert run_sql(sql, [(1, "007", ts(1))])["orders.golden.1"] == 0
    assert run_sql(sql, [(1, "7", ts(1))])["orders.golden.1"] == 1


def test_spark_dialect_quotes_with_backticks():
    sql, _ = compile_contract(ORDERS, "spark")
    assert "`orders`" in sql and "`case`" in sql and "current_timestamp()" in sql
