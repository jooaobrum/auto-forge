import re

from conftest import SKILLS

ROUTER = (SKILLS / "agent-spec-router" / "SKILL.md").read_text()
DESCRIPTION = re.search(r"^description:\s*(.+)$", ROUTER, re.MULTILINE).group(1)


def test_router_routes_by_the_proof():
    assert DESCRIPTION.startswith("Use first")
    for lane_skill in ("agent-spec-lean", "agent-spec-pipeline", "agent-spec-experiment"):
        assert lane_skill in DESCRIPTION
    body = ROUTER.split("## 3. Route by the proof")[1].split("## 4.")[0]
    assert "end-to-end test" in body and "**agent-spec-lean**" in body
    assert "data contract" in body and "**agent-spec-pipeline**" in body
    assert "rate over a dataset" in body and "**agent-spec-experiment**" in body


def test_router_grills_when_not_actionable():
    body = ROUTER.split("## 2. Is the context actionable?")[1].split("## 3.")[0]
    assert "no goal or no way to prove it" in body
    assert "**agent-spec-grilling** before routing" in body


def test_router_reroutes_promote():
    body = ROUTER.split("## 4. Take back a promote")[1]
    assert "`promote`" in body and "build lane" in body and "<slug>-build/spec.md" in body


def test_router_writes_lab_once():
    body = ROUTER.split("## 1. Know the project")[1].split("## 2.")[0]
    assert "When it does not exist, write it now" in body and "confirm each part with the user" in body
    for part in ("**Eval command**", "**Results glue**", "## Metrics", "## Surface", "## Domain skills"):
        assert part in body, part


def test_route_freeze_junit_deliver(host):
    host.write(".specs/features/a/spec.md", "# Sum\n\n**Profile**: app\n**Lane**: build\n\n## Goal\n\nA total.\n")
    host.commit()
    code, out = host.route("freeze", "a")
    assert code == 2 and "no **Approved**: line" in out
    host.write(".specs/features/a/spec.md", "# Sum\n\n**Profile**: app\n**Lane**: build\n"
               "**Approved**: 2026-11-22 - user: \"go\"\n\n## Goal\n\nA total.\n")
    assert host.route("freeze", "a")[0] == 0
    code, out = host.route("deliver", "a")
    assert code == 2 and "no gate has run" in out
    xml = ('<testsuites><testsuite>{}</testsuite></testsuites>')
    host.write(".specs/features/a/runs/main/e2e.xml", xml.format(
        '<testcase classname="e2e" name="sum"/><testcase classname="e2e" name="empty"><failure/></testcase>'
        '<testcase classname="e2e" name="later"><skipped/></testcase>'))
    code, out = host.route("junit", "a")
    assert code == 1 and "FAIL e2e.empty: failed" in out and "e2e.later" not in out
    host.write(".specs/features/a/runs/main/e2e.xml", xml.format('<testcase name="x"><skipped/></testcase>'))
    code, out = host.route("junit", "a")
    assert code == 1 and "no test ran" in out
    host.write(".specs/features/a/runs/main/e2e.xml", xml.format('<testcase classname="e2e" name="sum"/>'))
    assert host.route("junit", "a")[0] == 0
    host.write("app.py", "print(1)\n")
    host.commit("feat: sum")
    code, out = host.route("deliver", "a")
    assert code == 0, out
    text = (host.root / ".specs/features/a/delivery.md").read_text()
    assert "A total." in text and "route.py junit a" in text and "feat: sum" in text
