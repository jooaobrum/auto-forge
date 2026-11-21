"""target_signal.py - what relates to the target, on the train window only. Aggregates only.

  python3 target_signal.py <catalog.schema.table> --lock .specs/split.lock [--group lot] \
      --out .specs/features/<slug>/eda.md [--top 25] [--json <path>]

Per numeric column: correlation with the target, % missing, target rate when missing vs present,
constant flag, and for the strongest columns the correlation per month (stability) and, with
--group, raw vs group-relative correlation. Per categorical column (<= 50 levels in a sample):
target rate per level. Flags |r| > 0.9 as a leakage suspect. Everything runs as SQL in Spark; only
aggregates come back. Importable: main(argv, spark=spark).
"""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import sys

CHUNK = 150


def _spark():
    try:
        from pyspark.sql import SparkSession
        s = SparkSession.getActiveSession()
        if s is not None:
            return s
    except ImportError:
        pass
    from databricks.connect import DatabricksSession
    b = DatabricksSession.builder
    if os.environ.get("DATABRICKS_CONFIG_PROFILE"):
        b = b.profile(os.environ["DATABRICKS_CONFIG_PROFILE"])
    return b.serverless(True).getOrCreate()


def _rows(spark, sql):
    return spark.sql(sql).toPandas().to_dict("records")


def _num(v):
    try:
        f = float(v)
        return None if math.isnan(f) else f
    except (TypeError, ValueError):
        return None


def signal(spark, table, lock, group=None, top=25):
    t, y = lock["time_col"], lock["label_col"]
    lo, hi = lock["windows"]["train"]
    where = f"to_date(`{t}`) BETWEEN '{lo}' AND '{hi}'"
    sample = spark.sql(f"SELECT * FROM {table} WHERE {where} LIMIT 2000").toPandas()
    skip = {t, y, lock["id_col"], group, lock.get("group_col")}
    numeric = [c for c in sample.columns if c not in skip and sample[c].dtype.kind in "iuf"]
    categorical = [c for c in sample.columns if c not in skip and sample[c].dtype.kind in "OSUb"
                   and 1 < sample[c].nunique() <= 50]
    n = _rows(spark, f"SELECT count(*) AS n, avg(`{y}`) AS rate FROM {table} WHERE {where}")[0]
    out = {"table": table, "window": [lo, hi], "n": int(n["n"]), "target_rate": _num(n["rate"]), "numeric": [], "categorical": {}}

    for i in range(0, len(numeric), CHUNK):
        cols = numeric[i:i + CHUNK]
        exprs = []
        for j, c in enumerate(cols):
            q = f"`{c}`"
            exprs += [f"corr({q}, `{y}`) AS r{j}", f"avg(CASE WHEN {q} IS NULL THEN 1.0 ELSE 0.0 END) AS m{j}",
                      f"avg(CASE WHEN {q} IS NULL THEN `{y}` END) AS ym{j}", f"avg(CASE WHEN {q} IS NOT NULL THEN `{y}` END) AS yp{j}",
                      f"min({q}) AS lo{j}", f"max({q}) AS hi{j}"]
        r = _rows(spark, f"SELECT {', '.join(exprs)} FROM {table} WHERE {where}")[0]
        for j, c in enumerate(cols):
            out["numeric"].append({"column": c, "r": _num(r[f"r{j}"]), "missing": _num(r[f"m{j}"]),
                                   "rate_if_missing": _num(r[f"ym{j}"]), "rate_if_present": _num(r[f"yp{j}"]),
                                   "constant": r[f"lo{j}"] == r[f"hi{j}"]})
    ranked = sorted([c for c in out["numeric"] if c["r"] is not None], key=lambda c: -abs(c["r"]))
    strong = [c["column"] for c in ranked[:min(top, 15)]]
    if strong:
        month = f"substr(CAST(`{t}` AS STRING), 1, 7)"
        exprs = ", ".join(f"corr(`{c}`, `{y}`) AS r{j}" for j, c in enumerate(strong))
        per = _rows(spark, f"SELECT {month} AS month, count(*) AS n, {exprs} FROM {table} WHERE {where} GROUP BY {month} ORDER BY month")
        out["stability"] = {c: {str(p["month"]): _num(p[f"r{j}"]) for p in per} for j, c in enumerate(strong)}
        if group:
            rel = ", ".join(f"`{c}` - avg(`{c}`) OVER (PARTITION BY `{group}`) AS d{j}" for j, c in enumerate(strong))
            inner = f"SELECT `{y}`, {rel} FROM {table} WHERE {where}"
            r = _rows(spark, f"SELECT {', '.join(f'corr(d{j}, `{y}`) AS r{j}' for j in range(len(strong)))} FROM ({inner}) sub")[0]
            out["group_relative"] = {c: _num(r[f"r{j}"]) for j, c in enumerate(strong)}
    for c in categorical:
        out["categorical"][c] = _rows(spark, f"SELECT CAST(`{c}` AS STRING) AS level, count(*) AS n, avg(`{y}`) AS rate "
                                              f"FROM {table} WHERE {where} GROUP BY CAST(`{c}` AS STRING) ORDER BY n DESC LIMIT 20")
    out["ranked"] = [c["column"] for c in ranked[:top]]
    out["leak_suspects"] = [c["column"] for c in ranked if abs(c["r"]) > 0.9]
    out["constant"] = [c["column"] for c in out["numeric"] if c["constant"]]
    out["informative_missing"] = [c["column"] for c in out["numeric"]
                                  if c["missing"] and 0.01 < c["missing"] < 0.99 and c["rate_if_missing"] is not None
                                  and c["rate_if_present"] and abs(c["rate_if_missing"] - c["rate_if_present"]) > 0.5 * c["rate_if_present"]]
    return out


def to_markdown(s, top=25):
    f = lambda v, p=3: "-" if v is None else f"{v:.{p}f}"
    by = {c["column"]: c for c in s["numeric"]}
    L = ["## Signal panorama", "",
         f"Train only: {s['window'][0]} .. {s['window'][1]}, {s['n']} rows, target rate {f(s['target_rate'])}.", "",
         f"- Numeric: {len(s['numeric'])}; constant: {len(s['constant'])}; informative missing: {len(s['informative_missing'])}",
         f"- Leakage suspects (|r| > 0.9): {', '.join(f'`{c}`' for c in s['leak_suspects']) or 'nenhuma'}", "",
         f"### Top {min(top, len(s['ranked']))} by |correlation|", "",
         "| Column | r | % missing | rate if missing | rate if present | r per month | group-relative r |",
         "|---|---|---|---|---|---|---|"]
    for c in s["ranked"]:
        d = by[c]
        st = s.get("stability", {}).get(c)
        stab = " / ".join(f(v, 2) for v in st.values()) if st else "-"
        gr = f(s.get("group_relative", {}).get(c))
        L.append(f"| `{c}` | {f(d['r'])} | {f((d['missing'] or 0) * 100, 1)} | {f(d['rate_if_missing'])} | {f(d['rate_if_present'])} | {stab} | {gr} |")
    if s["informative_missing"]:
        L += ["", "### Informative missing", ""]
        L += [f"- `{c}`: rate {f(by[c]['rate_if_missing'])} if missing vs {f(by[c]['rate_if_present'])} if present "
              f"({f(by[c]['missing'] * 100, 1)}% missing)" for c in s["informative_missing"][:20]]
    for c, levels in s["categorical"].items():
        L += ["", f"### `{c}`", "", "| Level | n | target rate |", "|---|---|---|"]
        L += [f"| {lv['level']} | {lv['n']} | {f(_num(lv['rate']))} |" for lv in levels]
    return "\n".join(L) + "\n"


def write_md(path, md):
    text = ""
    if os.path.exists(path):
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
    pat = re.compile(r"^## Signal panorama\n.*?(?=^## (?!#)|\Z)", re.DOTALL | re.MULTILINE)
    if pat.search(text):
        text = pat.sub(lambda _: md + "\n", text, count=1)
    else:
        text = (text or "# EDA\n\n") + ("\n" if text and not text.endswith("\n") else "") + md + \
               "\n## Findings\n\n## Questions\n\n## Candidate features\n\n## Leakage suspects\n"
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)


def main(argv=None, spark=None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("table")
    p.add_argument("--lock", default=".specs/split.lock")
    p.add_argument("--group")
    p.add_argument("--top", type=int, default=25)
    p.add_argument("--out", required=True, help=".specs/features/<slug>/eda.md")
    p.add_argument("--json", help="default: target_signal.json next to --out")
    a = p.parse_args(argv)
    a.json = a.json or os.path.join(os.path.dirname(a.out), "target_signal.json")
    with open(a.lock, encoding="utf-8") as fh:
        lock = json.load(fh)
    s = signal(spark or _spark(), a.table, lock, a.group, a.top)
    os.makedirs(os.path.dirname(a.json) or ".", exist_ok=True)
    with open(a.json, "w", encoding="utf-8") as fh:
        json.dump(s, fh, indent=2, default=str)
    write_md(a.out, to_markdown(s, a.top))
    print(f"wrote {a.out} and {a.json}: top {', '.join(s['ranked'][:5])}; leak suspects: {s['leak_suspects'] or 'none'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
