import builtins
import datetime as dt
import sqlite3

SPEC = """# Orders

**Profile**: pipeline
**Lane**: build
**Approved**: 2026-11-22 - user: "go"

## Goal

One row per order.

## Data contract

### orders

| Column | Type | Required | Unique | Accepted values |
| --- | --- | --- | --- | --- |
| order_id | integer | yes | yes | |
| status | string | | | open, closed |
| loaded_at | timestamp | | | |

- rowCount between 1 and 100
- freshness loaded_at 24h
- sql open_without_date: SELECT COUNT(*) FROM orders WHERE status = 'open' AND loaded_at IS NULL
{golden}"""

GOLDEN = """
## Golden rows

| order_id | status |
| --- | --- |
| 1 | closed |
| 2 | 007 |
"""


def ts(hours_ago: float) -> str:
    return (dt.datetime.now(dt.timezone.utc) - dt.timedelta(hours=hours_ago)).strftime("%Y-%m-%d %H:%M:%S")


def run_sql(sql: str, rows: list) -> dict:
    db = sqlite3.connect(":memory:")
    db.execute("CREATE TABLE orders (order_id INTEGER, status TEXT, loaded_at TEXT)")
    db.executemany("INSERT INTO orders VALUES (?, ?, ?)", rows)
    return dict(db.execute(sql.rstrip().rstrip(";")).fetchall())


def compiled(host, golden: str = "") -> str:
    host.write(".specs/features/p/plan.md", SPEC.format(golden=golden))
    code, out = host.contract("compile", "p", "--dialect", "sqlite")
    assert code == 0, out
    return (host.root / ".specs/features/p/contract.sql").read_text()


def test_spec_contract_compiles_and_counts(host):
    sql = compiled(host)
    fresh = ts(1)
    rows = [(1, "open", fresh), (1, "closed", fresh), (None, "lost", fresh), (4, "open", None)]
    result = run_sql(sql, rows)
    assert list(result) == ["orders.order_id.required", "orders.order_id.unique", "orders.status.invalidValues",
                            "orders.rowCount", "orders.freshness", "orders.sql.open_without_date"]
    assert result["orders.order_id.required"] == 1
    assert result["orders.order_id.unique"] == 2
    assert result["orders.status.invalidValues"] == 1
    assert result["orders.sql.open_without_date"] == 1
    for n, expected in ((0, 1), (1, 0), (100, 0), (101, 1)):
        assert run_sql(sql, [(i, "open", fresh) for i in range(n)])["orders.rowCount"] == expected, n
    assert run_sql(sql, [(1, "open", ts(25))])["orders.freshness"] == 1
    assert run_sql(sql, [(1, "open", ts(23))])["orders.freshness"] == 0


def test_golden_rows(host):
    sql = compiled(host, GOLDEN)
    result = run_sql(sql, [(1, "closed", ts(1)), (2, "007", ts(1))])
    assert result["orders.golden.1"] == 0
    assert result["orders.golden.2"] == 0
    result = run_sql(sql, [(1, "open", ts(1)), (2, "7", ts(1))])
    assert result["orders.golden.1"] == 1
    assert result["orders.golden.2"] == 1


def test_odcs_fallback_and_unknown_rule(host, monkeypatch):
    host.write(".specs/features/p/plan.md", "# Orders\n\n**Profile**: pipeline\n**Lane**: build\n\n## Goal\n\nx\n")
    host.write("contracts/orders.yaml", "schema:\n  - name: orders\n    properties:\n      - name: order_id\n"
                                        "        required: true\n")
    code, out = host.contract("compile", "p", "--dialect", "sqlite")
    assert code == 0, out
    assert "orders.order_id.required" in (host.root / ".specs/features/p/contract.sql").read_text()
    real_import = builtins.__import__

    def no_yaml(name, *args, **kwargs):
        if name == "yaml":
            raise ImportError("no yaml")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", no_yaml)
    code, out = host.contract("compile", "p")
    assert code == 2 and "pyyaml is not installed" in out
    monkeypatch.undo()
    host.write(".specs/features/p/plan.md", SPEC.format(golden="").replace("- freshness loaded_at 24h",
                                                                           "- zScoreOutliers loaded_at"))
    (host.root / ".specs/features/p/contract.sql").unlink()
    code, out = host.contract("compile", "p")
    assert code == 2 and "zScoreOutliers" in out
    assert not (host.root / ".specs/features/p/contract.sql").exists()


def test_contract_gate(host):
    compiled(host, GOLDEN)
    path = ".specs/features/p/runs/main/contract.csv"
    cases = ["orders.order_id.required", "orders.order_id.unique", "orders.status.invalidValues", "orders.rowCount",
             "orders.freshness", "orders.sql.open_without_date", "orders.golden.1", "orders.golden.2"]
    rows = {c: 0 for c in cases}
    rows["orders.order_id.required"] = 2
    rows["orders.golden.2"] = 1
    host.write(path, "case,violations\n" + "".join(f"{c},{v}\n" for c, v in rows.items()))
    code, out = host.contract("gate", "p")
    assert code == 1
    assert "FAIL orders.order_id.required: 2 violations" in out
    assert "FAIL orders.golden.2: golden row missing" in out
    assert "FAIL orders.rowCount" not in out
    host.write(path, "case,violations\n" + "".join(f"{c},0\n" for c in cases))
    assert host.contract("gate", "p")[0] == 0
    host.write(path, "case,violations\n" + "".join(f"{c},0\n" for c in cases[1:]))
    code, out = host.contract("gate", "p")
    assert code == 1 and "orders.order_id.required: no result" in out
