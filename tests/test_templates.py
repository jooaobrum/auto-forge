import re

from conftest import SKILLS

APPROVE = '**Approved**: 2026-11-22 - user: "go"'


def filled(path) -> str:
    """The template's markdown block, with only the approval written and the Dataset placeholder dropped."""
    text = re.search(r"```markdown\n(.*?)\n```", path.read_text(), re.DOTALL).group(1)
    text = re.sub(r"(?m)^\*\*Approved\*\*:.*$", APPROVE, text)
    return re.sub(r"(?m)^\*\*Dataset\*\*:.*\n", "", text)


def test_templates_freeze_and_compile_as_shown(host):
    for name, template in (("agent", "spec-agent.md"), ("model", "spec-model.md")):
        host.spec(name, text=filled(SKILLS / "agent-spec-experiment" / "references" / template))
        host.commit(name)
        code, out = host.exp("freeze", name)
        assert code == 0, (template, out)
    host.write(".specs/features/pipe/spec.md", filled(SKILLS / "agent-spec-pipeline" / "references" / "spec-pipeline.md"))
    code, out = host.contract("compile", "pipe", "--dialect", "sqlite")
    assert code == 0, out
    assert host.route("freeze", "pipe")[0] == 0
