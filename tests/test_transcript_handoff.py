import unittest

from token_beggar import handoff, transcript

from .helpers import Isolated, assistant, bash, edit, user


def session() -> list[dict]:
    return [
        user("Fix the parser and keep the tests green."),
        assistant("Looking.", [("Read", {"file_path": "/p/a.py"})], tokens=5000),
        assistant("Editing.", [edit("/p/a.py")], tokens=9000),
        assistant("Testing.", [bash("python3 -m unittest")], tokens=12000),
        assistant("One more.", [edit("/p/b.py")], tokens=20000),
    ]


class TranscriptTests(Isolated):
    def test_context_tokens_is_the_latest_request(self):
        self.assertEqual(transcript.context_tokens(session()), 20010)

    def test_sidechain_is_ignored(self):
        items = session() + [assistant("sub", tokens=999999, sidechain=True)]
        self.assertEqual(transcript.context_tokens(items), 20010)

    def test_user_prompts_skip_summaries_and_reminders(self):
        items = [user("real ask"), user("<system-reminder>x</system-reminder>"), user("This session is being continued from a previous one")]
        self.assertEqual(transcript.user_prompts(items), ["real ask"])

    def test_only_edits_after_the_last_check_are_unverified(self):
        self.assertEqual(transcript.unverified_edits(session()), ["/p/b.py"])

    def test_no_edits_after_a_check_means_nothing_unverified(self):
        self.assertEqual(transcript.unverified_edits(session()[:4]), [])

    def test_check_command_detection(self):
        for command in (
            "pytest -q",
            "npm run build",
            "ruff check .",
            "cargo test",
            "cd app && python3 -m unittest discover",
            "CI=1 make test",
            "uv run pytest",
        ):
            self.assertTrue(transcript.is_check_command(command), command)
        for command in ("ls -la", "ls tests", "cat tests/test_a.py", "git log --latest", "ls build/", "echo pytest"):
            self.assertFalse(transcript.is_check_command(command), command)

    def test_broken_lines_are_skipped(self):
        path = self.tmp / "t.jsonl"
        path.write_text('{"type": "user"}\nnot json\n')
        self.assertEqual(len(transcript.entries(path)), 1)
        self.assertEqual(transcript.entries(self.tmp / "missing.jsonl"), [])


class HandoffTests(Isolated):
    def test_note_keeps_the_task_files_and_open_edits(self):
        note = handoff.build(session(), "/p")
        self.assertIn("Fix the parser", note)
        self.assertIn("- /p/a.py", note)
        self.assertIn("## Edited since the last test, lint or build", note)
        self.assertIn("python3 -m unittest", note)

    def test_write_read_prune(self):
        path = handoff.write("abc", session())
        self.assertEqual(handoff.read("abc"), path.read_text())
        self.assertIsNone(handoff.read("missing"))
        import os
        import time

        old = time.time() - 30 * 86400
        os.utime(path, (old, old))
        handoff.prune(14)
        self.assertIsNone(handoff.read("abc"))

    def test_open_todos_are_listed(self):
        todos = [{"content": "ship it", "status": "in_progress"}, {"content": "done thing", "status": "completed"}]
        note = handoff.build(session() + [assistant("", [("TodoWrite", {"todos": todos})])])
        self.assertIn("ship it", note)
        self.assertNotIn("done thing", note)


if __name__ == "__main__":
    unittest.main()
