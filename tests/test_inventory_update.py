import json
import time
import unittest
from pathlib import Path
from unittest import mock

from token_beggar import catalog, inventory, update

from .helpers import Isolated

FIXTURE = Path(__file__).parent / "fixtures" / "models-overview.fixture"


class InventoryTests(Isolated):
    def test_discovers_cli_tools_on_path(self):
        with mock.patch("shutil.which", side_effect=lambda b: "/bin/codex" if b == "codex" else None):
            found = inventory.discover()
        self.assertEqual([e["name"] for e in found["external"]], ["codex"])

    def test_an_mcp_server_that_fronts_another_ai_is_a_route(self):
        project = self.tmp / "proj"
        project.mkdir()
        (project / ".mcp.json").write_text(json.dumps({"mcpServers": {"codex-cli": {}, "postgres": {}}}))
        with mock.patch("shutil.which", return_value=None):
            found = inventory.discover(str(project))
        mcp = [e for e in found["external"] if e["kind"] == "mcp"]
        self.assertIn("codex-cli", [e["name"] for e in mcp])
        self.assertNotIn("postgres", [e["name"] for e in found["external"]])

    def test_the_external_list_can_be_limited_by_environment(self):
        with mock.patch("shutil.which", return_value="/bin/x"), mock.patch.dict("os.environ", {"TOKEN_BEGGAR_EXTERNAL": "agy"}):
            self.assertEqual([e["name"] for e in inventory.discover()["external"]], ["agy"])
        with mock.patch("shutil.which", return_value="/bin/x"), mock.patch.dict("os.environ", {"TOKEN_BEGGAR_EXTERNAL": "none"}):
            self.assertEqual(inventory.discover()["external"], [])

    def test_denied_models_leave_the_inventory(self):
        self.settings(deniedModels=["claude-fable-5-1"])
        self.assertNotIn("fable", inventory.discover()["claude"])

    def test_available_models_acts_as_an_allow_list(self):
        self.settings(availableModels=["sonnet", "haiku"])
        self.assertEqual(sorted(inventory.discover()["claude"]), ["haiku", "sonnet"])

    def test_exhausted_marks_expire(self):
        inventory.mark_exhausted("opus", hours=1)
        self.assertEqual(inventory.exhausted_aliases(inventory.load()), {"opus"})
        later = time.time() + 2 * 3600
        self.assertEqual(inventory.exhausted_aliases(inventory.load(), now=later), set())
        inventory.clear_exhausted("opus")
        self.assertEqual(inventory.exhausted_aliases(inventory.load()), set())

    def test_exhausted_marks_survive_a_rebuild(self):
        inventory.mark_exhausted("sonnet")
        again = inventory.load(max_age=0)
        self.assertIn("sonnet", again["exhausted"])


class UpdateTests(Isolated):
    def test_parses_the_real_models_page(self):
        found = update.parse_overview(FIXTURE.read_text())
        self.assertEqual([m["alias"] for m in found], ["haiku", "sonnet", "opus", "fable"])
        self.assertEqual([m["tier"] for m in found], [1, 2, 3, 4])
        self.assertTrue(all(m["id"].startswith("claude-") for m in found))
        self.assertTrue(all(m["input_per_mtok"] < m["output_per_mtok"] for m in found))

    def test_a_changed_page_keeps_the_old_catalog(self):
        with self.assertRaises(ValueError):
            update.refresh(markdown="| Feature | nothing |\n")
        self.assertFalse((Path(update.paths.home()) / "models.json").exists())

    def test_refresh_writes_and_the_newer_file_wins(self):
        data = update.refresh(markdown=FIXTURE.read_text())
        self.assertEqual(catalog.find("opus").id, next(m["id"] for m in data["claude"] if m["alias"] == "opus"))
        stale = json.loads(update.paths.data_file("models.json").read_text())
        stale["updated"] = "2999-01-01"
        stale["claude"][0]["id"] = "claude-haiku-9-9"
        shipped = update.paths.home() / "models.json"
        shipped.write_text(json.dumps(stale))
        self.assertEqual(catalog.find("haiku").id, "claude-haiku-9-9")

    def test_due_after_a_week(self):
        self.assertTrue(update.due())
        update.mark_checked()
        self.assertFalse(update.due())
        (update.paths.home() / "models.checked").write_text(str(time.time() - 8 * 86400))
        self.assertTrue(update.due())


if __name__ == "__main__":
    unittest.main()
