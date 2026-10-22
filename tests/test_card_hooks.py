import io
import json
import os
import unittest
from contextlib import redirect_stderr, redirect_stdout
from unittest import mock

from token_beggar import __main__ as cli
from token_beggar import card, hooks, inventory

from .helpers import Isolated, assistant, edit, user, write_transcript

OPUS_HIGH = {"model": "claude-opus-5-5", "alias": "opus", "tier": 3, "effort": "high", "effort_source": "--effort", "known": True}


def run_hook(event: str, payload: dict) -> tuple[int, str]:
    out = io.StringIO()
    with mock.patch("sys.stdin", io.StringIO(json.dumps(payload))), redirect_stdout(out), redirect_stderr(io.StringIO()):
        code = hooks.run(event)
    return code, out.getvalue()


class CardTests(Isolated):
    def test_card_states_the_ceiling_and_lists_the_menu(self):
        text = card.build(OPUS_HIGH, inventory.load())
        self.assertIn("claude-opus-5-5 at high", text)
        self.assertIn("claude haiku (cap 2", text)
        self.assertIn("claude opus (cap 4", text)
        self.assertNotIn("claude fable", text)  # above the ceiling

    def test_card_has_no_fixed_table(self):
        text = card.build(OPUS_HIGH, inventory.load())
        self.assertNotIn("class | model | effort", text)
        self.assertIn("split it into subtasks", text)
        self.assertIn("Stay inline only", text)

    def test_unknown_ceiling_asks_the_model_to_use_its_own(self):
        text = card.build({"model": None, "effort": "high", "known": False}, inventory.load())
        self.assertIn("at or below your own", text)

    def test_the_card_leaves_the_footer_to_the_hook(self):
        self.assertIn("Do not write one", card.build(OPUS_HIGH, inventory.load()))

    def test_external_ais_are_listed_with_caps_applied(self):
        inv = {
            "claude": ["haiku", "sonnet", "opus"],
            "external": [{"name": "agy", "kind": "cli", "models": ["gemini-3.8-flash-low", "gpt-oss-120b-medium"]}],
        }
        text = card.build(OPUS_HIGH, inv, {"agy": "flash"})
        self.assertIn("gemini-3.8-flash-low", text)
        self.assertNotIn("gpt-oss", text)
        self.assertIn("User caps for this session: agy flash", text)
        self.assertIn("ask <tool>", text)

    def test_an_mcp_route_is_named(self):
        inv = {"claude": ["haiku"], "external": [{"name": "gemini-mcp", "kind": "mcp", "models": []}]}
        self.assertIn("gemini-mcp (MCP server)", card.build(OPUS_HIGH, inv))

    def test_exhausted_models_are_called_out(self):
        inventory.mark_exhausted("sonnet")
        text = card.build(OPUS_HIGH, inventory.load())
        self.assertIn("sonnet", text.split("Out of quota")[1])
        self.assertNotIn("claude sonnet (", text)


class ModeHookTests(Isolated):
    def prompt(self, mode, session="m1", model="claude-opus-5-5"):
        text = "Refactor the whole payments module and add tests please"
        path = write_transcript(self.tmp / f"{session}.jsonl", [user(text)])
        with mock.patch.dict("os.environ", {"TOKEN_BEGGAR_MODE": mode}):
            return run_hook("prompt", {"prompt": text, "session_id": session, "cwd": str(self.tmp), "transcript_path": path})[1]

    def test_off_adds_no_card_and_no_reminder(self):
        self.assertEqual(self.prompt("off"), "")
        self.assertEqual(self.prompt("off"), "")

    def test_sized_is_one_short_card_that_decides_by_size_and_has_no_reminders(self):
        first = json.loads(self.prompt("sized"))["hookSpecificOutput"]["additionalContext"]
        self.assertIn(card.MARKER, first)
        for word in ("SMALL", "LARGE", "inline", "exploring", "mechanical edits", "report under 150 words"):
            self.assertIn(word, first)
        self.assertNotIn("Menu:", first)
        self.assertLess(len(first), 1700)
        self.assertEqual(self.prompt("sized"), "")

    def test_sized_names_a_worker_one_tier_below_the_ceiling(self):
        self.assertIn("model sonnet, effort medium", card.sized(OPUS_HIGH, inventory.load()))

    def test_sized_mentions_an_outside_ai_only_when_one_is_installed(self):
        self.assertNotIn("100k", card.sized(OPUS_HIGH, {"claude": ["sonnet"], "external": []}))
        inv = {"claude": ["sonnet"], "external": [{"name": "agy", "kind": "cli", "models": []}]}
        self.assertIn("names it or one job reads about 100k", card.sized(OPUS_HIGH, inv))

    def test_at_max_effort_the_card_suggests_a_lower_effort(self):
        max_top = {**OPUS_HIGH, "effort": "max"}
        self.assertIn("lower effort", card.sized(max_top, inventory.load()))
        self.assertIn("lower effort", card.build(max_top, inventory.load()))
        self.assertNotIn("lower effort", card.sized(OPUS_HIGH, inventory.load()))

    def test_full_is_the_whole_menu(self):
        self.assertIn("Menu:", json.loads(self.prompt("full"))["hookSpecificOutput"]["additionalContext"])


class GrowthTests(Isolated):
    """A reply that starts small and keeps going is treated as large for the rest of it."""

    def setUp(self):
        super().setUp()
        os.environ["TOKEN_BEGGAR_MODE"] = "sized"
        self.path = write_transcript(self.tmp / "g.jsonl", [user("fix the failing import please")])

    def step(self, **extra):
        payload = {"session_id": "g1", "cwd": str(self.tmp), "transcript_path": self.path, "tool_name": "Read", **extra}
        return run_hook("posttool", payload)[1]

    def prompt(self):
        run_hook("prompt", {"prompt": "fix the failing import please", "session_id": "g1", "cwd": str(self.tmp), "transcript_path": self.path})

    def test_said_once_when_the_step_limit_is_reached(self):
        self.prompt()
        for _ in range(card.GROW_STEPS - 1):
            self.assertEqual(self.step(), "")
        said = json.loads(self.step())["hookSpecificOutput"]["additionalContext"]
        self.assertIn("no longer small", said)
        self.assertEqual(self.step(), "")

    def test_a_reply_that_already_used_a_worker_is_not_told(self):
        self.prompt()
        self.step(tool_name="Agent", tool_input={"subagent_type": "token-beggar:beggar-worker"})
        for _ in range(card.GROW_STEPS + 2):
            self.assertEqual(self.step(), "")

    def test_a_worker_own_tool_calls_do_not_count(self):
        self.prompt()
        for _ in range(card.GROW_STEPS + 2):
            self.assertEqual(self.step(agent_id="a1"), "")

    def test_a_new_prompt_starts_the_count_again(self):
        self.prompt()
        for _ in range(card.GROW_STEPS):
            self.step()
        self.prompt()
        self.assertEqual(self.step(), "")

    def test_a_long_context_counts_as_large(self):
        self.path = write_transcript(self.tmp / "g.jsonl", [user("x"), assistant("a", tokens=card.GROW_CONTEXT + 1000)])
        self.prompt()
        self.assertIn("no longer small", self.step())

    def test_full_mode_says_nothing_about_growth(self):
        os.environ["TOKEN_BEGGAR_MODE"] = "full"
        self.prompt()
        for _ in range(card.GROW_STEPS + 2):
            self.assertEqual(self.step(), "")


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
        path = write_transcript(self.tmp / "p.jsonl", [user("x"), assistant("e", [edit("/p/a.py")], tokens=970_000)])
        code, _ = run_hook("precompact", {"session_id": "s9", "trigger": "auto", "cwd": str(self.tmp), "transcript_path": path})
        self.assertEqual(code, 2)

    def test_session_start_after_compaction_reinjects_card_and_note(self):
        path = write_transcript(self.tmp / "c.jsonl", [user("big job"), assistant("e", [edit("/p/a.py")])])
        run_hook("precompact", {"session_id": "s8", "trigger": "manual", "cwd": str(self.tmp), "transcript_path": path})
        _, out = run_hook("sessionstart", {"session_id": "s8", "source": "compact", "cwd": str(self.tmp), "transcript_path": path})
        text = json.loads(out)["hookSpecificOutput"]["additionalContext"]
        self.assertIn(card.MARKER, text)
        self.assertIn("big job", text)

    def test_user_caps_in_the_prompt_are_recorded_and_shown(self):
        self.prompt("Summarise every module, using agy max flash and no gemini please", session="cap1")
        _, out = self.prompt("Now also look at the tests folder carefully please", session="cap1")
        self.assertEqual(hooks.external.load_caps("cap1"), {"agy": "flash", "gemini": "off"})
        _, again = self.prompt("Okay, lift that: agy max none for the rest of this job", session="cap1")
        self.assertEqual(hooks.external.load_caps("cap1"), {"gemini": "off"})
        self.assertIn("User caps now", json.loads(again)["hookSpecificOutput"]["additionalContext"])

    def test_context_warning_rides_on_the_prompt(self):
        self.settings(env={"CLAUDE_CODE_AUTO_COMPACT_WINDOW": "100000"})
        path = write_transcript(self.tmp / "w.jsonl", [assistant("x", tokens=95_000)])
        _, out = run_hook(
            "prompt", {"prompt": "Carry on with the migration of all modules", "session_id": "s7", "cwd": str(self.tmp), "transcript_path": path}
        )
        self.assertIn("compaction point", json.loads(out)["hookSpecificOutput"]["additionalContext"])


class AgentClampTests(Isolated):
    def call(self, tool_input, ceiling_dict=OPUS_HIGH):
        path = write_transcript(self.tmp / "a.jsonl", [user("x")])
        with mock.patch.object(hooks.ceiling, "resolve", return_value=ceiling_dict):
            _, out = run_hook("pretool", {"session_id": "a", "cwd": str(self.tmp), "transcript_path": path, "tool_input": tool_input})
        return json.loads(out)["hookSpecificOutput"]["updatedInput"] if out else None

    WORKER = "token-beggar:beggar-worker"

    def test_a_model_above_the_ceiling_is_lowered(self):
        sonnet = {**OPUS_HIGH, "model": "claude-sonnet-5-5", "alias": "sonnet", "tier": 2}
        fixed = self.call({"subagent_type": self.WORKER, "model": "opus", "effort": "high"}, sonnet)
        self.assertEqual(fixed["model"], "sonnet")

    def test_an_effort_above_the_ceiling_is_lowered(self):
        medium = {**OPUS_HIGH, "effort": "medium"}
        self.assertEqual(self.call({"subagent_type": self.WORKER, "model": "haiku", "effort": "max"}, medium)["effort"], "medium")

    def test_a_call_inside_the_ceiling_is_left_alone(self):
        self.assertIsNone(self.call({"subagent_type": self.WORKER, "model": "haiku", "effort": "low"}))

    def test_other_agents_are_not_touched(self):
        self.assertIsNone(self.call({"subagent_type": "Explore", "model": "fable"}))

    def test_a_model_out_of_quota_is_swapped_for_a_cheaper_one(self):
        inventory.mark_exhausted("sonnet")
        self.assertEqual(self.call({"subagent_type": self.WORKER, "model": "sonnet", "effort": "low"})["model"], "haiku")


class PostToolTests(Isolated):
    def test_the_compaction_check_runs_during_a_long_turn(self):
        self.settings(env={"CLAUDE_CODE_AUTO_COMPACT_WINDOW": "100000"})
        path = write_transcript(self.tmp / "w.jsonl", [user("x"), assistant("x", tokens=65_000)])
        _, out = run_hook("posttool", {"session_id": "pt", "cwd": str(self.tmp), "transcript_path": path})
        self.assertIn("compaction point", json.loads(out)["hookSpecificOutput"]["additionalContext"])
        _, quiet = run_hook("posttool", {"session_id": "pt", "cwd": str(self.tmp), "transcript_path": path})
        self.assertEqual(quiet, "")

    def test_a_worker_that_hits_a_usage_limit_marks_its_model_out_of_quota(self):
        path = write_transcript(self.tmp / "q.jsonl", [user("x"), assistant("x", tokens=1_000)])
        payload = {
            "session_id": "qq",
            "cwd": str(self.tmp),
            "transcript_path": path,
            "tool_name": "Agent",
            "tool_input": {"subagent_type": "token-beggar:beggar-worker", "model": "sonnet"},
            "tool_response": "You have hit your usage limit. It will reset in 2h 30m.",
        }
        _, out = run_hook("posttool", payload)
        self.assertIn("marked sonnet out of quota", json.loads(out)["hookSpecificOutput"]["additionalContext"])
        self.assertIn("sonnet", inventory.exhausted_aliases(inventory.load()))

    def test_an_ordinary_worker_result_marks_nothing(self):
        path = write_transcript(self.tmp / "o.jsonl", [user("x"), assistant("x", tokens=1_000)])
        payload = {
            "session_id": "oo",
            "cwd": str(self.tmp),
            "transcript_path": path,
            "tool_name": "Agent",
            "tool_input": {"subagent_type": "token-beggar:beggar-worker", "model": "haiku"},
            "tool_response": "Edited two files, tests pass.",
        }
        self.assertEqual(run_hook("posttool", payload)[1], "")
        self.assertEqual(inventory.exhausted_aliases(inventory.load()), set())

    def test_a_small_context_costs_nothing(self):
        path = write_transcript(self.tmp / "s.jsonl", [user("x"), assistant("x", tokens=5_000)])
        self.assertEqual(run_hook("posttool", {"session_id": "q", "cwd": str(self.tmp), "transcript_path": path})[1], "")

    def test_a_long_context_gets_the_phase_question_once(self):
        path = write_transcript(self.tmp / "l.jsonl", [user("x"), assistant("x", tokens=170_000)])
        payload = {"session_id": "ll", "cwd": str(self.tmp), "transcript_path": path}
        first = json.loads(run_hook("posttool", payload)[1])["hookSpecificOutput"]["additionalContext"]
        self.assertIn("--phase-done", first)
        self.assertEqual(run_hook("posttool", payload)[1], "")

    def test_the_deferral_is_announced_after_the_next_tool_call(self):
        path = write_transcript(self.tmp / "d.jsonl", [user("x"), assistant("e", [edit("/p/a.py")], tokens=970_000)])
        run_hook("precompact", {"session_id": "dd", "trigger": "auto", "cwd": str(self.tmp), "transcript_path": path})
        _, out = run_hook("posttool", {"session_id": "dd", "cwd": str(self.tmp), "transcript_path": path})
        self.assertIn("deferred", json.loads(out)["hookSpecificOutput"]["additionalContext"])


class CliTests(Isolated):
    def run_cli(self, *argv: str) -> str:
        out = io.StringIO()
        with redirect_stdout(out):
            cli.main(list(argv))
        return out.getvalue()

    def test_menu_json(self):
        data = json.loads(self.run_cli("menu", "--model", "opus", "--effort", "high", "--json"))
        self.assertEqual(data["ceiling"]["effort"], "high")
        self.assertEqual({r["model"] for r in data["claude"]}, {"haiku", "sonnet", "opus"})

    def test_exhausted_round_trip(self):
        self.assertIn("opus", self.run_cli("exhausted", "opus"))
        self.assertEqual(self.run_cli("exhausted", "--clear").strip(), "{}")

    def test_env_lists_the_variables_and_the_state_directory(self):
        text = self.run_cli("env")
        self.assertIn("TOKEN_BEGGAR_HOME", text)
        self.assertIn("state directory:", text)

    def test_window_works_with_nothing_set(self):
        text = self.run_cli("window", "--model", "opus")
        self.assertIn("967,000", text)
        self.assertIn("model default", text)
        with mock.patch.dict("os.environ", {"CLAUDE_CODE_AUTO_COMPACT_WINDOW": "100k"}):
            self.assertIn("67,000", self.run_cli("window", "--model", "opus"))

    def test_note_cli_writes_the_models_note(self):
        with mock.patch("sys.stdin", io.StringIO("Goal: ship. Next: run tests.")):
            self.run_cli("note", "--mid-step", "--session", "sx")
        saved = hooks.compact.handoff.read_model("sx")
        self.assertTrue(saved["mid_step"])
        self.assertIn("Next: run tests", saved["text"])
        self.run_cli("note", "--clean", "--session", "sx", "all", "done")
        self.assertFalse(hooks.compact.handoff.read_model("sx")["mid_step"])

    def test_note_reads_the_session_id_from_the_environment(self):
        with mock.patch.dict("os.environ", {"CLAUDE_CODE_SESSION_ID": "envsess"}):
            self.run_cli("note", "--clean", "text")
        self.assertIsNotNone(hooks.compact.handoff.read_model("envsess"))

    def test_cap_cli(self):
        self.run_cli("cap", "agy", "flash", "--session", "sc")
        self.run_cli("cap", "gemini", "--session", "sc")
        self.assertEqual(json.loads(self.run_cli("cap", "--session", "sc")), {"agy": "flash", "gemini": "off"})


if __name__ == "__main__":
    unittest.main()
