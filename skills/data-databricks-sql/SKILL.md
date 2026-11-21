---
name: data-databricks-sql
description: Use when a lane reaches its plan or work load point and needs data from Databricks - an example domain skill showing how a team writes down how to query its data. Replace its content with your own catalogs, tables and access rules.
---

# Data: Databricks SQL (example)

An example of a team's data-access skill. Load points: **plan** (to know what data exists), **work** (to
query it). Keep it to what an agent cannot find by looking.

- **Where the data lives.** Catalog `main`, schemas `sales` (production, read only) and `dev_<user>`
  (scratch, writable). Never write outside `dev_<user>`.
- **How to query.** From a notebook: `spark.sql("...")`. From a laptop: the Databricks SQL connector with
  the warehouse in `DATABRICKS_WAREHOUSE_ID`; credentials come from the environment, never from a file.
- **Size.** Sample with `TABLESAMPLE (1 PERCENT)` or `LIMIT` while exploring; full scans only in jobs.
- **Contract runs.** Run `contract.sql` with `spark.sql(open(path).read()).toPandas().to_csv(out, index=False)`
  and save it as the work's `runs/main/contract.csv`.
