from __future__ import annotations

import json
import re

from conftest import LAB, SKILLS

ROUTER = (SKILLS / "agent-spec-router" / "SKILL.md").read_text()

PROBLEM = """
## Problem

**Target**: a customer churns: cancels or stops paying within 30 days of the prediction
**Label rule**: `churned = 1` when the account is cancelled or unpaid in the 30 days after the prediction time
**Prediction time**: the first day of each month, with data up to the day before
**Exclusions**: accounts younger than 30 days; internal test accounts
**Cost of FP**: a retention call to a customer who would stay, about 5 dollars
**Cost of FN**: a lost customer, about 300 dollars of margin
**Metric**: pr_auc
**Label check**: `.specs/label_check.json`
**Confirmed**: 2026-11-21 - user: "yes, that is churn"

```sql
SELECT count(*) AS rows, sum(CASE WHEN rule_label = churned THEN 0 ELSE 1 END) AS mismatches FROM main.crm.accounts
```
"""


def problem_host(host, problem: str = PROBLEM, check: dict | None = None):
    host.write(".specs/LAB.md", LAB + problem)
    host.write(".specs/label_check.json", json.dumps(check if check is not None else {"rows": 1200, "mismatches": 0}))


def test_problem_passes_when_complete_confirmed_and_reproduced(host):
    problem_host(host)
    code, out = host.route("problem")
    assert code == 0, out
    assert "problem: pass" in out and "WARN" not in out


def test_problem_without_lab_or_section_is_invalid(host):
    (host.root / ".specs/LAB.md").unlink()
    code, out = host.route("problem")
    assert code == 2 and ".specs/LAB.md is missing" in out
    host.write(".specs/LAB.md", LAB)
    code, out = host.route("problem")
    assert code == 2 and "no ## Problem section" in out


def test_each_fact_and_the_confirmation_are_required(host):
    for name in ("Target", "Label rule", "Prediction time", "Cost of FP", "Cost of FN", "Metric"):
        problem_host(host, re.sub(rf"(?m)^\*\*{re.escape(name)}\*\*:.*$", f"**{name}**: <fill>", PROBLEM))
        code, out = host.route("problem")
        assert code == 1 and f"FAIL **{name}**: missing or not filled" in out, name
    problem_host(host, PROBLEM.replace("**Metric**: pr_auc", "**Metric**: vibes"))
    code, out = host.route("problem")
    assert code == 1 and "**Metric**: vibes is not one of" in out
    problem_host(host, PROBLEM.replace('2026-11-21 - user: "yes, that is churn"', "later"))
    code, out = host.route("problem")
    assert code == 1 and "**Confirmed**" in out


def test_the_label_rule_must_reproduce_the_label(host):
    problem_host(host, check={"rows": 1200, "mismatches": 7})
    code, out = host.route("problem")
    assert code == 1 and "disagrees with the stored label on 7 of 1200 rows" in out
    problem_host(host, check={"rows": 0, "mismatches": 0})
    code, out = host.route("problem")
    assert code == 1 and "ran on no rows" in out
    problem_host(host)
    (host.root / ".specs/label_check.json").unlink()
    code, out = host.route("problem")
    assert code == 1 and ".specs/label_check.json is missing" in out
    problem_host(host, PROBLEM.split("```sql")[0])
    code, out = host.route("problem")
    assert code == 1 and "no ```sql block" in out
    host.write(".specs/label_check.json", "not json")
    problem_host(host, PROBLEM.replace(".specs/label_check.json", ".specs/check.csv"))
    host.write(".specs/check.csv", "rows,mismatches\n50,0\n")
    assert host.route("problem")[0] == 0


def test_missing_exclusions_only_warns(host):
    problem_host(host, re.sub(r"(?m)^\*\*Exclusions\*\*:.*\n", "", PROBLEM))
    code, out = host.route("problem")
    assert code == 0 and "WARN **Exclusions**: missing" in out


def test_router_template_holds_the_problem():
    template = re.search(r"````markdown\n(.*?)\n````", ROUTER, re.DOTALL).group(1)
    body = template.split("## Problem")[1]
    for name in ("Target", "Label rule", "Prediction time", "Exclusions", "Cost of FP", "Cost of FN", "Metric",
                 "Label check", "Confirmed"):
        assert f"**{name}**:" in body, name
    assert "```sql" in body
    assert "route.py problem" in ROUTER and "references/problem.md" in ROUTER
    assert (SKILLS / "agent-spec-router" / "references" / "problem.md").exists()
