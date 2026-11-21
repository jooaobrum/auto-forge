# v2-agent-spec-skills proofs

**HEAD**: 25b2099
**Tree**: clean
**Result**: 32 pass, 0 fail; mutations 0 killed, 0 not

| Check | Proof | Ran | Passed | Result |
| --- | --- | --- | --- | --- |
| C1 | `uv run pytest tests/test_router.py::test_router_routes_by_the_proof` | 1 | 1 | pass |
| C2 | `uv run pytest tests/test_router.py::test_router_grills_when_not_actionable` | 1 | 1 | pass |
| C3 | `uv run pytest tests/test_router.py::test_router_reroutes_promote` | 1 | 1 | pass |
| C4 | `uv run pytest tests/test_router.py::test_router_writes_lab_once` | 1 | 1 | pass |
| C5 | `uv run pytest tests/test_spec.py::test_spec_metrics_override_lab` | 1 | 1 | pass |
| C6 | `uv run pytest tests/test_spec.py::test_defaults` | 1 | 1 | pass |
| C7 | `uv run pytest tests/test_spec.py::test_freeze_refuses_incomplete_spec` | 1 | 1 | pass |
| C8 | `uv run pytest tests/test_spec.py::test_cases_columns_adapt` | 1 | 1 | pass |
| C9 | `uv run pytest tests/test_spec.py::test_cases_or_dataset` | 1 | 1 | pass |
| C10 | `uv run pytest tests/test_gate.py::test_regression_tier_is_pass_hat_k` | 2 | 2 | pass |
| C11 | `uv run pytest tests/test_gate.py::test_capability_tier_is_majority` | 4 | 4 | pass |
| C12 | `uv run pytest tests/test_gate.py::test_regression_is_named` | 1 | 1 | pass |
| C13 | `uv run pytest tests/test_gate.py::test_guardrail_budget_boundary` | 3 | 3 | pass |
| C14 | `uv run pytest tests/test_gate.py::test_target_mean_over_target_cases` | 3 | 3 | pass |
| C15 | `uv run pytest tests/test_gate.py::test_missing_runs_and_confirm` | 1 | 1 | pass |
| C16 | `uv run pytest tests/test_gate.py::test_regression_only` | 1 | 1 | pass |
| C17 | `uv run pytest tests/test_gate.py::test_edit_scope` | 1 | 1 | pass |
| C18 | `uv run pytest tests/test_deliver.py::test_graduation_streak` | 1 | 1 | pass |
| C19 | `uv run pytest tests/test_deliver.py::test_deliver_rules_and_promote` | 1 | 1 | pass |
| C20 | `uv run pytest tests/test_budget.py::test_budget_stop_and_add` | 1 | 1 | pass |
| C21 | `uv run pytest tests/test_contract.py::test_spec_contract_compiles_and_counts` | 1 | 1 | pass |
| C22 | `uv run pytest tests/test_contract.py::test_golden_rows` | 1 | 1 | pass |
| C23 | `uv run pytest tests/test_contract.py::test_odcs_fallback_and_unknown_rule` | 1 | 1 | pass |
| C24 | `uv run pytest tests/test_contract.py::test_contract_gate` | 1 | 1 | pass |
| C25 | `uv run pytest tests/test_skills.py::test_load_points_and_domain_skills` | 1 | 1 | pass |
| C26 | `uv run pytest tests/test_skills.py::test_skill_frontmatter_and_shared_parser` | 1 | 1 | pass |
| C27 | `uv run pytest tests/test_examples.py::test_run_all` | 1 | 1 | pass |
| C27 | `uv run pytest tests/test_examples.py::test_agent_regression_is_named` | 1 | 1 | pass |
| C28 | `uv run pytest tests/test_lean.py::test_agent_spec_lean_selftest` | 1 | 1 | pass |
| C29 | `uv run pytest tests/test_packaging.py::test_plugin_manifests_and_marketplace` | 1 | 1 | pass |
| C30 | `uv run pytest tests/test_router.py::test_route_freeze_junit_deliver` | 1 | 1 | pass |
| Build | `uv run ruff check skills tests` | - | - | pass |
