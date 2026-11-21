import re

import yaml
from conftest import SKILLS

SKILL_DIRS = sorted(p for p in SKILLS.iterdir() if p.is_dir())


def frontmatter(path) -> dict:
    match = re.match(r"^---\n(.*?)\n---\n", path.read_text(), re.DOTALL)
    assert match, f"{path} has no frontmatter"
    return yaml.safe_load(match.group(1))


def test_skill_frontmatter_and_shared_parser():
    names = {p.name for p in SKILL_DIRS}
    assert names == {"agent-spec-router", "agent-spec-grilling", "agent-spec-writer", "agent-spec-lean",
                     "agent-spec-pipeline", "agent-spec-experiment", "data-databricks-sql", "ml-mlflow-log"}
    for folder in SKILL_DIRS:
        meta = frontmatter(folder / "SKILL.md")
        assert meta["name"] == folder.name
        assert "Use when" in meta["description"] or "Use first" in meta["description"], folder.name
    copies = [p.read_text() for p in SKILLS.glob("*/scripts/spec_md.py")]
    assert len(copies) == 3 and len(set(copies)) == 1


def test_load_points_and_domain_skills():
    for lane in ("agent-spec-lean", "agent-spec-pipeline", "agent-spec-experiment"):
        text = (SKILLS / lane / "SKILL.md").read_text()
        points = text.split("## Load points")[1].split("\n## ")[0]
        assert ".specs/LAB.md" in points and "## Domain skills" in points, lane
        for point in ("**plan**", "**work**", "**verify**"):
            assert point in points, (lane, point)
    for skill, point in (("data-databricks-sql", "plan"), ("ml-mlflow-log", "verify")):
        meta = frontmatter(SKILLS / skill / "SKILL.md")
        assert meta["description"].startswith("Use when") and f"{point}" in meta["description"]
