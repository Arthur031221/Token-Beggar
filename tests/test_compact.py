import unittest
from unittest import mock

from token_beggar import compact, handoff

from .helpers import Isolated, assistant, bash, edit, user, write_transcript


def payload(tmp, items, trigger="auto", session="s1"):
    return {"session_id": session, "trigger": trigger, "cwd": str(tmp), "transcript_path": write_transcript(tmp / "t.jsonl", items)}


MID_STEP = [user("do it"), assistant("e", [edit("/p/a.py")], tokens=410_000)]
CLEAN = [user("do it"), assistant("e", [edit("/p/a.py")]), assistant("t", [bash("pytest")], tokens=410_000)]


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
        self.assertEqual(compact.configured_window(), 300_000)
        with mock.patch.dict("os.environ", {"CLAUDE_CODE_AUTO_COMPACT_WINDOW": "100000"}):
            self.assertEqual(compact.configured_window(), 100_000)


class NoticeTests(Isolated):
    def test_no_notice_when_the_window_is_not_known(self):
        self.assertIsNone(compact.usage_notice([assistant("x", tokens=900_000)], None))

    def test_warns_only_near_the_point(self):
        self.assertIsNone(compact.usage_notice([assistant("x", tokens=100_000)], 400_000))
        self.assertIn("compaction point", compact.usage_notice([assistant("x", tokens=360_000)], 400_000))


class PreCompactTests(Isolated):
    def setUp(self):
        super().setUp()
        self.settings(env={"CLAUDE_CODE_AUTO_COMPACT_WINDOW": "400000"})

    def test_mid_step_auto_compaction_is_deferred_then_released(self):
        data = payload(self.tmp, MID_STEP)
        codes = [compact.on_precompact(data)[0] for _ in range(compact.MAX_DEFERRALS + 1)]
        self.assertEqual(codes, [2, 2, 2, 0])

    def test_clean_state_compacts_at_once(self):
        self.assertEqual(compact.on_precompact(payload(self.tmp, CLEAN))[0], 0)

    def test_without_a_configured_window_nothing_is_deferred_but_the_note_is_written(self):
        (self.tmp / "settings.json").unlink(missing_ok=True)
        with mock.patch.object(compact, "configured_window", return_value=None):
            self.assertEqual(compact.on_precompact(payload(self.tmp, MID_STEP))[0], 0)
        self.assertIn("do it", handoff.read("s1"))

    def test_manual_compaction_is_never_deferred(self):
        self.assertEqual(compact.on_precompact(payload(self.tmp, MID_STEP, trigger="manual"))[0], 0)

    def test_context_far_past_the_point_is_never_deferred(self):
        items = [user("x"), assistant("e", [edit("/p/a.py")], tokens=900_000)]
        self.assertEqual(compact.on_precompact(payload(self.tmp, items))[0], 0)

    def test_note_is_written_every_time(self):
        compact.on_precompact(payload(self.tmp, CLEAN))
        self.assertIn("do it", handoff.read("s1"))

    def test_session_start_restores_the_note_after_compaction_only(self):
        compact.on_precompact(payload(self.tmp, CLEAN))
        restored = compact.on_session_start({"session_id": "s1", "source": "compact"})
        self.assertIn("do it", restored)
        self.assertIsNone(compact.on_session_start({"session_id": "s1", "source": "startup"}))


if __name__ == "__main__":
    unittest.main()
