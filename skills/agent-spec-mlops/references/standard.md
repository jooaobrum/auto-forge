# The production standard

What `validate_prod.py` checks is marked with its rule (D1-D10). Code style is the team's: classes or functions,
as long as each pipeline has a `main()` that reads the config and the logic is testable.

## Layout

```
config/project.yml               # the single source of truth (D1, D6, D10)
src/<pkg>/
├── data.py, features.py, model.py, ...   # testable logic: data in, data out
└── pipelines/
    ├── features.py              # main(): config -> functions -> feature table
    ├── train.py                 # main(): trains, registers the model, writes .specs/prod/trace.json
    ├── score.py                 # main(): loads the alias, scores, writes the inference table
    └── monitor.py               # main(): creates or updates the monitor of the inference table
tests/test_<module>.py           # one per module of src/<pkg>/ (D4)
databricks.yml, resources/*.yml  # on Databricks: targets dev, qa, prod and jobs (D5)
uv.lock                          # dependencies locked (D9)
.specs/prod/trace.json           # traceability and reproducibility (D7, D8, D9, D10)
MODEL_CARD.md                    # written by model_card.py, then reviewed (D8)
```

## config/project.yml (D1)

```yaml
project: churn
platform: databricks              # optional: turns on D5 and the Unity Catalog registry of D10
environments:
  dev:  {catalog: main, schema: churn_dev}
  qa:   {catalog: main, schema: churn_qa}
  prod: {catalog: main, schema: churn}
inputs:
  accounts: main.crm.accounts
model:
  name: churn_30d                 # registered as <catalog>.<schema>.<name>
  task: binary
  threshold: 0.42                 # the experiment's, chosen on valid
pipelines: [features, train, score, monitor]
mlflow:
  experiment: /Shared/ds/churn
  registry: databricks-uc
  required_tags: [git_commit, config_env, round, experiment_id, training_tables]
monitoring:
  inference_table: inference      # <catalog>.<schema>.inference
  metrics: [pr_auc, positive_rate, score_mean]
  drift: {baseline: training, threshold: 0.2}
  schedule: daily
  alert: ds-alerts
```

- Each environment writes to its own `catalog.schema`; prod never writes to dev's (D1).
- No `catalog.schema` of the config and no input table appears literally in `src/` (D2): the code gets them
  from the config.

## Pipelines are config plus logic (D3, D4)

```python
# src/churn/pipelines/train.py
import argparse
from churn import config, data, features, model, tracing

def main(argv=None, spark=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--env", choices=["dev", "qa", "prod"], required=True)
    cfg = config.load(parser.parse_args(argv).env)   # resolves the environment's catalog.schema
    df, versions = data.read_inputs(spark, cfg)      # also returns the version of each table read
    X = features.build(df)
    est = model.fit(X, cfg)
    run_id, version = model.register(est, cfg)      # registry, alias challenger
    tracing.write(cfg, versions, run_id, version)    # .specs/prod/trace.json
```

The logic (`features.build`, `model.fit`, ...) reads no config and no table: it takes data and returns data,
which keeps it testable. Every pipeline listed in `pipelines:`, at least `train` and `score`, exists with a
`main()` that loads the config (D3). Every module has its `tests/test_<module>.py`, and the tests pass: run
them with `--junitxml .specs/features/<slug>/runs/main/tests.xml`, the file D4 reads.

## Deploy targets (D5, Databricks only)

With `platform: databricks`, `databricks.yml` has the targets `dev`, `qa` and `prod`, and every job in
`resources/*.yml` calls a pipeline with `--env`. Without a platform, D5 is skipped with a warning: the team's
deploy is checked by its own build lane.

## MLflow (D10)

- The registry is declared (`mlflow.registry`); on Databricks it is Unity Catalog (`databricks-uc`) and the
  model is named `<catalog>.<schema>.<model.name>` of the environment.
- The signature and input example hold only the features.
- Aliases: training registers `challenger`; `champion` is given only by the promotion (references/promote.md).
- Every training run carries the tags in `mlflow.required_tags`, at least `git_commit`, `config_env`, `round`,
  `experiment_id` and `training_tables`.
- Without an `mlflow:` section (and no platform), the registry and tags are not checked; the trace still names
  the model, an integer version and the commit.

## Monitoring (D6)

`monitoring` in the config with `inference_table`, `metrics` (a list), `drift` (`baseline` and a numeric
`threshold`), `schedule` and `alert`. The `monitor` pipeline creates the monitor from it; the inference table
keeps the id, timestamp, features used, score, model version and, once it arrives, the label. D6 checks the
monitoring is declared, not that an alert fires.

## Traceability and reproducibility (D7, D8, D9)

The train pipeline writes `.specs/prod/trace.json`:

```json
{
  "model": {"name": "main.churn_dev.churn_30d", "version": 3, "alias": "challenger"},
  "git_commit": "a1b2c3d",
  "config_env": "dev",
  "data": [{"table": "main.crm.accounts", "version": 12}],
  "mlflow_run_id": "...",
  "experiment": {"round": "churn", "id": "dfdee50fa862a2c3", "valid_metric": 0.571},
  "reproducibility": {"metric": "pr_auc", "prod_valid_metric": 0.569, "tolerance": 0.01,
                      "seed": 42, "lockfile": "uv.lock", "lockfile_sha256": "<sha256 of uv.lock>"},
  "metrics": {"valid": 0.569, "oot": 0.480}
}
```

- **D7**: the source round `.specs/features/<round>/` has a `verification.md` with `PASS`, and `experiment.id`
  is the `best` of its `ledger.json`; `|prod_valid_metric - experiment.valid_metric| <= tolerance` (> 0), on
  the same valid window of `.specs/split.lock`.
- **D9**: `lockfile_sha256` is the hash of the committed lock file (`lockfile`, `uv.lock` by default); the
  seed is recorded.
- **D8**: every table read is listed with its version; `MODEL_CARD.md` carries the model and version, the
  commit, the run, the round and every table with its version, plus Intended use, Limitations and Monitoring.

On Databricks, the version of a Delta table read: `spark.sql(f"DESCRIBE HISTORY {t} LIMIT 1").first()["version"]`,
recorded before reading; or read with `VERSION AS OF` to pin it.
