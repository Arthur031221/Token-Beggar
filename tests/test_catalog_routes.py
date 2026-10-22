import unittest

from token_beggar import catalog, routes

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


class RouteTests(Isolated):
    def test_never_above_the_ceiling(self):
        for alias in ("haiku", "sonnet", "opus", "fable"):
            for effort in catalog.load()["efforts"]:
                cap = ceiling(alias, effort)
                for row in routes.table(cap):
                    self.assertLessEqual(catalog.find(row["model"]).tier, cap["tier"], row)
                    self.assertLessEqual(catalog.effort_rank(row["effort"]), catalog.effort_rank(effort), row)

    def test_cheap_classes_go_to_the_smallest_model(self):
        row = routes.route("mechanical", ceiling("opus", "high"))
        self.assertEqual((row["model"], row["mode"]), ("haiku", "subagent"))

    def test_judgement_classes_stay_inline_on_the_ceiling(self):
        for name in ("debugging", "design"):
            row = routes.route(name, ceiling("opus", "high"))
            self.assertEqual((row["model"], row["effort"], row["mode"]), ("opus", "high", "inline"))

    def test_low_ceiling_collapses_to_inline(self):
        row = routes.route("routine_code", ceiling("haiku", "low"))
        self.assertEqual((row["model"], row["effort"], row["mode"]), ("haiku", "low", "inline"))

    def test_exhausted_model_falls_to_the_next_one_down(self):
        row = routes.route("routine_code", ceiling("opus", "high"), {"sonnet"})
        self.assertEqual(row["model"], "haiku")

    def test_when_every_smaller_model_is_out_the_row_stays_with_the_chat_model(self):
        row = routes.route("mechanical", ceiling("sonnet", "high"), {"haiku", "sonnet"})
        self.assertEqual(row["model"], "sonnet")


if __name__ == "__main__":
    unittest.main()
