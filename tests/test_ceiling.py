import unittest
from unittest import mock

from token_beggar import ceiling

from .helpers import Isolated, assistant, user, write_transcript


class CeilingTests(Isolated):
    def test_transcript_model_wins(self):
        self.settings(model="haiku", effortLevel="low")
        path = write_transcript(self.tmp / "t.jsonl", [user("hi"), assistant("ok", model="claude-sonnet-5-5")])
        got = ceiling.resolve(path, str(self.tmp))
        self.assertEqual((got["alias"], got["effort"], got["known"]), ("sonnet", "low", True))

    def test_sidechain_messages_do_not_set_the_ceiling(self):
        path = write_transcript(
            self.tmp / "t.jsonl",
            [assistant("main", model="claude-opus-5-5"), assistant("sub", model="claude-haiku-5-5", sidechain=True)],
        )
        self.assertEqual(ceiling.resolve(path, None)["alias"], "opus")

    def test_launch_flags_beat_settings(self):
        self.settings(model="opus", effortLevel="xhigh")
        args = [["/usr/bin/claude", "-p", "x", "--model", "sonnet", "--effort=high"]]
        with mock.patch.object(ceiling, "_ancestor_args", return_value=args):
            got = ceiling.resolve(None, None)
        self.assertEqual((got["alias"], got["effort"]), ("sonnet", "high"))

    def test_flags_of_unrelated_processes_are_ignored(self):
        args = [["python3", "tool.py", "--model", "haiku"]]
        with mock.patch.object(ceiling, "_ancestor_args", return_value=args):
            self.assertIsNone(ceiling.launch_flag("--model"))

    def test_environment_effort_beats_settings(self):
        self.settings(effortLevel="low")
        with mock.patch.dict("os.environ", {"CLAUDE_CODE_EFFORT_LEVEL": "max"}):
            self.assertEqual(ceiling.resolve(None, None)["effort"], "max")

    def test_unknown_model_is_reported_as_unknown(self):
        got = ceiling.resolve(None, None)
        self.assertFalse(got["known"])
        self.assertIsNone(got["model"])

    def test_default_effort_comes_from_the_model(self):
        path = write_transcript(self.tmp / "t.jsonl", [assistant("ok", model="claude-opus-5-5")])
        self.assertEqual(ceiling.resolve(path, None)["effort"], "medium")


if __name__ == "__main__":
    unittest.main()
