import json
import re

import yaml
from conftest import ROOT, SKILLS

AGENTS = {"verifier": "verify-model", "modeling-iteration-runner": "run-modeling-iteration"}


def test_plugin_manifests_and_marketplace():
    agent_plugins = json.loads((ROOT / "plugin.json").read_text())
    assert agent_plugins["$schema"] == "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json"
    claude = json.loads((ROOT / ".claude-plugin" / "plugin.json").read_text())
    for manifest in (agent_plugins, claude):
        assert manifest["name"] == "auto-forge"
        assert re.fullmatch(r"\d+\.\d+\.\d+", manifest["version"])
    assert agent_plugins["version"] == claude["version"]
    market = json.loads((ROOT / ".claude-plugin" / "marketplace.json").read_text())
    assert [p["name"] for p in market["plugins"]] == ["auto-forge"]
    assert market["plugins"][0]["source"] == "./"
    for folder in SKILLS.iterdir():
        if folder.is_dir():
            assert re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", folder.name), folder.name
            assert (folder / "SKILL.md").exists(), folder.name



def split_frontmatter(path) -> tuple[dict, str]:
    match = re.match(r"^---\n(.*?)\n---\n(.*)$", path.read_text(), re.DOTALL)
    assert match, f"{path} has no frontmatter"
    return yaml.safe_load(match.group(1)), match.group(2)


def test_agents_are_shared_by_claude_code_and_copilot():
    files = sorted(p.stem for p in (ROOT / "agents").glob("*.md"))
    assert files == sorted(AGENTS)
    for name in AGENTS:
        meta, body = split_frontmatter(ROOT / "agents" / f"{name}.md")
        # only the fields both Claude Code and GitHub Copilot read; no model (their ids differ)
        assert set(meta) == {"name", "description", "tools"}, name
        assert meta["name"] == name and "Use when" in meta["description"]
        assert [t.strip() for t in meta["tools"].split(",")] == ["Read", "Grep", "Glob", "Bash", "Edit", "Write"]
        assert body.strip()
    # Claude Code scans agents/ by default; an "agents" field would replace that scan
    for manifest in (ROOT / "plugin.json", ROOT / ".claude-plugin" / "plugin.json"):
        assert "agents" not in json.loads(manifest.read_text()), manifest


def test_platforms_without_subagents_get_the_same_body_as_a_skill():
    for agent, skill in AGENTS.items():
        _, agent_body = split_frontmatter(ROOT / "agents" / f"{agent}.md")
        meta, skill_body = split_frontmatter(SKILLS / skill / "SKILL.md")
        assert meta["name"] == skill and "no subagents" in meta["description"]
        assert skill_body == agent_body, f"skills/{skill}/SKILL.md drifted from agents/{agent}.md"
