import io
import json
import unittest
from contextlib import redirect_stderr, redirect_stdout
from unittest import mock

from token_beggar import __main__ as cli
from token_beggar import card, hooks, inventory

from .helpers import Isolated, assistant, edit, user, write_transcript

OPUS_HIGH = {"model": "claude-opus-5-5", "alias": "opus", "tier": 3, "effort": "high", "effort_source": "--effort", "known": True}
BENCH = {"top_model": "claude-opus-5-5", "top_effort": "high", "classes": {"mechanical": {"cost_x": 4.2}, "reading": {"cost_x": 1.3}}}


def run_hook(event: str, payload: dict) -> tuple[int, str]:
    out = io.StringIO()
    with mock.patch("sys.stdin", io.StringIO(json.dumps(payload))), redirect_stdout(out), redirect_stderr(io.StringIO()):
        code = hooks.run(event)
    return code, out.getvalue()


class CardTests(Isolated):
    def test_card_states_the_ceiling_and_the_table(self):
        text = card.build(OPUS_HIGH, inventory.load())
        self.assertIn("claude-opus-5-5 at high", text)
        self.assertIn("mechanical | haiku", text)
        self.assertIn("debugging | opus | high | stay inline", text)

    def test_unknown_ceiling_asks_the_model_to_use_its_own(self):
        text = card.build({"model": None, "effort": "high", "known": False}, inventory.load())
        self.assertIn("never above your own model", text)

    def test_multiplier_only_for_the_benchmarked_model_and_effort(self):
        with mock.patch.object(card, "measured", return_value=BENCH):
            self.assertIn("mechanical 4.2x", card.footer_rule(OPUS_HIGH))
            self.assertNotIn("x less", card.footer_rule({**OPUS_HIGH, "effort": "low"}))
            self.assertNotIn("4.2x", card.footer_rule({**OPUS_HIGH, "model": "claude-sonnet-5-5"}))
            self.assertNotIn("x less", card.footer_rule({**OPUS_HIGH, "effort_source": "default"}))
            self.assertIn("Never write a multiplier that is not in that table", card.footer_rule(OPUS_HIGH))

    def test_a_class_inside_the_noise_gets_no_multiplier(self):
        bench = {**BENCH, "classes": {"review": {"cost_x": 1.07}, "mechanical": {"cost_x": 1.4}}}
        with mock.patch.object(card, "measured", return_value=bench):
            text = card.footer_rule(OPUS_HIGH)
        self.assertIn("mechanical 1.4x", text)
        self.assertNotIn("review 1.07x", text)

    def test_no_multiplier_without_a_benchmark(self):
        with mock.patch.object(card, "measured", return_value=None):
            self.assertIn("Give no multiplier", card.footer_rule(OPUS_HIGH))

    def test_exhausted_models_are_called_out(self):
        inventory.mark_exhausted("sonnet")
        self.assertIn("sonnet", card.build(OPUS_HIGH, inventory.load()).split("Out of quota")[1])


class HookTests(Isolated):
    def prompt(self, text="Refactor the whole payments module and add tests please", session="s1"):
        path = write_transcript(self.tmp / f"{session}.jsonl", [user(text)])
        return run_hook("prompt", {"prompt": text, "session_id": session, "cwd": str(self.tmp), "transcript_path": path})

    def test_first_prompt_gets_the_card_then_a_reminder(self):
        _, first = self.prompt()
        _, second = self.prompt()
        self.assertIn(card.MARKER, json.loads(first)["hookSpecificOutput"]["additionalContext"])
        self.assertEqual(json.loads(second)["hookSpecificOutput"]["additionalContext"], card.reminder())

    def test_card_is_sent_again_when_the_model_changes(self):
        sonnet = {"model": "claude-sonnet-5-5", "alias": "sonnet", "tier": 2, "effort": "high", "effort_source": "--effort", "known": True}
        with mock.patch.object(hooks.ceiling, "resolve", return_value={**OPUS_HIGH, "model": None, "known": False}):
            _, first = self.prompt()
        with mock.patch.object(hooks.ceiling, "resolve", return_value={**OPUS_HIGH, "model": None, "known": False}):
            _, same = self.prompt()
        with mock.patch.object(hooks.ceiling, "resolve", return_value=sonnet):
            _, changed = self.prompt()
        text = lambda out: json.loads(out)["hookSpecificOutput"]["additionalContext"]  # noqa: E731
        self.assertIn(card.MARKER, text(first))
        self.assertEqual(text(same), card.reminder())
        self.assertIn("claude-sonnet-5-5 at high", text(changed))

    def test_short_prompts_and_slash_commands_get_nothing(self):
        self.assertEqual(self.prompt("ok thanks")[1], "")
        self.assertEqual(self.prompt("/compact please summarise everything now")[1], "")

    def test_off_switch(self):
        with mock.patch.dict("os.environ", {"TOKEN_BEGGAR": "off"}):
            self.assertEqual(self.prompt()[1], "")
        (hooks.paths.home() / "off").touch()
        self.assertEqual(self.prompt(session="s2")[1], "")

    def test_a_broken_payload_never_breaks_the_session(self):
        out = io.StringIO()
        with mock.patch("sys.stdin", io.StringIO("{not json")), redirect_stdout(out):
            self.assertEqual(hooks.run("prompt"), 0)

    def test_errors_are_logged_not_raised(self):
        with mock.patch.object(hooks.ceiling, "resolve", side_effect=RuntimeError("boom")):
            code, _ = self.prompt(session="s3")
        self.assertEqual(code, 0)
        self.assertIn("boom", (hooks.paths.home() / "errors.log").read_text())

    def test_precompact_exit_code_defers(self):
        self.settings(env={"CLAUDE_CODE_AUTO_COMPACT_WINDOW": "400000"})
        path = write_transcript(self.tmp / "p.jsonl", [user("x"), assistant("e", [edit("/p/a.py")], tokens=410_000)])
        code, _ = run_hook("precompact", {"session_id": "s9", "trigger": "auto", "cwd": str(self.tmp), "transcript_path": path})
        self.assertEqual(code, 2)

    def test_session_start_after_compaction_reinjects_card_and_note(self):
        path = write_transcript(self.tmp / "c.jsonl", [user("big job"), assistant("e", [edit("/p/a.py")])])
        run_hook("precompact", {"session_id": "s8", "trigger": "manual", "cwd": str(self.tmp), "transcript_path": path})
        _, out = run_hook("sessionstart", {"session_id": "s8", "source": "compact", "cwd": str(self.tmp), "transcript_path": path})
        text = json.loads(out)["hookSpecificOutput"]["additionalContext"]
        self.assertIn(card.MARKER, text)
        self.assertIn("big job", text)

    def test_context_warning_rides_on_the_prompt(self):
        self.settings(env={"CLAUDE_CODE_AUTO_COMPACT_WINDOW": "100000"})
        path = write_transcript(self.tmp / "w.jsonl", [assistant("x", tokens=95_000)])
        _, out = run_hook(
            "prompt", {"prompt": "Carry on with the migration of all modules", "session_id": "s7", "cwd": str(self.tmp), "transcript_path": path}
        )
        self.assertIn("compaction point", json.loads(out)["hookSpecificOutput"]["additionalContext"])


class CliTests(Isolated):
    def run_cli(self, *argv: str) -> str:
        out = io.StringIO()
        with redirect_stdout(out):
            cli.main(list(argv))
        return out.getvalue()

    def test_route_json(self):
        data = json.loads(self.run_cli("route", "--model", "opus", "--effort", "high", "--json"))
        self.assertEqual(data["ceiling"]["effort"], "high")
        self.assertEqual(len(data["routes"]), 7)

    def test_exhausted_round_trip(self):
        self.assertIn("opus", self.run_cli("exhausted", "opus"))
        self.assertEqual(self.run_cli("exhausted", "--clear").strip(), "{}")

    def test_env_lists_the_variables_and_the_state_directory(self):
        text = self.run_cli("env")
        self.assertIn("TOKEN_BEGGAR_HOME", text)
        self.assertIn("state directory:", text)

    def test_window(self):
        self.assertIn("not set", self.run_cli("window"))
        with mock.patch.dict("os.environ", {"CLAUDE_CODE_AUTO_COMPACT_WINDOW": "100k"}):
            self.assertEqual(self.run_cli("window").strip(), "100000")


if __name__ == "__main__":
    unittest.main()
