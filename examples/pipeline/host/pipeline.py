"""Load raw orders into the dev schema, keeping the latest version of each order."""
import csv
import datetime as dt
import sqlite3
import sys

raw, db_path = sys.argv[1], sys.argv[2]
latest: dict = {}
with open(raw, newline="") as handle:
    for row in csv.DictReader(handle):
        if row["order_id"] not in latest or int(row["version"]) > int(latest[row["order_id"]]["version"]):
            latest[row["order_id"]] = row
now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
db = sqlite3.connect(db_path)
db.execute("DROP TABLE IF EXISTS orders")
db.execute("CREATE TABLE orders (order_id INTEGER, status TEXT, loaded_at TEXT)")
db.executemany("INSERT INTO orders VALUES (?, ?, ?)",
               [(int(r["order_id"]), r["status"], now) for r in latest.values()])
db.commit()
