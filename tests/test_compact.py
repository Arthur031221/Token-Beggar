import dataclasses
import json
import os
import unittest
from unittest import mock

from token_beggar import catalog, compact, handoff, transcript

from .helpers import Isolated, assistant, bash, edit, user, write_transcript

OPUS = catalog.find("opus")
SMALL = dataclasses.replace(OPUS, context_window=400_000)  # the host default point is 367k, with no setting for the skill to respect


def payload(tmp, items, trigger="auto", session="s1"):
    return {"session_id": session, "trigger": trigger, "cwd": str(tmp), "transcript_path": write_transcript(tmp / "t.jsonl", items)}


def at(tokens, edits=True):
    return [user("do it"), assistant("e", [edit("/p/a.py")] if edits else [], tokens=tokens)]


class WindowTests(Isolated):
    def test_parse(self):
        self.assertEqual(compact.parse_window("400000"), 400000)
        self.assertEqual(compact.parse_window("400k"), 400000)
        self.assertEqual(compact.parse_window("1m"), 1_000_000)
        self.assertEqual(compact.parse_window("1.5M"), 1_500_000)
        self.assertIsNone(compact.parse_window("lots"))
        self.assertIsNone(compact.parse_window(None))

    def test_environment_then_settings_then_unset(self):
        self.assertIsNone(compact.configured_window())
        self.settings(env={"CLAUDE_CODE_AUTO_COMPACT_WINDOW": "300k"})
        self.assertEqual(compact.configured_window(), (300_000, "CLAUDE_CODE_AUTO_COMPACT_WINDOW"))
        with mock.patch.dict("os.environ", {"CLAUDE_CODE_AUTO_COMPACT_WINDOW": "100000"}):
            self.assertEqual(compact.configured_window()[0], 100_000)

    def test_the_window_setting_is_clamped_like_the_host_does(self):
        with mock.patch.dict("os.environ", {"CLAUDE_CODE_AUTO_COMPACT_WINDOW": "50000"}):
            self.assertEqual(compact.configured_window()[0], 100_000)
        with mock.patch.dict("os.environ", {"CLAUDE_CODE_AUTO_COMPACT_WINDOW": "5m"}):
            self.assertEqual(compact.configured_window()[0], 1_000_000)

    def test_settings_keys_are_read(self):
        self.settings(autoCompactWindow=400000)
        self.assertEqual(compact.configured_window(), (400_000, "autoCompactWindow"))
        self.settings(modelSettings={"opus": {"autoCompactWindow": 250000}}, autoCompactWindow=400000)
        self.assertEqual(compact.configured_window(model=OPUS), (250_000, "modelSettings.autoCompactWindow"))
        self.assertEqual(compact.configured_window(model=catalog.find("haiku")), (400_000, "autoCompactWindow"))


class ResolveTests(Isolated):
    def test_default_point_works_with_nothing_configured(self):
        point = compact.resolve(None, OPUS)
        self.assertEqual(point["threshold"], 1_000_000 - 20_000 - 13_000)
        self.assertEqual(point["source"], "model default")
        self.assertFalse(point["disabled"])

    def test_a_configured_window_moves_the_point(self):
        self.settings(env={"CLAUDE_CODE_AUTO_COMPACT_WINDOW": "400000"})
        point = compact.resolve(None, OPUS)
        self.assertEqual(point["threshold"], 367_000)
        self.assertEqual(point["source"], "CLAUDE_CODE_AUTO_COMPACT_WINDOW")

    def test_percent_override_only_lowers_the_point(self):
        self.settings(env={"CLAUDE_AUTOCOMPACT_PCT_OVERRIDE": "50"})
        self.assertEqual(compact.resolve(None, OPUS)["threshold"], 490_000)
        self.settings(env={"CLAUDE_AUTOCOMPACT_PCT_OVERRIDE": "100"})
        self.assertEqual(compact.resolve(None, OPUS)["threshold"], 967_000)

    def test_disable_switches(self):
        for setting in ({"env": {"DISABLE_AUTO_COMPACT": "1"}}, {"env": {"DISABLE_COMPACT": "true"}}, {"autoCompactEnabled": False}):
            self.settings(**setting)
            self.assertTrue(compact.resolve(None, OPUS)["disabled"], setting)

    def test_deferral_stays_below_the_blocking_level(self):
        point = compact.resolve(None, OPUS)
        self.assertLess(point["defer_limit"], point["context_window"] - 23_000)
        self.settings(env={"CLAUDE_CODE_AUTO_COMPACT_WINDOW": "400000"})
        small = compact.resolve(None, OPUS)
        self.assertGreater(small["defer_limit"], small["threshold"])


class NoticeTests(Isolated):
    def point(self, window="400000"):
        self.settings(env={"CLAUDE_CODE_AUTO_COMPACT_WINDOW": window})
        return compact.resolve(None, OPUS)

    def test_warns_only_near_the_point(self):
        point = self.point()
        self.assertIsNone(compact.usage_notice("s1", at(100_000), point))
        notice = compact.usage_notice("s1", at(360_000), point)
        self.assertIn("compaction point", notice)
        self.assertIn("note --mid-step", notice)

    def test_a_small_window_warns_early_enough_for_one_big_tool_result(self):
        self.assertEqual(compact.warn_point(67_000), 37_000)
        self.assertEqual(compact.warn_point(967_000), 846_125)
        self.assertGreater(compact.warn_point(40_000), 19_999)

    def test_the_notice_is_throttled_across_a_long_turn(self):
        point = self.point()
        self.assertIsNotNone(compact.usage_notice("s1", at(360_000), point))
        self.assertIsNone(compact.usage_notice("s1", at(362_000), point))
        self.assertIsNotNone(compact.usage_notice("s1", at(380_000), point))

    def test_a_fresh_note_silences_it(self):
        point = self.point()
        handoff.write_model("s1", "state", mid_step=False, used=358_000)
        self.assertIsNone(compact.usage_notice("s1", at(360_000), point))

    def test_nothing_when_compaction_is_off(self):
        self.settings(env={"DISABLE_AUTO_COMPACT": "1"})
        self.assertIsNone(compact.usage_notice("s1", at(990_000), compact.resolve(None, OPUS)))


class VerdictTests(Isolated):
    def test_mechanical_rule_without_a_note(self):
        self.assertTrue(compact.verdict("s1", at(10_000))[0])
        clean = [user("x"), assistant("e", [edit("/p/a.py")]), assistant("t", [bash("pytest")])]
        self.assertFalse(compact.verdict("s1", clean)[0])

    def test_the_models_note_wins_while_it_is_fresh(self):
        handoff.write_model("s1", "half done", mid_step=True, used=10_000)
        self.assertTrue(compact.verdict("s1", at(12_000, edits=False))[0])
        handoff.write_model("s1", "done", mid_step=False, used=10_000)
        self.assertFalse(compact.verdict("s1", at(12_000, edits=True))[0])

    def test_a_stale_clean_note_is_ignored(self):
        handoff.write_model("s1", "done", mid_step=False, used=10_000)
        self.assertTrue(compact.verdict("s1", at(10_000 + compact.FRESH_NOTE_TOKENS + 5_000, edits=True))[0])

    def test_a_stale_mid_step_note_still_defers(self):
        handoff.write_model("s1", "half done", mid_step=True, used=10_000)
        self.assertTrue(compact.verdict("s1", at(10_000 + compact.FRESH_NOTE_TOKENS + 5_000, edits=False))[0])


class PreCompactTests(Isolated):
    def setUp(self):
        super().setUp()

    def test_mid_step_auto_compaction_is_deferred_then_released(self):
        data = payload(self.tmp, at(370_000))
        codes = [compact.on_precompact(data, SMALL)[0] for _ in range(compact.MAX_DEFERRALS + 1)]
        self.assertEqual(codes, [2, 2, 2, 0])

    def test_clean_state_compacts_at_once(self):
        clean = [user("do it"), assistant("e", [edit("/p/a.py")]), assistant("t", [bash("pytest")], tokens=370_000)]
        self.assertEqual(compact.on_precompact(payload(self.tmp, clean), SMALL)[0], 0)

    def test_it_works_with_nothing_configured(self):
        self.assertEqual(compact.on_precompact(payload(self.tmp, at(970_000)), OPUS)[0], 2)
        self.assertIn("do it", handoff.read("s1"))

    def test_the_models_note_can_declare_a_clean_stop(self):
        handoff.write_model("s1", "all done", mid_step=False, used=365_000)
        self.assertEqual(compact.on_precompact(payload(self.tmp, at(370_000)), SMALL)[0], 0)

    def test_manual_compaction_is_never_deferred(self):
        self.assertEqual(compact.on_precompact(payload(self.tmp, at(370_000), trigger="manual"), SMALL)[0], 0)

    def test_disabled_compaction_is_never_deferred(self):
        self.settings(env={"DISABLE_AUTO_COMPACT": "1"})
        self.assertEqual(compact.on_precompact(payload(self.tmp, at(370_000)), SMALL)[0], 0)

    def test_context_far_past_the_point_is_never_deferred(self):
        self.assertEqual(compact.on_precompact(payload(self.tmp, at(900_000)), SMALL)[0], 0)

    def test_the_deferral_is_announced_once(self):
        compact.on_precompact(payload(self.tmp, at(370_000)), SMALL)
        self.assertIn("deferred", compact.deferred_notice("s1"))
        self.assertIsNone(compact.deferred_notice("s1"))

    def test_note_is_written_every_time(self):
        compact.on_precompact(payload(self.tmp, at(10_000)), SMALL)
        self.assertIn("do it", handoff.read("s1"))

    def test_session_start_restores_the_models_note_first(self):
        compact.on_precompact(payload(self.tmp, at(10_000)), SMALL)
        handoff.write_model("s1", "Decision: use sqlite because of two writers.", mid_step=False, used=1)
        restored = compact.on_session_start({"session_id": "s1", "source": "compact"})
        self.assertIn("Decision: use sqlite", restored)
        self.assertIn("do it", restored)  # the mechanical extract rides along as the backup
        self.assertIsNone(compact.on_session_start({"session_id": "s1", "source": "startup"}))

    def test_an_old_note_is_labelled_and_the_extract_comes_first(self):
        compact.on_precompact(payload(self.tmp, at(60_000)), SMALL)
        handoff.write_model("s1", "Decision: use sqlite.", mid_step=False, used=10_000)
        restored = compact.on_session_start({"session_id": "s1", "source": "compact"})
        self.assertIn("older than the compaction", restored)
        self.assertLess(restored.index("do it"), restored.index("Decision: use sqlite"))

    def test_session_start_falls_back_to_the_mechanical_extract(self):
        compact.on_precompact(payload(self.tmp, at(10_000)), SMALL)
        self.assertIn("do it", compact.on_session_start({"session_id": "s1", "source": "compact"}))


class DynamicPointTests(Isolated):
    def point(self):
        return compact.resolve(None, SMALL)

    def test_a_point_the_user_set_is_used_as_it_is_and_a_mid_step_is_still_deferred(self):
        self.settings(env={"CLAUDE_CODE_AUTO_COMPACT_WINDOW": "400000"})
        point = compact.resolve(None, OPUS)
        self.assertTrue(point["user_set"])
        self.assertEqual(point["threshold"], 400_000 - 33_000)
        self.assertEqual(compact.deferral_plan("s1", point)["mode"], "defer")
        handoff.write_model("s1", "half done", mid_step=True, used=1)
        self.assertEqual(compact.on_precompact(payload(self.tmp, at(370_000)), OPUS)[0], 2)

    def test_a_user_set_point_never_gets_the_early_suggestion(self):
        self.settings(env={"CLAUDE_CODE_AUTO_COMPACT_WINDOW": "400000"})
        handoff.write_model("s1", "phase over", mid_step=False, used=1, phase_done=True)
        point = compact.resolve(None, OPUS)
        self.assertEqual(compact.deferral_plan("s1", point)["mode"], "defer")
        self.assertIsNone(compact.early_notice("s1", 150_000, point))

    def test_the_percent_override_counts_as_the_users_point(self):
        self.settings(env={"CLAUDE_AUTOCOMPACT_PCT_OVERRIDE": "50"})
        self.assertTrue(compact.resolve(None, OPUS)["user_set"])

    def test_nothing_set_means_the_skill_chooses(self):
        self.assertFalse(self.point()["user_set"])
        self.assertEqual(compact.deferral_plan("s1", self.point())["mode"], "defer")

    def test_a_nearly_done_step_is_deferred_once_and_an_early_one_longer(self):
        point = self.point()
        handoff.write_model("s1", "n", mid_step=True, used=1, progress=0.95)
        self.assertEqual(compact.deferral_plan("s1", point)["deferrals"], 1)
        handoff.write_model("s1", "n", mid_step=True, used=1, progress=0.1)
        self.assertEqual(compact.deferral_plan("s1", point)["deferrals"], compact.MAX_DEFERRALS)

    def test_needed_early_detail_keeps_the_most_context(self):
        handoff.write_model("s1", "n", mid_step=True, used=1, progress=0.95, needs_detail=True)
        self.assertEqual(compact.deferral_plan("s1", self.point())["deferrals"], compact.MAX_DEFERRALS)

    def test_the_deferral_count_is_honoured_and_stays_below_the_blocking_level(self):
        point = self.point()
        handoff.write_model("s1", "n", mid_step=True, used=350_000, progress=0.95)
        codes = [compact.on_precompact(payload(self.tmp, at(350_000)), SMALL)[0] for _ in range(2)]
        self.assertEqual(codes, [2, 0])
        self.assertLessEqual(compact.deferral_plan("s1", point)["wanted"], point["defer_limit"])

    def test_a_long_context_asks_once_whether_a_phase_finished(self):
        point = self.point()
        self.assertIsNone(compact.usage_notice("s1", at(50_000, edits=False), point))
        notice = compact.usage_notice("s1", at(160_000, edits=False), point)
        self.assertIn("--phase-done", notice)
        self.assertIn("/compact", notice)
        self.assertIsNone(compact.usage_notice("s1", at(165_000, edits=False), point))

    def test_after_a_phase_done_note_it_tells_the_model_to_suggest_it(self):
        handoff.write_model("s1", "phase one done", mid_step=False, used=150_000, phase_done=True)
        notice = compact.usage_notice("s1", at(160_000, edits=False), self.point())
        self.assertIn("Your note says the last phase is finished", notice)

    def test_asks_again_after_a_compaction_shrank_the_context(self):
        point = self.point()
        self.assertIsNotNone(compact.usage_notice("s1", at(200_000, edits=False), point))
        self.assertIsNone(compact.usage_notice("s1", at(210_000, edits=False), point))
        self.assertIsNotNone(compact.usage_notice("s1", at(160_000, edits=False), point))

    def test_the_early_point_is_bounded(self):
        self.assertEqual(compact.early_point({"threshold": 967_000}), compact.EARLY_CEILING)
        self.assertEqual(compact.early_point({"threshold": 100_000}), compact.EARLY_FLOOR)

    def test_no_early_suggestion_when_the_user_chose_the_point(self):
        self.settings(env={"CLAUDE_CODE_AUTO_COMPACT_WINDOW": "400000"})
        self.assertIsNone(compact.early_notice("s1", 160_000, compact.resolve(None, OPUS)))

    def test_the_early_suggestion_is_off_unless_asked_for(self):
        with mock.patch.dict(os.environ, {"TOKEN_BEGGAR_EARLY": ""}):
            self.assertFalse(compact.early_enabled())
            self.assertIsNone(compact.early_notice("s1", 160_000, compact.resolve(None, OPUS)))

    def test_the_new_note_fields_round_trip(self):
        handoff.write_model("s1", "n", mid_step=False, used=5, progress=0.5, phase_done=True, needs_detail=True)
        note = handoff.read_model("s1")
        self.assertEqual((note["progress"], note["phase"], note["needs_detail"]), (0.5, "done", True))


class TailTests(Isolated):
    def test_tail_context_matches_the_full_parse(self):
        path = write_transcript(self.tmp / "big.jsonl", [user("x")] + [assistant("y", tokens=n) for n in range(1000, 4000, 1000)])
        self.assertEqual(transcript.tail_context_tokens(path), transcript.context_tokens(transcript.entries(path)))
        self.assertEqual(transcript.tail_context_tokens(self.tmp / "missing.jsonl"), 0)

    def test_tail_reads_only_the_end_of_a_long_file(self):
        rows = [json.dumps(assistant("pad " * 50, tokens=1)) for _ in range(400)] + [json.dumps(assistant("last", tokens=77_000))]
        path = self.tmp / "long.jsonl"
        path.write_text("\n".join(rows) + "\n")
        self.assertEqual(transcript.tail_context_tokens(path, window=20_000), 77_010)


if __name__ == "__main__":
    unittest.main()
