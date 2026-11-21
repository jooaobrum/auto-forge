import pytest
from conftest import RESEARCH_BRIEF

BUILD_BRIEF = """# Orders pipeline

**Profile**: pipeline
**Lane**: build

## Goal

Orders land deduplicated.

## Readiness

| Item | State | Why |
| --- | --- | --- |
{rows}
"""


def test_missing_fields_are_named(host):
    host.write(".lanes/work/w/brief.md", "# Nothing\n\n## Readiness\n")
    code, out = host.rl("brief", "w")
    assert code == 2
    assert "missing: goal" in out
    assert "missing: profile" in out
    assert "missing: lane" in out


def test_missing_profile_only_is_named_alone(host):
    host.write(".lanes/work/w/brief.md", BUILD_BRIEF.format(rows="").replace("**Profile**: pipeline\n", ""))
    code, out = host.rl("brief", "w")
    assert code == 2
    assert "missing: profile" in out
    assert "missing: goal" not in out and "missing: lane" not in out


@pytest.mark.parametrize(
    "rows, expected_code, expected, absent",
    [
        ("| Fixture | ready | small |\n| Contract | ready | drafted |", 0, [], ["WARN", "ERROR"]),
        ("| Fixture | ready | small |\n| Golden rows | needs attention | only 2 |", 0,
         ["WARN  needs attention: Golden rows"], ["ERROR"]),
        ("| Fixture | not ready | no sample yet |\n| Contract | ready | drafted |", 2,
         ["ERROR not ready: Fixture"], []),
    ],
    ids=["all-ready", "needs-attention", "not-ready"],
)
def test_readiness_levels(host, rows, expected_code, expected, absent):
    host.write(".lanes/work/w/brief.md", BUILD_BRIEF.format(rows=rows))
    code, out = host.rl("brief", "w")
    assert code == expected_code
    for text in expected:
        assert text in out
    for text in absent:
        assert text not in out


def test_research_brief_needs_declared_metric(host):
    host.write(".lanes/work/w/brief.md", RESEARCH_BRIEF.replace("- cited_recall", "- bleu"))
    code, out = host.rl("brief", "w")
    assert code == 2
    assert "research lane needs a metric declared for profile `agent`" in out
    host.write(".lanes/work/w/brief.md", RESEARCH_BRIEF.replace("- cited_recall", "- bleu\n- cited_recall"))
    code, out = host.rl("brief", "w")
    assert code == 0, out
