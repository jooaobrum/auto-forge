---
name: ml-mlflow-log
description: Use when a lane reaches its work or verify load point on a project that logs to MLflow - an example domain skill for logging runs and evals and turning them into Results files, with what each trace read and cited. Replace the experiment names and metric keys with your own.
---

# ML: MLflow logging (example)

An example of a team's tracking skill. Load points: **work** (log every run), **verify** (read runs into
Results files).

- **Log.** One MLflow run per Case and repeat, tagged `experiment_slug`, `variant`, `case`, `seed`. Log the
  metrics the spec's `## Metrics` names, with the same keys.
- **Traces.** Agent runs go through `mlflow.langchain.autolog()`; each trace carries the turn's spans. The
  records a turn **read** are the ids in the outputs of retrieval tool spans; the records it **cited** are
  the ids in the final answer.
- **Results file.** Write `{"runs":[{"case","run","metrics","touched","trace","read","cited"}]}` from
  `mlflow.search_runs(filter_string="tags.experiment_slug = '<slug>' and tags.variant = '<v>'")`;
  `touched` lists the tool and skill span names (`tool:<name>`, `skill:<name>`), `trace` the trace id.
- **Hygiene.** The holdout or eval set is frozen for the Experiment; no row of it reaches training or
  prompt examples; seeds are fixed and logged.
