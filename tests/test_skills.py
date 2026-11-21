import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
COMMANDS = ("brief", "freeze", "baseline", "select", "contract", "gate", "budget", "deliver")


def frontmatter(path: Path) -> dict:
    match = re.match(r"^---\n(.*?)\n---\n", path.read_text(), re.DOTALL)
    assert match, f"{path} has no frontmatter"
    return yaml.safe_load(match.group(1))


def test_skills_frontmatter_and_commands():
    for name in ("shape", "lanes"):
        path = ROOT / "skills" / name / "SKILL.md"
        meta = frontmatter(path)
        assert meta["name"] == name
        assert len(meta["description"]) > 40
    shape = (ROOT / "skills/shape/SKILL.md").read_text()
    assert "rl brief" in shape
    lanes = (ROOT / "skills/lanes/SKILL.md").read_text()
    for command in COMMANDS[1:]:
        assert f"rl {command}" in lanes, command
