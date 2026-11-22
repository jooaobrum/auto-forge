import re

from conftest import ROOT, SKILLS, load

APPROVE = '**Approved**: 2026-11-22 - user: "go"'
lean_plan = load("agent-spec-lean", "validate_plan")


def blocks(path) -> list[str]:
    """The guide's plan blocks, with only the approval written and the Dataset placeholder dropped."""
    out = []
    for text in re.findall(r"`````markdown\n(.*?)\n`````", path.read_text(), re.DOTALL):
        text = re.sub(r"(?m)^\*\*Approved\*\*:.*$", APPROVE, text)
        out.append(re.sub(r"(?m)^\*\*Dataset\*\*:.*\n", "", text))
    return out


def test_every_lane_has_a_plan_guide_and_no_spec_template():
    for lane in ("agent-spec-lean", "agent-spec-pipeline", "agent-spec-experiment", "agent-spec-modeling",
                 "agent-spec-mlops"):
        assert (SKILLS / lane / "references" / "plan.md").exists(), lane
        assert not list((SKILLS / lane / "references").glob("spec-*.md")), lane
    writer = (SKILLS / "agent-spec-writer" / "SKILL.md").read_text()
    for lane in ("agent-spec-lean", "agent-spec-pipeline", "agent-spec-experiment", "agent-spec-modeling",
                 "agent-spec-mlops"):
        assert f"`{lane}/references/plan.md`" in writer, lane


def test_research_templates_freeze_as_shown(host):
    agent, model = blocks(SKILLS / "agent-spec-experiment" / "references" / "plan.md")
    for name, text in (("agent", agent), ("model", model)):
        host.spec(name, text=text)
        host.commit(name)
        code, out = host.exp("freeze", name)
        assert code == 0, (name, out)
        assert "WARN" not in out, (name, out)


def test_build_examples_pass_lean_and_compile(host):
    (pipeline,) = blocks(SKILLS / "agent-spec-pipeline" / "references" / "plan.md")
    host.write(".specs/features/pipe/plan.md", pipeline)
    code, out = host.contract("compile", "pipe", "--dialect", "sqlite")
    assert code == 0, out
    assert host.route("freeze", "pipe")[0] == 0
    (mlops,) = blocks(SKILLS / "agent-spec-mlops" / "references" / "plan.md")
    host.write(".specs/features/churn-mlops/plan.md", mlops)
    assert host.route("freeze", "churn-mlops")[0] == 0
    assert host.contract("compile", "churn-mlops", "--dialect", "sqlite")[0] == 0


def test_example_plans_are_valid():
    for host, slug in (("app", "sum"), ("pipeline", "orders"), ("mlops", "churn-mlops")):
        root = ROOT / "examples" / host / "host"
        assert lean_plan.main([slug, "--root", str(root)]) == 0, slug


def test_research_freeze_needs_the_research_half(host):
    host.spec("thin", text=re.sub(r"## Problem.*?(?=## Cases)", "", blocks(
        SKILLS / "agent-spec-experiment" / "references" / "plan.md")[0], flags=re.DOTALL))
    host.commit("thin")
    code, out = host.exp("freeze", "thin")
    assert code == 2
    for part in ("no ## Problem", "no ## Diagnosis", "no ## Hypotheses"):
        assert part in out, part


def test_research_hypothesis_needs_idea_and_why(host):
    text = blocks(SKILLS / "agent-spec-experiment" / "references" / "plan.md")[0]
    host.spec("h", text=text.replace("- Why: the records were read on all 14 failing traces; only the citation was missing\n", ""))
    host.commit("h")
    code, out = host.exp("freeze", "h")
    assert code == 2 and "H1 - cite-ids" in out and "- Why:" in out


def test_experiment_has_a_reference_per_phase_like_lean():
    skill = (SKILLS / "agent-spec-experiment" / "SKILL.md").read_text()
    for phase, ref in (("Plan", "plan.md"), ("Run", "run.md"), ("Verify", "verify.md")):
        assert (SKILLS / "agent-spec-experiment" / "references" / ref).exists(), ref
        assert f"| {phase} |" in skill and f"(references/{ref})" in skill, phase
    assert (SKILLS / "agent-spec-experiment" / "references" / "memory.md").exists()
    assert "## Rules" in skill and "Author is not verifier" in skill
