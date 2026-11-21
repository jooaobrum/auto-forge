BRIEF = """# {title}

**Profile**: {profile}
**Lane**: build
**Plan**: .specs/plan.md

## Goal

{title} works end to end.
"""


def frozen_build(host, profile: str, slug: str) -> None:
    host.write(f".lanes/work/{slug}/brief.md", BRIEF.format(title=slug, profile=profile))
    host.write(".specs/plan.md", "# Plan\n\n**Approved**: 2026-11-21 - user: \"go\"\n")
    host.commit("plan")
    code, out = host.rl("freeze", slug)
    assert code == 0, out


def test_pipeline_gate(host):
    frozen_build(host, "pipeline", "p")
    host.write_json(".lanes/work/p/contract.json",
                    {"cases": ["orders.order_id.required", "orders.rowCount", "orders.golden.1", "orders.golden.2"]})
    host.write(".lanes/work/p/runs/main/contract.csv",
               "case,violations\norders.order_id.required,2\norders.rowCount,0\n"
               "orders.golden.1,0\norders.golden.2,1\n")
    code, out = host.rl("gate", "p")
    assert code == 1
    assert "FAIL orders.order_id.required: 2 violations" in out
    assert "FAIL orders.golden.2: golden row missing" in out
    assert "FAIL orders.rowCount" not in out and "FAIL orders.golden.1" not in out
    host.write(".lanes/work/p/runs/main/contract.csv",
               "case,violations\norders.order_id.required,0\norders.rowCount,0\n"
               "orders.golden.1,0\norders.golden.2,0\n")
    code, out = host.rl("gate", "p")
    assert code == 0, out


def test_pipeline_gate_fails_on_a_case_with_no_result(host):
    frozen_build(host, "pipeline", "p")
    host.write_json(".lanes/work/p/contract.json", {"cases": ["orders.rowCount", "orders.freshness"]})
    host.write(".lanes/work/p/runs/main/contract.csv", "case,violations\norders.rowCount,0\n")
    code, out = host.rl("gate", "p")
    assert code == 1
    assert "orders.freshness: no result" in out


JUNIT = """<?xml version="1.0"?>
<testsuites><testsuite name="e2e">
{cases}
</testsuite></testsuites>
"""


def test_junit_gate(host):
    frozen_build(host, "app", "a")
    cases = ('<testcase classname="e2e" name="login"/>'
             '<testcase classname="e2e" name="checkout"><failure message="x"/></testcase>'
             '<testcase classname="e2e" name="search"><error message="boom"/></testcase>')
    host.write(".lanes/work/a/runs/main/junit.xml", JUNIT.format(cases=cases))
    code, out = host.rl("gate", "a")
    assert code == 1
    assert "FAIL e2e.checkout: failed" in out
    assert "FAIL e2e.search: failed" in out
    assert "e2e.login" not in out
    host.write(".lanes/work/a/runs/main/junit.xml", JUNIT.format(cases='<testcase classname="e2e" name="login"/>'))
    code, out = host.rl("gate", "a")
    assert code == 0, out
    skipped = '<testcase classname="e2e" name="later"><skipped/></testcase>'
    host.write(".lanes/work/a/runs/main/junit.xml", JUNIT.format(cases=skipped))
    code, out = host.rl("gate", "a")
    assert code == 1
    assert "no test ran" in out and "e2e.later" not in out
    host.write(".lanes/work/a/runs/main/junit.xml", JUNIT.format(cases=""))
    code, out = host.rl("gate", "a")
    assert code == 1
    assert "no test ran" in out
