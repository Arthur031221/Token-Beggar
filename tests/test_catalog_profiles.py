import unittest

from token_beggar import card, catalog, inventory, profiles

from .helpers import Isolated


def ceiling(alias: str, effort: str) -> dict:
    model = catalog.find(alias)
    return {"model": model.id, "alias": model.alias, "tier": model.tier, "effort": effort, "known": True}


class CatalogTests(unittest.TestCase):
    def test_find_by_alias_id_and_dated_id(self):
        self.assertEqual(catalog.find("opus").id, "claude-opus-5-5")
        self.assertEqual(catalog.find("claude-sonnet-5-5").alias, "sonnet")
        self.assertEqual(catalog.find("claude-haiku-5-5-20260901").alias, "haiku")
        self.assertIsNone(catalog.find("gpt-9"))
        self.assertIsNone(catalog.find(None))

    def test_cap_effort_never_raises(self):
        self.assertEqual(catalog.cap_effort("high", "medium"), "medium")
        self.assertEqual(catalog.cap_effort("low", "max"), "low")

    def test_every_model_has_a_context_window(self):
        for model in catalog.models():
            self.assertGreaterEqual(model.context_window, 100_000)


class ProfileTests(Isolated):
    def test_every_claude_model_has_a_capability_and_a_description(self):
        spec = profiles.load()["claude"]
        for model in catalog.models():
            self.assertIn(model.alias, spec)
            self.assertTrue(spec[model.alias]["good_for"])

    def test_menu_never_goes_above_the_ceiling(self):
        for alias in ("haiku", "sonnet", "opus", "fable"):
            for effort in catalog.load()["efforts"]:
                cap = ceiling(alias, effort)
                for row in profiles.claude_combos(cap):
                    self.assertLessEqual(catalog.find(row["model"]).tier, cap["tier"], row)
                    self.assertLessEqual(catalog.effort_rank(row["effort"]), catalog.effort_rank(effort), row)

    def test_menu_is_sorted_cheapest_first(self):
        costs = [row["cost_index"] for row in profiles.claude_combos(ceiling("fable", "high"))]
        self.assertEqual(costs, sorted(costs))

    def test_models_that_are_out_of_quota_leave_the_menu(self):
        rows = profiles.claude_combos(ceiling("opus", "high"), {"sonnet"})
        self.assertNotIn("sonnet", {r["model"] for r in rows})

    def test_a_ceiling_effort_above_high_is_offered(self):
        efforts = {r["effort"] for r in profiles.claude_combos(ceiling("opus", "max"))}
        self.assertIn("max", efforts)
        self.assertNotIn("xhigh", efforts)

    def test_external_models_get_a_capability(self):
        self.assertEqual(profiles.external_model("agy", "gemini-3.8-flash-low")["capability"], 1)
        self.assertEqual(profiles.external_model("agy", "gemini-3.8-flash-high")["capability"], 3)
        self.assertEqual(profiles.external_model("agy", "something-new")["capability"], 2)

    def test_a_claude_model_behind_another_tool_still_obeys_the_ceiling(self):
        inv = {"external": [{"name": "agy", "models": ["gemini-3.8-flash-low", "claude-opus-4-6-thinking", "claude-sonnet-4-6"]}]}
        low = {r["model"] for r in profiles.external_combos(inv, {}, set(), ceiling_tier=2)}
        self.assertEqual(low, {"gemini-3.8-flash-low", "claude-sonnet-4-6"})
        high = {r["model"] for r in profiles.external_combos(inv, {}, set(), ceiling_tier=3)}
        self.assertIn("claude-opus-4-6-thinking", high)

    def test_user_caps_and_exhaustion_leave_the_menu(self):
        inv = {"external": [{"name": "agy", "models": ["gemini-3.8-flash-low", "gemini-3.8-flash-high", "gpt-oss-120b-medium"]}]}
        capped = {r["model"] for r in profiles.external_combos(inv, {"agy": "flash"})}
        self.assertEqual(capped, {"gemini-3.8-flash-low", "gemini-3.8-flash-high"})
        self.assertEqual(profiles.external_combos(inv, {"agy": "off"}), [])
        gone = {r["model"] for r in profiles.external_combos(inv, {}, {"agy:gemini-3.8-flash-high"})}
        self.assertNotIn("gemini-3.8-flash-high", gone)
        self.assertEqual(profiles.external_combos(inv, {}, {"agy"}), [])


class MenuTests(Isolated):
    def test_menu_reports_what_is_unavailable(self):
        inventory.mark_exhausted("sonnet")
        options = card.menu(ceiling("opus", "high"), inventory.load())
        self.assertIn("sonnet", options["unavailable"])
        self.assertNotIn("sonnet", {r["model"] for r in options["claude"]})


if __name__ == "__main__":
    unittest.main()
