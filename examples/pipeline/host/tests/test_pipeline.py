"""The plan's criteria, run on the fixture as the pipeline runs: raw file in, `orders` table out."""
import sqlite3
import subprocess
import sys


def orders(tmp_path) -> dict:
    db = tmp_path / "dev.db"
    subprocess.run([sys.executable, "pipeline.py", "fixture/orders_raw.csv", str(db)], check=True)
    return {row[0]: row[1] for row in sqlite3.connect(db).execute("SELECT order_id, status FROM orders")}


def test_one_row_per_order(tmp_path):
    db = tmp_path / "dev.db"
    subprocess.run([sys.executable, "pipeline.py", "fixture/orders_raw.csv", str(db)], check=True)
    ids = [row[0] for row in sqlite3.connect(db).execute("SELECT order_id FROM orders")]
    assert sorted(ids) == [1, 2, 3]


def test_latest_version_wins(tmp_path):
    assert orders(tmp_path)[1] == "closed"


def test_cancelled_order_kept(tmp_path):
    assert orders(tmp_path)[3] == "cancelled"
