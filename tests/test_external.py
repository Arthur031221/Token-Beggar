import json
import os
import stat
from unittest import mock

from token_beggar import external, inventory, profiles, usage

from .helpers import Isolated


class FakeCli(Isolated):
    """A stand-in for an external AI on PATH. The real tools are never called."""

    def fake(self, name: str, body: str) -> None:
        bin_dir = self.tmp / "bin"
        bin_dir.mkdir(exist_ok=True)
        script = bin_dir / name
        script.write_text("#!/bin/sh\n" + body + "\n")
        script.chmod(script.stat().st_mode | stat.S_IEXEC)
        patcher = mock.patch.dict(os.environ, {"PATH": f"{bin_dir}:{os.environ['PATH']}"})
        patcher.start()
        self.addCleanup(patcher.stop)


class CapTests(Isolated):
    def test_caps_are_read_from_the_prompt(self):
        self.assertEqual(external.parse_caps("use agy max flash and no gemini"), {"agy": "flash", "gemini": "off"})
        self.assertEqual(external.parse_caps("nothing special here"), {})

    def test_a_family_cap_allows_only_that_family(self):
        caps = {"agy": "flash"}
        self.assertTrue(external.allowed("agy", "gemini-3.8-flash-low", caps))
        self.assertFalse(external.allowed("agy", "gpt-oss-120b-medium", caps))
        self.assertFalse(external.allowed("agy", "claude-opus-4-6-thinking", caps))

    def test_a_level_cap_compares_levels(self):
        caps = {"agy": "medium"}
        self.assertTrue(external.allowed("agy", "gemini-3.8-flash-low", caps))
        self.assertTrue(external.allowed("agy", "gemini-3.8-flash-medium", caps))
        self.assertFalse(external.allowed("agy", "gemini-3.8-flash-high", caps))

    def test_off_blocks_everything_and_none_lifts_it(self):
        self.assertFalse(external.allowed("gemini", "default", {"gemini": "off"}))
        self.assertTrue(external.allowed("gemini", "default", {}))
        external.save_caps("s", {"gemini": "off"})
        external.save_caps("s", {"gemini": "none"})
        self.assertEqual(external.load_caps("s"), {})

    def test_an_unknown_word_allows_only_the_weakest_model(self):
        self.assertTrue(external.allowed("agy", "gemini-3.8-flash-low", {"agy": "nano"}))
        self.assertFalse(external.allowed("agy", "gemini-3.8-flash-high", {"agy": "nano"}))


class ParseTests(Isolated):
    def test_quota_text_gives_the_reset_time(self):
        kind, hours = external.classify("Error: usage limit reached. Your limit will reset in 2h 30m.")
        self.assertEqual(kind, "quota")
        self.assertAlmostEqual(hours, 2.5, places=2)

    def test_quota_without_a_time_waits_five_hours(self):
        self.assertEqual(external.classify("429 Too Many Requests"), ("quota", 5.0))

    def test_auth_errors_are_not_quota(self):
        self.assertEqual(external.classify("IneligibleTierError: not logged in")[0], "auth")

    def test_other_errors_are_plain_errors(self):
        self.assertEqual(external.classify("segfault"), ("error", 0.0))

    def test_agy_json_reports_tokens(self):
        raw = json.dumps({"response": " ok ", "usage": {"total_tokens": 321}})
        self.assertEqual(external.parse_output("agy", raw), ("ok", 321))

    def test_plain_text_has_no_token_count(self):
        self.assertEqual(external.parse_output("codex", "hello\n"), ("hello", None))

    def test_commands_per_tool(self):
        self.assertEqual(external.build_command("agy", "p", "m")[:5], ["agy", "-p", "p", "--model", "m"])
        self.assertIn("-m", external.build_command("gemini", "p", "gemini-pro"))
        self.assertIn("read-only", external.build_command("codex", "p", None))
        with self.assertRaises(ValueError):
            external.build_command("nope", "p", None)


class AskTests(FakeCli):
    def test_a_good_answer_is_returned_and_counted(self):
        self.fake("agy", """echo '{"response": "done", "usage": {"total_tokens": 900}}'""")
        result = external.ask("agy", "summarise", "gemini-3.8-flash-low", session_id="a1")
        self.assertTrue(result["ok"])
        self.assertEqual((result["text"], result["tokens"], result["tokens_source"]), ("done", 900, "reported"))
        rows = usage.ledger("a1")
        self.assertEqual(rows[0]["kind"], "external")
        self.assertEqual(rows[0]["tokens"], 900)

    def test_tokens_are_estimated_when_the_tool_reports_none(self):
        self.fake("gemini", "echo plain answer")
        result = external.ask("gemini", "x" * 400, session_id="a2")
        self.assertEqual(result["tokens_source"], "estimated")
        self.assertGreater(result["tokens"], 100)

    def test_the_helper_runs_in_an_empty_directory(self):
        self.fake("agy", """ls -A | wc -l | sed 's/^/{"response":"files:/;s/$/"}/'""")
        self.assertEqual(external.ask("agy", "list")["text"], "files:0")

    def test_a_quota_error_marks_the_model_out_and_skips_later_calls(self):
        self.fake("agy", "echo 'quota exceeded, resets in 3h' >&2; exit 1")
        first = external.ask("agy", "x", "gemini-3.8-flash-low")
        self.assertEqual(first["kind"], "quota")
        self.assertIn("agy:gemini-3.8-flash-low", profiles.exhausted(inventory.load()))
        self.assertEqual(external.ask("agy", "x", "gemini-3.8-flash-low")["kind"], "quota")

    def test_a_capped_model_is_refused_before_running(self):
        self.fake("agy", "echo should not run; exit 1")
        external.save_caps("c1", {"agy": "flash"})
        self.assertEqual(external.ask("agy", "x", "gpt-oss-120b-medium", session_id="c1")["kind"], "capped")

    def test_secret_files_and_keys_are_refused(self):
        self.fake("agy", "echo should not run")
        env_file = self.tmp / ".env"
        env_file.write_text("A=1")
        self.assertEqual(external.ask("agy", "read", files=[str(env_file)])["kind"], "secret")
        self.assertEqual(external.ask("agy", "key sk-" + "a" * 30)["kind"], "secret")

    def test_a_missing_tool_is_reported(self):
        with mock.patch.dict(os.environ, {"PATH": str(self.tmp)}):
            self.assertEqual(external.ask("agy", "x")["kind"], "missing")

    def test_files_are_sent_in_the_prompt(self):
        self.fake("agy", """printf '{"response": "%s"}' "$(echo "$2" | grep -c 'FILE')" """)
        note = self.tmp / "notes.txt"
        note.write_text("hello")
        self.assertEqual(external.ask("agy", "read", files=[str(note)])["text"], "1")

    def test_globs_and_directories_expand_to_plain_files(self):
        folder = self.tmp / "pkg"
        (folder / "__pycache__").mkdir(parents=True)
        (folder / "a.py").write_text("a")
        (folder / "b.py").write_text("b")
        (folder / ".hidden").write_text("x")
        (folder / "__pycache__" / "a.pyc").write_text("x")
        self.assertEqual(external.expand([str(folder)]), [str(folder / "a.py"), str(folder / "b.py")])
        self.assertEqual(external.expand([str(folder / "*.py")]), [str(folder / "a.py"), str(folder / "b.py")])
        self.fake("agy", """printf '{"response": "%s"}' "$(echo "$2" | grep -c 'FILE')" """)
        self.assertEqual(external.ask("agy", "read", files=[str(folder / "*.py")])["text"], "2")
