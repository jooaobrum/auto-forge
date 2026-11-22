import re
import subprocess

from conftest import ROOT, SKILLS

ROUTER = (SKILLS / "agent-spec-router" / "SKILL.md").read_text()
DESCRIPTION = re.search(r"^description:\s*(.+)$", ROUTER, re.MULTILINE).group(1)


def test_router_routes_by_the_proof():
    assert DESCRIPTION.startswith("Use first")
    for lane_skill in ("agent-spec-lean", "agent-spec-pipeline", "agent-spec-experiment", "agent-spec-modeling",
                       "agent-spec-mlops"):
        assert lane_skill in DESCRIPTION
    body = ROUTER.split("## 3. Route by the proof")[1].split("## 4.")[0]
    assert "end-to-end test" in body and "**agent-spec-lean**" in body
    assert "data contract" in body and "**agent-spec-pipeline**" in body
    assert "rate over a dataset" in body and "**agent-spec-experiment**" in body
    assert "no champion" in body and "**agent-spec-modeling**" in body
    assert "validate_prod.py" in body and "**agent-spec-mlops**" in body
    assert "Failure Mode of a model in production" in body


def test_router_grills_when_not_actionable():
    body = ROUTER.split("## 2. Is the context actionable?")[1].split("## 3.")[0]
    assert "no goal or no way to prove it" in body
    assert "**agent-spec-grilling** before routing" in body


def test_router_reroutes_promote():
    body = ROUTER.split("## 4. Take back a promote")[1]
    assert "`promote`" in body and "build lane" in body and "<slug>-build/plan.md" in body
    assert "<slug>-mlops/plan.md" in body and "**agent-spec-mlops**" in body


def test_router_writes_lab_once():
    body = ROUTER.split("## 1. Know the project")[1].split("## 2.")[0]
    assert "When it does not exist, write it now" in body and "confirm each part with the user" in body
    for part in ("**Eval command**", "**Results glue**", "## Metrics", "## Surface", "## Domain skills"):
        assert part in body, part


def test_route_freeze_junit_deliver(host):
    code, out = host.route("freeze", "a")
    assert code == 2 and "plan.md is missing" in out
    host.write(".specs/features/a/plan.md", "# Sum\n\n**Profile**: app\n**Lane**: build\n\n## Problem\n\nA total.\n")
    host.commit()
    code, out = host.route("freeze", "a")
    assert code == 2 and "no **Approved**: line" in out
    host.write(".specs/features/a/plan.md", "# Sum\n\n**Profile**: app\n**Lane**: build\n"
               "**Approved**: 2026-11-22 - user: \"go\"\n\n## Problem\n\nA total.\n")
    code, out = host.route("freeze", "a")
    assert code == 2 and "validate_plan.py" in out and "Shape" in out
    host.write(".specs/features/a/plan.md", (ROOT / "examples/app/host/.specs/features/sum/plan.md").read_text())
    code, out = host.route("freeze", "a")
    assert code == 0, out
    code, out = host.route("deliver", "a")
    assert code == 2 and "no gate has run" in out
    xml = ('<testsuites><testsuite>{}</testsuite></testsuites>')
    host.write(".specs/features/a/runs/main/e2e.xml", xml.format(
        '<testcase classname="e2e" name="sum"/><testcase classname="e2e" name="empty"><failure/></testcase>'
        '<testcase classname="e2e" name="later"><skipped/></testcase>'))
    code, out = host.route("junit", "a")
    assert code == 1 and "FAIL e2e.empty: failed" in out and "e2e.later" not in out
    code, out = host.route("deliver", "a")
    assert code == 2 and "the last gate failed" in out
    host.write(".specs/features/a/runs/main/e2e.xml", xml.format('<testcase name="x"><skipped/></testcase>'))
    code, out = host.route("junit", "a")
    assert code == 1 and "no test ran" in out
    host.write(".specs/features/a/runs/main/e2e.xml", xml.format('<testcase classname="e2e" name="sum"/>'))
    assert host.route("junit", "a")[0] == 0
    host.write("app.py", "print(1)\n")
    host.commit("feat: sum")
    code, out = host.route("deliver", "a")
    assert code == 2 and "not verified" in out and "no verification.md" in out
    lean_verified(host, "a")
    code, out = host.route("deliver", "a")
    assert code == 0, out
    text = (host.root / ".specs/features/a/delivery.md").read_text()
    assert "sees their total" in text and "route.py junit a" in text and "feat: sum" in text


def lean_verified(host, slug: str) -> None:
    """agent-spec-lean's evidence at HEAD: one check, its proof passing, the Verifier's report."""
    head = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=host.root, capture_output=True, check=True,
                          text=True).stdout.strip()
    folder = f".specs/features/{slug}"
    host.write(f"{folder}/checks.md", "# a - checks\n\nMutations: 0\nBuild: none - test\n\n## Checks\n\n"
               "**C1** - the total of 2 and 3 is 5\nProof: `true`\n")
    host.write(f"{folder}/proofs.md", f"# a proofs\n\n**HEAD**: {head}\n**Tree**: clean\n\n"
               "| Check | Proof | Ran | Passed | Result |\n| --- | --- | --- | --- | --- |\n| C1 | `true` | 1 | 1 | pass |\n")
    host.write(f"{folder}/verification.md", "# a verification\n\n**Verdict**: PASS\n"
               "**Verifier**: independent sub-agent (author != verifier)\n\n## Findings\n\nNone - probed C1\n")
