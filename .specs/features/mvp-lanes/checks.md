# MVP lanes - checks

Mutations: 3
Build: `uv run ruff check src tests`
Plan: `.specs/features/mvp-lanes/plan.md`

## Intent

36 checks in 8 slices · 6 one-way doors · 0 open

## Checks

### S1 - Shape ends in a Brief that says what is not ready

**C1** - `rl brief` exits `2` naming each of a missing goal, Profile and lane (AC 1)
Proof: `uv run pytest tests/test_brief.py::test_missing_fields_are_named`

**C2** - All `ready` → `0`; one `needs attention` → `0` with a warning naming it; one `not ready` → `2` naming it (AC 2)
Proof: `uv run pytest tests/test_brief.py::test_readiness_levels`

**C3** - A research Brief whose metrics are not declared for its Profile in `lanes.json` exits `2` (AC 3)
Proof: `uv run pytest tests/test_brief.py::test_research_brief_needs_declared_metric`

### S2 - A pipeline is proven by its data contract

**C4** - `contract.sql` returns one `(case, violations)` row per rule with ids `orders.order_id.required`, `orders.order_id.unique`, `orders.rowCount` (AC 4)
Proof: `uv run pytest tests/test_contract.py::test_case_ids`

**C5** - On SQLite: 2 null `order_id` → `2`; `rowCount [1, 100]` with 0 rows → `1`, with 50 → `0`; freshness 24h with newest row 25h old → `1` (AC 5)
Proof: `uv run pytest tests/test_contract.py::test_violation_counts_on_sqlite`

**C6** - `unique`, `nullValues`, `invalidValues`, `duplicateValues` and `sql` rules each count exactly the rows breaking them on SQLite (AC 5)
Proof: `uv run pytest tests/test_contract.py::test_every_rule_kind_counts`

**C7** - A rule outside the subset exits `2` naming it and writes no `contract.sql` (AC 6)
Proof: `uv run pytest tests/test_contract.py::test_unknown_rule_is_refused`

**C8** - The pipeline gate exits `1` naming every contract Case above `0` and every missing golden row, and `0` when all are `0` (AC 7)
Proof: `uv run pytest tests/test_gate_build.py::test_pipeline_gate`

**C9** - Golden rows compile into Cases `<dataset>.golden.<n>` whose violations are `1` when the row is absent and `0` when present (AC 7)
Proof: `uv run pytest tests/test_contract.py::test_golden_rows_compile_to_cases`

### S3 - A behavior change is judged per Case against a Baseline

**C10** - `rl select` puts listed Cases in Target with `k.target`, touched-in-scope in Affected with `k.affected`, the rest in Stable with `0`; a Case both listed and touched is Target once (AC 8)
Proof: `uv run pytest tests/test_select.py::test_tiers`

**C11** - An Edit Scope path of an `affects_all` item puts every non-Target Case in Affected (AC 9)
Proof: `uv run pytest tests/test_select.py::test_affects_all`

**C12** - A Baseline recorded under a different content hash of its touched paths at the frozen commit is listed as stale; an unchanged one is not (AC 10)
Proof: `uv run pytest tests/test_select.py::test_stale_baseline`

**C13** - A run passes only if every `pass_at` metric meets it; 2 of 3 → passed, 1 of 3 → failed, 1 of 1 → passed, 1 of 2 → failed (AC 11)
Proof: `uv run pytest tests/test_gate.py::test_majority_rule`

**C14** - A Case that passed its Baseline and fails in the variant makes `rl gate` exit `1` naming it (AC 12)
Proof: `uv run pytest tests/test_gate.py::test_regression_is_named`

**C15** - Baseline 50,000 input tokens with budget 15: 57,500 passes, 57,501 fails naming Case and metric, +100k fails (AC 13)
Proof: `uv run pytest tests/test_gate.py::test_guardrail_budget_boundary`

**C16** - The gate exits `1` unless the Target Metric's mean over Target Cases rose by at least `min_delta`; exactly `min_delta` passes (AC 14)
Proof: `uv run pytest tests/test_gate.py::test_target_must_improve`

**C17** - A selected Case with fewer runs than its k makes the gate exit `1` naming the Case and the runs missing (AC 15)
Proof: `uv run pytest tests/test_gate.py::test_missing_runs_fail`

**C18** - `--confirm` exits `1` naming each Stable Case with no run, and `0` once each has one (AC 16)
Proof: `uv run pytest tests/test_gate.py::test_confirm_requires_stable`

**C19** - `results.md` holds one row per judged Case with Baseline status, variant status, Target before/after and each Guardrail before/after (AC 17)
Proof: `uv run pytest tests/test_gate.py::test_results_table`

**C20** - `--regression-only` passes a run with no Target improvement and still fails on a regression, a guardrail breach, a missing run and an out-of-scope edit (AC 18)
Proof: `uv run pytest tests/test_gate.py::test_regression_only`

### S4 - Edit Scope enforced by the diff

**C21** - An in-scope edit gives no finding; a changed `tools/sql.py` and a new untracked file outside scope are each listed and the gate exits `1`; files under `.lanes/work/<slug>/` and `.lanes/baseline/` are ignored (AC 19)
Proof: `uv run pytest tests/test_scope.py::test_outside_scope_is_named`

**C22** - With no `edit_scope` in `experiment.json` the Profile's `default_edit_scope` decides (AC 20)
Proof: `uv run pytest tests/test_scope.py::test_default_edit_scope`

### S5 - The budget stops the loop and the user decides

**C23** - Summed `input_tokens` reaching `budget_tokens` makes `rl budget` and `rl select` exit `4` printing the spend and "ask the user"; one token below exits `0` (AC 21)
Proof: `uv run pytest tests/test_budget.py::test_budget_spent_exits_4`

**C24** - `rl budget --add N --user "<words>"` raises the budget by N and appends N, the date and the quote to `budget.md`, keeping earlier lines (AC 22)
Proof: `uv run pytest tests/test_budget.py::test_add_records_user_words`

**C25** - `rl budget --add` with no `--user` exits `2` and leaves the budget unchanged (AC 23)
Proof: `uv run pytest tests/test_budget.py::test_add_without_user_is_refused`

**C26** - With `max_variants` variants already run, `rl select --variant <new>` exits `3` (AC 24)
Proof: `uv run pytest tests/test_select.py::test_variant_cap`

### S6 - Delivery closes the goal

**C27** - `rl deliver` exits `2` when the last gate failed or never ran, and `0` for an Experiment ending in `reject` after a failed gate (AC 25)
Proof: `uv run pytest tests/test_deliver.py::test_deliver_requires_green_gate`

**C28** - `delivery.md` holds the Brief's goal, the last gate command, its verdict table and the commits since freeze (AC 26)
Proof: `uv run pytest tests/test_deliver.py::test_delivery_contents`

**C29** - `--decision promote` writes `.lanes/work/<slug>-build/brief.md` with lane `build`, the Failure Mode, the Target Cases and the gate command (AC 27)
Proof: `uv run pytest tests/test_deliver.py::test_promote_writes_build_brief`

### S7 - Apps reuse their own e2e suite

**C30** - A JUnit file with a failure and an error exits `1` naming both; all passed exits `0`; zero tests exits `1` (AC 28)
Proof: `uv run pytest tests/test_gate_build.py::test_junit_gate`

### S8 - Every Profile end to end on local engines

**C31** - `examples/run_all.sh` takes `app`, `pipeline`, `model` and `agent` from `brief.md` to `delivery.md` with exit `0` (AC 29)
Proof: `uv run pytest tests/test_examples.py::test_run_all`

**C32** - The agent example's seeded regression variant makes `rl gate` exit `1` naming the regressed Case and `input_tokens` (AC 30)
Proof: `uv run pytest tests/test_examples.py::test_agent_regression_is_named`

### Cross-cutting

**C33** - `rl freeze` exits `2` when the plan has no `**Approved**:` line or the folder is not a git repo, and records the start commit otherwise (AC 25)
Proof: `uv run pytest tests/test_freeze.py::test_freeze_requires_approval`

**C34** - `skills/shape/SKILL.md` and `skills/lanes/SKILL.md` carry Agent Skills frontmatter (`name`, `description`) and name every CLI command they rely on (AC 29)
Proof: `uv run pytest tests/test_skills.py::test_skills_frontmatter_and_commands`

**C35** - A Results file that is not valid JSON, CSV or JUnit makes `rl gate` exit `2` naming the file (AC 15)
Proof: `uv run pytest tests/test_gate.py::test_malformed_results_file_exits_2`

**C36** - Selecting the same variant name twice does not count as a new variant toward the cap (AC 24)
Proof: `uv run pytest tests/test_select.py::test_reselect_same_variant`

## Coverage

| Set (size) | Member -> proof | Unproven |
| --- | --- | --- |
| CLI exit codes, door 5 (5) | `0` C2 · `1` C14 · `2` C1 · `3` C26 · `4` C23 | - |
| CLI commands, door 5 (8) | `brief` C1 · `freeze` C33 · `baseline` C12 · `select` C10 · `contract` C4 · `gate` C14 · `budget` C24 · `deliver` C28 | - |
| Results file formats, door 1 (3) | JSON C14 · CSV C8 · JUnit C30 | - |
| contract rules, door 6 (8) | `required` C5 · `unique` C6 · `rowCount` C5 · `nullValues` C6 · `invalidValues` C6 · `duplicateValues` C6 · `freshness` C5 · `sql` C6 | - |
| `lanes.json` keys, door 2 (9) | `profiles.lane` C3 · `profiles.metrics` C3 · `pass_at` C13 · `budget_pct` C15 · `surface.paths` C10 · `affects_all` C11 · `default_edit_scope` C22 · `k` C10 · `max_variants` C26 · `budget_tokens` C23 | - |
| work folder files, door 3 (10) | `brief.md` C1 · `experiment.json` C10 · `frozen.json` C33 · `selection.json` C10 · `contract.sql` C4 · `runs/` C14 · `results.md` C19 · `budget.md` C24 · `delivery.md` C28 · `.lanes/baseline/` C12 | - |
| instructions, door 4 (2) | `skills/shape/SKILL.md` C34 · `skills/lanes/SKILL.md` C34 | - |
| Profiles (4) | `app` C31 · `pipeline` C31 · `model` C31 · `agent` C31, C32 | - |
| Readiness levels (3) | `ready` C2 · `needs attention` C2 · `not ready` C2 | - |
| Case tiers (3) | Target C10 · Affected C10, C11 · Stable C10, C18 | - |
| AC 5 examples (4) | 2 nulls C5 · 0 rows C5 · 50 rows C5 · 25h old C5 | - |
| AC 8 examples (3) | q07 Affected C10 · q09 Stable C10 · listed and touched C10 | - |
| AC 11 examples (4) | 2/3 C13 · 1/3 C13 · 1/1 C13 · 1/2 C13 | - |
| AC 13 examples (3) | 57,500 C15 · 57,501 C15 · +100k C15 | - |
| AC 19 examples (3) | in scope C21 · `tools/sql.py` C21 · untracked C21 | - |
| Decisions (3) | adopt C28 · promote C29 · reject C27 | - |
| gate checks skipped or kept by `--regression-only` (5) | target skipped C20 · regression C20 · guardrail C20 · missing run C20 · scope C20 | - |

- No check claims more than the cases its proof exercises; C31 is the end-to-end path and each rule also has its own test

## Swept

- validation: C1, C7, C25, C35
- failure modes: C17, C35
- idempotency: C36
- authorization: n/a - a local CLI over the user's own git checkout; access is the repo's
- concurrency: n/a - one agent works one work folder; two agents on one slug is out of the model
- data lifecycle: C24
- dependency failure: C33
- state transitions: C27, C33
- observability: C19

## Handoff

- **Settled mid-build:** none
- **Dispatched:** none
- **Boundary:** none yet
- **Abandoned:** none
