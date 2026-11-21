# v2: agent-spec skills - checks

Mutations: 3
Build: `uv run ruff check skills tests`
Plan: `.specs/features/v2-agent-spec-skills/plan.md`

## Intent

31 checks in 7 slices · 9 one-way doors · 0 open

## Checks

### S1 - The router is the one entry

**C1** - The router's description starts "Use first", names `agent-spec-lean`, `agent-spec-pipeline` and `agent-spec-experiment`, and its body routes an end-to-end proof to build and a rate over a dataset to research (AC 1)
Proof: `uv run pytest tests/test_router.py::test_router_routes_by_the_proof`

**C2** - The router's body calls `agent-spec-grilling` when the context names no goal or no way to prove it, before routing (AC 2)
Proof: `uv run pytest tests/test_router.py::test_router_grills_when_not_actionable`

**C3** - The router's body takes a `promote` Decision back and routes its brief to the build lane (AC 3)
Proof: `uv run pytest tests/test_router.py::test_router_reroutes_promote`

**C4** - The router's body writes `.specs/LAB.md` on a project without one, naming the eval command, results glue, metrics, surface map and domain skills per load point, each confirmed with the user (AC 4)
Proof: `uv run pytest tests/test_router.py::test_router_writes_lab_once`

### S2 - A spec from context, with defaults

**C5** - With no `## Metrics` in the spec the LAB table is used; a spec row overrides the LAB row of the same metric, cell by cell (AC 5)
Proof: `uv run pytest tests/test_spec.py::test_spec_metrics_override_lab`

**C6** - With no `**Variants**:`, k or guardrail values: 3 variants, k 3/1/1, `input_tokens` +15% and `latency_ms` +20% when those metrics are listed, and no guardrail for a metric that is not (AC 6)
Proof: `uv run pytest tests/test_spec.py::test_defaults`

**C7** - `freeze` exits `2` naming the missing `**Approved**:` line, the missing Cases, a Target case absent from the Cases table, or a Target Metric absent from the merged metrics (AC 7)
Proof: `uv run pytest tests/test_spec.py::test_freeze_refuses_incomplete_spec`

**C8** - A Cases table with only `Case`, `Question`, `Rubric` is accepted; with `Cite` the cited recall is graded from the run's `cited` ids; an empty `Cite` cell is not graded (AC 8)
Proof: `uv run pytest tests/test_spec.py::test_cases_columns_adapt`
Proof: `uv run pytest tests/test_spec.py::test_read_column_and_failure_mode_targets`
Proof: `uv run pytest tests/test_spec.py::test_route_column_is_graded_when_present`
Proof: `uv run pytest tests/test_spec.py::test_only_the_first_table_of_a_section_is_read`

**C9** - A spec with neither `## Cases` nor `**Dataset**:` exits `2`; with only `**Dataset**:` it freezes (AC 9)
Proof: `uv run pytest tests/test_spec.py::test_cases_or_dataset`

### S3 - The experiment gate

**C10** - A `regression` Case passes only when every run passes: 3 of 3 → passed, 2 of 3 → failed (AC 10)
Proof: `uv run pytest tests/test_gate.py::test_regression_tier_is_pass_hat_k`

**C11** - A `capability` Case, or one with no tier, passes on a majority: 2 of 3 → passed, 1 of 2 → failed (AC 11)
Proof: `uv run pytest tests/test_gate.py::test_capability_tier_is_majority`

**C12** - A Case that passed its Baseline and fails now is named and the gate exits `1` (AC 12)
Proof: `uv run pytest tests/test_gate.py::test_regression_is_named`

**C13** - Guardrail per Case: Baseline 50,000 input tokens at +15% → 57,500 passes, 57,501 fails naming Case and metric (AC 12)
Proof: `uv run pytest tests/test_gate.py::test_guardrail_budget_boundary`

**C14** - The Target Metric's mean over two Target Cases must rise by at least the Target delta; exactly the delta passes (AC 12)
Proof: `uv run pytest tests/test_gate.py::test_target_mean_over_target_cases`

**C15** - A selected Case with fewer runs than its k fails naming the runs missing; `--confirm` requires one run per Stable Case (AC 12)
Proof: `uv run pytest tests/test_gate.py::test_missing_runs_and_confirm`

**C16** - `--regression-only` skips the Target and still fails on a regression, a guardrail, a missing run and an out-of-scope edit (AC 12)
Proof: `uv run pytest tests/test_gate.py::test_regression_only`

**C17** - The Edit Scope check lists a changed file, an untracked file, both sides of a rename and a path with a space; files under the work folder and `.specs/baseline/` are ignored, another slug's folder is not (AC 12)
Proof: `uv run pytest tests/test_gate.py::test_edit_scope`

**C18** - `deliver --decision adopt` raises the streak of each passing capability Case, resets a failing one, and lists in `delivery.md` the Cases whose streak reached 3 (AC 13)
Proof: `uv run pytest tests/test_deliver.py::test_graduation_streak`
Proof: `uv run pytest tests/test_deliver.py::test_regression_cases_do_not_count_toward_graduation`

**C19** - `deliver` exits `2` with no gate, after a failed gate unless the Decision is `reject`, and for research with no Decision; `promote` writes `.specs/features/<slug>-build/spec.md` with lane `build` (AC 13)
Proof: `uv run pytest tests/test_deliver.py::test_deliver_rules_and_promote`

**C20** - Spent budget makes `select` and `budget` exit `4` with "ask the user"; `budget --add` records the user's words and refuses without them (AC 14)
Proof: `uv run pytest tests/test_budget.py::test_budget_stop_and_add`

### S4 - A pipeline proven by the contract in its spec

**C21** - The `## Data contract` section compiles to one query with cases `orders.order_id.required`, `orders.order_id.unique`, `orders.status.invalidValues`, `orders.rowCount`, `orders.freshness`, `orders.sql.<name>`, each counting exactly the breaking rows on SQLite, `rowCount` checked at 1, 100 and 101 rows (AC 15)
Proof: `uv run pytest tests/test_contract.py::test_spec_contract_compiles_and_counts`

**C22** - Golden rows become Cases `<dataset>.golden.<n>`, `0` when present and `1` when absent, `007` compared as text (AC 16)
Proof: `uv run pytest tests/test_contract.py::test_golden_rows`

**C23** - With no contract section an ODCS file under `contracts/` is read; with no `pyyaml` it exits `2` saying so; an unknown rule exits `2` naming it (AC 17)
Proof: `uv run pytest tests/test_contract.py::test_odcs_fallback_and_unknown_rule`

**C24** - `contract.py gate` exits `1` naming each Case above `0` and each missing golden row, `0` when all are `0`, and `1` for a Case with no result (AC 18)
Proof: `uv run pytest tests/test_contract.py::test_contract_gate`

### S5 - Domain skills at fixed load points

**C25** - `agent-spec-lean`, `agent-spec-pipeline` and `agent-spec-experiment` each name the load points plan, work and verify and read them from `.specs/LAB.md`; `data-databricks-sql` and `ml-mlflow-log` exist with "Use when" descriptions naming their load point (AC 19)
Proof: `uv run pytest tests/test_skills.py::test_load_points_and_domain_skills`

### S6 - Skills described and every example on the new shape

**C26** - Every skill's `name` equals its folder and its description contains "Use when" or "Use first"; every copy of `spec_md.py` is identical (AC 21)
Proof: `uv run pytest tests/test_skills.py::test_skill_frontmatter_and_shared_parser`

**C27** - `examples/run_all.sh` takes app, pipeline, model and agent from `spec.md` to `delivery.md` with exit `0`, and the agent's "read in full" variant fails naming `q02` regressed and its `input_tokens` guardrail; no example has `lanes.json` or calls `rl` (AC 22)
Proof: `uv run pytest tests/test_examples.py::test_run_all`
Proof: `uv run pytest tests/test_examples.py::test_agent_regression_is_named`

**C28** - `agent-spec-lean`'s `selftest.py` exits `0` after the rename and its files name no `tlc-spec-lean` path (AC 24)
Proof: `uv run pytest tests/test_lean.py::test_agent_spec_lean_selftest`

### S7 - Installable from anywhere

**C29** - `plugin.json` has the Agent Plugins 1.0 `$schema`, name `agent-spec` and the same semantic version as `.claude-plugin/plugin.json`; the marketplace lists `agent-spec` at `./`; every skill folder is kebab-case with a `SKILL.md` (AC 25)
Proof: `uv run pytest tests/test_packaging.py::test_plugin_manifests_and_marketplace`

**C30** - `route.py` freezes only an approved spec, judges JUnit (a failure named, skipped tests not counted, none run fails) and delivers only after a passing gate, with the goal, gate and commits (door 9)
Proof: `uv run pytest tests/test_router.py::test_route_freeze_junit_deliver`

**C31** - Each spec template, filled exactly as shown with only the approval written, freezes (agent, model) or compiles (pipeline) (AC 8)
Proof: `uv run pytest tests/test_templates.py::test_templates_freeze_and_compile_as_shown`

## Coverage

| Set (size) | Member -> proof | Unproven |
| --- | --- | --- |
| skills (8) | `agent-spec-router` C1 · `agent-spec-grilling` C26 · `agent-spec-writer` C26 · `agent-spec-lean` C28 · `agent-spec-pipeline` C25 · `agent-spec-experiment` C25 · `data-databricks-sql` C25 · `ml-mlflow-log` C25 | - |
| script exit codes, door 6 (5) | `0` C9 · `1` C12 · `2` C7 · `3` C20 · `4` C20 | - |
| experiment commands, door 6 (6) | `freeze` C7 · `baseline` C12 · `select` C15 · `gate` C12 · `budget` C20 · `deliver` C19 | - |
| contract commands, door 6 (2) | `compile` C21 · `gate` C24 | - |
| spec fields, door 7 (6) | `Profile` C7 · `Lane` C7 · `Approved` C7 · `Budget` C20 · `Variants` C6 · `Dataset` C9 | - |
| spec sections, door 7 (6) | `Cases` C8 · `Metrics` C5 · `Surface` C17 · `Data contract` C21 · `Golden rows` C22 · `Edit Scope` C17 | - |
| optional Case columns, AC 8 (5) | `Read` C8 · `Cite` C8 · `Route` C8 · `Failure mode` C8 · `Tier` C10 | - |
| contract rules (6) | `required` C21 · `unique` C21 · `accepted values` C21 · `rowCount` C21 · `freshness` C21 · `sql` C21 | - |
| tiers (2) | regression C10 · capability C11 | - |
| Decisions (3) | adopt C18 · promote C19 · reject C19 | - |
| Profiles in examples (4) | app C27 · pipeline C27 · model C27 · agent C27 | - |
| load points (3) | plan C25 · work C25 · verify C25 | - |

- C1-C4 and C25 are prose obligations of the skills; their proofs assert the text, and C27 runs the paths end to end

## Swept

- validation: C7, C9, C23
- failure modes: C15, C24
- idempotency: n/a - each script rewrites its own output files; reruns give the same result
- authorization: n/a - local scripts over the user's own checkout
- concurrency: n/a - one agent per work folder
- data lifecycle: C18, C20
- dependency failure: C23
- state transitions: C19
- observability: C15

## Handoff

- **Settled mid-build:** user: "can we format it to be available by github in case we clone (databricks can only close as entry point) and also available as a vscode agent plugin?" - added door 8, AC 25, C29 (AD-028)
- **Dispatched:** Verifier at `25b2099`
- **Boundary:** C1-C30 closed at `25b2099`
- **Abandoned:** none
