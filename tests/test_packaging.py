import json
import re

from conftest import ROOT, SKILLS


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
