# Project state

## Decisions

| ID | Decision | Rationale | Status | Date |
| --- | --- | --- | --- | --- |
| AD-001 | Work goes to the build lane if an end-to-end test reproducing the user's behavior can prove it, and to the research lane if only a rate over a dataset can | user: "build if a end to end tests can prove it. This is very important. It should reproduce, as much as possible the user behavior." | active | 2026-11-21 |
| AD-002 | The harness depends on no single coding agent: instructions are markdown in the Agent Skills format, rules run in a stdlib Python CLI, and the Edit Scope is enforced by the gate's git diff check, not by hooks | user: "this should find a way to work on github copilot, databricks genie etc" | active | 2026-11-21 |
| AD-003 | Each host repo provides one Adapter command (`--cases --k --out`, JSON out); the harness owns process, selection, gates and records | asked Q19 "plugin owns the process, each repo provides a small adapter" - user: "ok" | superseded by AD-011 | 2026-11-21 |
| AD-004 | One Profile per kind (`app`, `pipeline`, `model`, `agent`) declares its default lane and plan obligations; the lane of each piece of work is still chosen by its proof; the repo is renamed `lanes` | asked Q21 - user: "yes" | active | 2026-11-21 |
| AD-005 | Data contracts are a subset of ODCS v3 (YAML); the harness takes one dependency, `pyyaml` | asked Q22 - user: "yes" | active | 2026-11-21 |
| AD-006 | The harness compiles each contract rule into a SQL query returning a violation count; each rule is a Case that passes at 0 violations or within its threshold | asked Q23 - user: "yes" | active | 2026-11-21 |
| AD-007 | A pipeline Build Change is proven by running the pipeline on a small versioned input fixture into a dev schema, then its output contract and golden rows | asked Q24 - user: "yes" | active | 2026-11-21 |
| AD-008 | For a model, a Case is a slice of the frozen holdout and k is the number of seeds; the gate is the same as for agents | asked Q25 - user: "yes" | active | 2026-11-21 |
| AD-009 | Apps add no new gate: the app Profile's proof is the host's own e2e command, judged by exit code | asked Q26 - user: "yes" | active | 2026-11-21 |
| AD-010 | MVP done = one worked example per kind in `examples/`, each from frozen plan to gate verdict on local engines; real hosts are later Build Changes in their repos | asked Q27 - user: "yes" | active | 2026-11-21 |
| AD-011 | The harness runs nothing: it writes `selection.json` and `contract.sql` and reads Results files (one JSON shape, or JUnit XML); the agent runs the host's own tools and keeps working until the goal is closed; AD-003's Adapter is dropped | asked Q28 "Drop the Adapter for a Results file" - user: "results file can replace it, but let the agent flow until it's a closed task/goal." | active | 2026-11-21 |
| AD-012 | When the token budget is spent the agent stops and asks the user whether to continue; the user's answer and the added budget are recorded | user: "token budget: user can choose if he wants to to continue when toekn budget is exhasusted" | active | 2026-11-21 |
| AD-013 | Every piece of work follows seven stages: shape (offline material + a short grilling, ending in a Brief with readiness), goal, plan, approve, work, verify (deterministic gate, rework on failure), deliver; the shape stage writes a host's Results-file glue script when one is needed | user: "Flow 1. Brainstrom offline ... + a small grilling session ... 2. goal defined 3. plan 4. approve 5. agent takes the task 6. agent auto verify deterministically ... (rebuild if need something) 7. Deliver" | active | 2026-11-21 |
