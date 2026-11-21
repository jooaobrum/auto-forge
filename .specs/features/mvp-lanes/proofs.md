# mvp-lanes proofs

**HEAD**: 927e3e0
**Tree**: clean
**Result**: 41 pass, 0 fail; mutations 3 killed, 0 not

| Check | Proof | Ran | Passed | Result |
| --- | --- | --- | --- | --- |
| C1 | `uv run pytest tests/test_brief.py::test_missing_fields_are_named` | 1 | 1 | pass |
| C2 | `uv run pytest tests/test_brief.py::test_readiness_levels` | 3 | 3 | pass |
| C3 | `uv run pytest tests/test_brief.py::test_research_brief_needs_declared_metric` | 1 | 1 | pass |
| C4 | `uv run pytest tests/test_contract.py::test_case_ids` | 1 | 1 | pass |
| C5 | `uv run pytest tests/test_contract.py::test_violation_counts_on_sqlite` | 1 | 1 | pass |
| C6 | `uv run pytest tests/test_contract.py::test_every_rule_kind_counts` | 1 | 1 | pass |
| C7 | `uv run pytest tests/test_contract.py::test_unknown_rule_is_refused` | 1 | 1 | pass |
| C8 | `uv run pytest tests/test_gate_build.py::test_pipeline_gate` | 1 | 1 | pass |
| C9 | `uv run pytest tests/test_contract.py::test_golden_rows_compile_to_cases` | 1 | 1 | pass |
| C10 | `uv run pytest tests/test_select.py::test_tiers` | 1 | 1 | pass |
| C11 | `uv run pytest tests/test_select.py::test_affects_all` | 1 | 1 | pass |
| C12 | `uv run pytest tests/test_select.py::test_stale_baseline` | 1 | 1 | pass |
| C12 | `uv run pytest tests/test_select.py::test_working_tree_edits_do_not_make_a_baseline_stale` | 1 | 1 | pass |
| C13 | `uv run pytest tests/test_gate.py::test_majority_rule` | 1 | 1 | pass |
| C14 | `uv run pytest tests/test_gate.py::test_regression_is_named` | 1 | 1 | pass |
| C15 | `uv run pytest tests/test_gate.py::test_guardrail_budget_boundary` | 3 | 3 | pass |
| C16 | `uv run pytest tests/test_gate.py::test_target_must_improve` | 3 | 3 | pass |
| C16 | `uv run pytest tests/test_gate.py::test_target_mean_over_several_cases` | 2 | 2 | pass |
| C17 | `uv run pytest tests/test_gate.py::test_missing_runs_fail` | 1 | 1 | pass |
| C18 | `uv run pytest tests/test_gate.py::test_confirm_requires_stable` | 1 | 1 | pass |
| C19 | `uv run pytest tests/test_gate.py::test_results_table` | 1 | 1 | pass |
| C20 | `uv run pytest tests/test_gate.py::test_regression_only` | 1 | 1 | pass |
| C21 | `uv run pytest tests/test_scope.py::test_outside_scope_is_named` | 1 | 1 | pass |
| C21 | `uv run pytest tests/test_scope.py::test_moving_a_file_into_scope_names_the_old_path` | 1 | 1 | pass |
| C22 | `uv run pytest tests/test_scope.py::test_default_edit_scope` | 1 | 1 | pass |
| C23 | `uv run pytest tests/test_budget.py::test_budget_spent_exits_4` | 1 | 1 | pass |
| C24 | `uv run pytest tests/test_budget.py::test_add_records_user_words` | 1 | 1 | pass |
| C25 | `uv run pytest tests/test_budget.py::test_add_without_user_is_refused` | 1 | 1 | pass |
| C26 | `uv run pytest tests/test_select.py::test_variant_cap` | 1 | 1 | pass |
| C27 | `uv run pytest tests/test_deliver.py::test_deliver_requires_green_gate` | 1 | 1 | pass |
| C28 | `uv run pytest tests/test_deliver.py::test_delivery_contents` | 1 | 1 | pass |
| C29 | `uv run pytest tests/test_deliver.py::test_promote_writes_build_brief` | 1 | 1 | pass |
| C30 | `uv run pytest tests/test_gate_build.py::test_junit_gate` | 1 | 1 | pass |
| C31 | `uv run pytest tests/test_examples.py::test_run_all` | 1 | 1 | pass |
| C32 | `uv run pytest tests/test_examples.py::test_agent_regression_is_named` | 1 | 1 | pass |
| C33 | `uv run pytest tests/test_freeze.py::test_freeze_requires_approval` | 1 | 1 | pass |
| C33 | `uv run pytest tests/test_freeze.py::test_freeze_outside_git_exits_2` | 1 | 1 | pass |
| C34 | `uv run pytest tests/test_skills.py::test_skills_frontmatter_and_commands` | 1 | 1 | pass |
| C35 | `uv run pytest tests/test_gate.py::test_malformed_results_file_exits_2` | 1 | 1 | pass |
| C36 | `uv run pytest tests/test_select.py::test_reselect_same_variant` | 1 | 1 | pass |
| Build | `uv run ruff check src tests` | - | - | pass |

## Mutations

| Mutation | Location | Killed |
| --- | --- | --- |
| rowCount upper bound shifted down by one (100 rows in [1, 100] fails) | `src/lanes/contract.py:87` | yes |
| a skipped JUnit test is counted as a passed run | `src/lanes/results.py:67` | yes |
| Edit Scope exempts every work folder, not only .lanes/work/<slug>/ | `src/lanes/gate.py:59` | yes |
