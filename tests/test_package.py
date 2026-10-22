import json
import re
import unittest
from pathlib import Path

from token_beggar import __version__, routes

ROOT = Path(__file__).resolve().parent.parent


def frontmatter(path: Path) -> dict:
    match = re.match(r"---\n(.*?)\n---\n", path.read_text(), re.S)
    assert match, path
    return dict(line.split(":", 1) for line in match.group(1).splitlines() if ":" in line)


class PackageTests(unittest.TestCase):
    def test_versions_agree(self):
        plugin = json.loads((ROOT / ".claude-plugin" / "plugin.json").read_text())
        self.assertEqual(plugin["version"], __version__)
        self.assertIn(f'version = "{__version__}"', (ROOT / "pyproject.toml").read_text())

    def test_marketplace_points_at_this_plugin(self):
        market = json.loads((ROOT / ".claude-plugin" / "marketplace.json").read_text())
        plugin = json.loads((ROOT / ".claude-plugin" / "plugin.json").read_text())
        self.assertEqual(market["plugins"][0]["name"], plugin["name"])

    def test_hooks_call_the_module_through_the_plugin_root(self):
        hooks = json.loads((ROOT / "hooks" / "hooks.json").read_text())["hooks"]
        self.assertEqual(set(hooks), {"UserPromptSubmit", "PreCompact", "SessionStart"})
        for groups in hooks.values():
            for group in groups:
                for hook in group["hooks"]:
                    self.assertIn("${CLAUDE_PLUGIN_ROOT}", hook["command"])
                    self.assertIn("token_beggar hook", hook["command"])

    def test_skill_and_agent_frontmatter(self):
        skill = frontmatter(ROOT / "skills" / "token-beggar" / "SKILL.md")
        self.assertEqual(skill["name"].strip(), "token-beggar")
        self.assertTrue(skill["description"].strip())
        agent = frontmatter(ROOT / "agents" / "beggar-worker.md")
        self.assertEqual(agent["model"].strip(), "haiku")

    def test_every_route_class_has_a_rubric_line_in_the_skill(self):
        text = (ROOT / "skills" / "token-beggar" / "SKILL.md").read_text()
        for spec in routes.classes():
            self.assertIn(spec["id"], text)

    def test_no_brand_names_in_the_package_name(self):
        for name in ("claude", "anthropic"):
            self.assertNotIn(name, ROOT.name.lower())
            self.assertNotIn(name, json.loads((ROOT / ".claude-plugin" / "plugin.json").read_text())["name"])


if __name__ == "__main__":
    unittest.main()
