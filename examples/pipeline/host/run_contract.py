"""Glue: run contract.sql on the dev schema and save its output as a Results file."""
import csv
import sqlite3
import sys

sql_path, db_path, out = sys.argv[1], sys.argv[2], sys.argv[3]
rows = sqlite3.connect(db_path).execute(open(sql_path).read().rstrip().rstrip(";")).fetchall()
with open(out, "w", newline="") as handle:
    writer = csv.writer(handle)
    writer.writerow(["case", "violations"])
    writer.writerows(rows)
