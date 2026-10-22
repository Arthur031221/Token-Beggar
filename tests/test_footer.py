import json
import os
from unittest import mock
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

from token_beggar import footer, transcript, usage
from token_beggar.__main__ import main

from .helpers import Isolated, assistant, edit, user, write_transcript

MATRIX = {
    "claude-opus-5-5": {
        "high": {"bulk-read": {"ratio": 4.0, "status": "measured"}, "edit": {"ratio": 0.5, "status": "measured"}, "read": {"ratio": 1.0}}
    }
}


def with_id(entry: dict, ident: str) -> dict:
    entry["message"]["id"] = ident
    return entry


def dispatch(call_id: str, agent_id: str, model: str = "haiku") -> tuple[dict, dict]:
    call = {
        "type": "assistant",
        "message": {
            "id": "m" + call_id,
            "role": "assistant",
            "model": "claude-opus-5-5",
            "usage": {"input_tokens": 100, "output_tokens": 10},
            "content": [
                {
                    "type": "tool_use",
                    "id": call_id,
                    "name": "Agent",
                    "input": {"model": model, "effort": "low", "subagent_type": "token-beggar:beggar-worker"},
                }
            ],
        },
    }
    result = {
        "type": "user",
        "toolUseResult": {"agentId": agent_id, "resolvedModel": "claude-haiku-5-5", "usage": {"input_tokens": 5, "output_tokens": 5}},
        "message": {"role": "user", "content": [{"type": "tool_result", "tool_use_id": call_id, "content": "ok"}]},
    }
    return call, result


def subagent_file(main: str, agent_id: str, calls: list[int]) -> None:
    folder = Path(main).with_suffix("") / "subagents"
    folder.mkdir(parents=True)
    rows = [{"type": "assistant", "message": {"id": f"s{i}", "usage": {"input_tokens": n, "output_tokens": 0}}} for i, n in enumerate(calls)]
    (folder / f"agent-{agent_id}.jsonl").write_text("\n".join(json.dumps(r) for r in rows))


class KindTests(Isolated):
    def test_kinds_come_from_the_prompt_and_the_edits(self):
        cases = [
            ("Summarise every module", set(), "bulk-read"),
            ("What does the parser do?", set(), "read"),
            ("Review this change", set(), "review"),
            ("Design the cache and weigh the trade-offs", set(), "design"),
            ("Fix the failing test", {"a.py"}, "bugfix"),
            ("Rename foo to bar", {"a.py"}, "edit"),
            ("Add a parse_window function", {"a.py"}, "function"),
            ("Add feature flags", {"a.py", "b.py", "c.py"}, "feature"),
        ]
        for prompt, files, kind in cases:
            self.assertEqual(footer.kind_of(prompt, files), kind, prompt)


class RatioTests(Isolated):
    def test_a_measured_cell_is_used_as_is(self):
        self.assertEqual(footer.ratio_for("claude-opus-5-5", "high", "bulk-read", MATRIX), (4.0, "measured"))

    def test_a_missing_effort_is_interpolated_from_the_nearest(self):
        ratio, status = footer.ratio_for("claude-opus-5-5", "medium", "bulk-read", MATRIX)
        self.assertEqual((ratio, status), (4.0, "interpolated"))

    def test_another_model_fills_in_when_this_one_has_no_data(self):
        self.assertEqual(footer.ratio_for("claude-sonnet-5-5", "high", "bulk-read", MATRIX), (4.0, "interpolated"))

    def test_the_pooled_ratio_is_quoted_not_the_noisy_cell(self):
        pool = {"claude-opus-5-5": {"bulk-read": {"ratio": 1.6}}}
        self.assertEqual(footer.ratio_for("claude-opus-5-5", "high", "bulk-read", MATRIX, pool), (1.6, "measured"))

    def test_a_pooled_ratio_for_an_unrun_effort_is_interpolated(self):
        pool = {"claude-opus-5-5": {"bulk-read": {"ratio": 1.6}}}
        self.assertEqual(footer.ratio_for("claude-opus-5-5", "medium", "bulk-read", MATRIX, pool), (1.6, "interpolated"))
        matrix = {"claude-opus-5-5": {"medium": {"bulk-read": {"ratio": 1.6, "status": "interpolated"}}}}
        self.assertEqual(footer.ratio_for("claude-opus-5-5", "medium", "bulk-read", matrix, pool), (1.6, "interpolated"))

    def test_no_data_gives_none(self):
        self.assertIsNone(footer.ratio_for("claude-opus-5-5", "high", "design", MATRIX))


OVERALL = {
    "claude-opus-5-5": {"high": {"ratio": 1.05}, "max": {"ratio": 1.3}, "low": {"ratio": 0.8}},
    "claude-sonnet-5-5": {"high": {"ratio": 1.0}},
}


class ModeCommandTests(Isolated):
    def run_mode(self, *args):
        out = StringIO()
        with redirect_stdout(out):
            self.assertEqual(main(["mode", *args]), 0)
        return out.getvalue()

    def test_it_states_the_mode_and_the_ratio_behind_it(self):
        os.environ.pop("TOKEN_BEGGAR_MODE")
        text = self.run_mode("--model", "sonnet", "--effort", "high")
        self.assertIn("sized", text)
        self.assertIn("0.85x", text)

    def test_all_lists_every_measured_model(self):
        os.environ.pop("TOKEN_BEGGAR_MODE")
        text = self.run_mode("--all")
        for name in ("fable", "opus", "sonnet", "haiku"):
            self.assertIn(name, text)


class ModeTests(Isolated):
    def setUp(self):
        super().setUp()
        os.environ.pop("TOKEN_BEGGAR_MODE")

    def mode(self, model, effort):
        return footer.mode(model, effort, OVERALL)

    def test_a_clear_saving_on_small_tasks_gets_the_full_menu(self):
        self.assertEqual(self.mode("claude-opus-5-5", "max"), "full")

    def test_anything_less_is_decided_by_the_size_of_the_task(self):
        for effort in ("low", "high"):
            self.assertEqual(self.mode("claude-opus-5-5", effort), "sized")
        self.assertEqual(self.mode("claude-sonnet-5-5", "high"), "sized")

    def test_the_cheapest_model_has_nothing_cheaper_to_send_work_to(self):
        self.assertEqual(self.mode("claude-haiku-5-5", "max"), "off")

    def test_an_unmeasured_model_keeps_the_full_menu(self):
        self.assertEqual(self.mode("claude-unknown", "high"), "full")
        self.assertEqual(footer.mode(None, "high", OVERALL), "full")

    def test_an_unmeasured_effort_uses_the_nearest_one(self):
        data = {"claude-opus-5-5": {"low": {"ratio": 0.8}, "max": {"ratio": 1.3}}}
        self.assertEqual(footer.mode("claude-opus-5-5", "xhigh", data), "full")  # the nearest measured effort is max
        self.assertEqual(footer.mode("claude-opus-5-5", "medium", data), "sized")  # the nearest is low

    def test_the_environment_forces_a_mode(self):
        os.environ["TOKEN_BEGGAR_MODE"] = "off"
        self.assertEqual(self.mode("claude-opus-5-5", "max"), "off")

    def test_the_shipped_data(self):
        for effort in ("low", "high", "max"):
            self.assertEqual(footer.mode("claude-haiku-5-5", effort), "off")
            self.assertEqual(footer.mode("claude-fable-5-1", effort), "full")
            self.assertEqual(footer.mode("claude-sonnet-5-5", effort), "sized" if effort != "max" else "sized")
        self.assertEqual(footer.mode("claude-opus-5-5", "high"), "sized")
        self.assertEqual(footer.mode("claude-opus-5-5", "max"), "full")


class UsageTests(Isolated):
    def test_a_message_logged_per_block_counts_once(self):
        a = with_id(assistant("x", tokens=500), "same")
        b = with_id(assistant("x", tokens=500), "same")
        path = write_transcript(self.tmp / "t.jsonl", [user("go"), a, b])
        window = usage.reply_window(transcript.entries(path))
        self.assertEqual(usage.tally(window, path)["main"], 510)

    def test_subagent_tokens_come_from_their_own_transcript(self):
        call, result = dispatch("c1", "ag1")
        path = write_transcript(self.tmp / "t.jsonl", [user("go"), call, result])
        subagent_file(path, "ag1", [1000, 2000, 3000])
        tally = usage.tally(usage.reply_window(transcript.entries(path)), path)
        self.assertEqual(tally["agents"], 6000)
        self.assertTrue(tally["dispatches"][0]["exact"])

    def test_without_the_file_the_parent_result_is_the_fallback(self):
        call, result = dispatch("c1", "ag1")
        path = write_transcript(self.tmp / "t.jsonl", [user("go"), call, result])
        tally = usage.tally(usage.reply_window(transcript.entries(path)), path)
        self.assertEqual(tally["agents"], 10)
        self.assertFalse(tally["dispatches"][0]["exact"])

    def test_only_the_latest_reply_is_counted(self):
        path = write_transcript(self.tmp / "t.jsonl", [user("one"), assistant("a", tokens=9000), user("two"), assistant("b", tokens=100)])
        self.assertEqual(usage.tally(usage.reply_window(transcript.entries(path)), path)["main"], 110)

    def test_ledger_rows_are_kept_per_session(self):
        usage.record("s1", kind="external", tool="agy", tokens=5)
        self.assertEqual(usage.ledger("s2"), [])
        self.assertEqual(usage.ledger("s1")[0]["tokens"], 5)


class FooterTests(Isolated):
    def payload(self, path, effort="high"):
        return {"session_id": "f1", "cwd": str(self.tmp), "transcript_path": path, "effort": {"level": effort}}

    def reply(self, prompt, extra=()):
        call, result = dispatch("c1", "ag1")
        path = write_transcript(self.tmp / "t.jsonl", [user(prompt), call, result, *extra, assistant("done", tokens=4000)])
        subagent_file(path, "ag1", [20000])
        return path

    def build(self, path, matrix=MATRIX, effort="high", pool=None):
        from unittest import mock

        top = {"model": "claude-opus-5-5", "effort": effort, "known": True}
        with (
            mock.patch.object(footer.ceiling_mod, "resolve", return_value=top),
            mock.patch.object(footer, "matrix", return_value=matrix),
            mock.patch.object(footer, "pooled", return_value=pool),
        ):
            return footer.build(self.payload(path, effort), transcript.entries(path))

    def test_no_dispatch_means_no_footer(self):
        path = write_transcript(self.tmp / "n.jsonl", [user("hi"), assistant("hello")])
        self.assertIsNone(self.build(path))

    def test_a_saving_is_claimed_in_quota_and_dollars_never_in_tokens(self):
        line = self.build(self.reply("Summarise every module"))
        self.assertTrue(line.startswith("Token Beggar: about 4.0x less quota than Opus 5.5 high alone, saved about $0.06 (est.)"), line)
        self.assertIn("routed 1: haiku low x1", line)
        self.assertNotIn("token", line.split("|")[0].replace("Token Beggar", ""))

    def test_the_footer_is_silent_where_the_skill_stands_down(self):
        os.environ["TOKEN_BEGGAR_MODE"] = "off"
        self.assertIsNone(self.build(self.reply("Summarise every module")))

    def test_a_sized_reply_uses_the_large_task_ratio_not_the_small_task_one(self):
        os.environ["TOKEN_BEGGAR_MODE"] = "sized"
        with mock.patch.object(footer, "_measured", return_value={"claude-opus-5-5": {"high": {"ratio": 1.6}}}):
            line = self.build(self.reply("Summarise every module"))
        self.assertTrue(line.startswith("Token Beggar: about 1.6x less quota than Opus 5.5 high alone"), line)
        self.assertIn("large task | routed 1", line)

    def test_a_sized_reply_without_a_large_task_ratio_gives_money_only(self):
        os.environ["TOKEN_BEGGAR_MODE"] = "sized"
        with mock.patch.object(footer, "_measured", return_value={}):
            line = self.build(self.reply("Summarise every module"))
        self.assertIn("no measured ratio for Opus 5.5 high on large tasks", line)
        self.assertNotIn("less quota", line)

    def test_a_large_task_ratio_under_the_claim_line_makes_no_claim(self):
        os.environ["TOKEN_BEGGAR_MODE"] = "sized"
        with mock.patch.object(footer, "_measured", return_value={"claude-opus-5-5": {"high": {"ratio": 1.05}}}):
            line = self.build(self.reply("Summarise every module"))
        self.assertIn("no measurable saving", line)

    def test_large_ratio_takes_the_nearest_effort_and_says_so(self):
        data = {"claude-opus-5-5": {"high": {"ratio": 1.4}}}
        self.assertEqual(footer.large_ratio("claude-opus-5-5", "high", data), (1.4, "measured"))
        self.assertEqual(footer.large_ratio("claude-opus-5-5", "xhigh", data), (1.4, "interpolated"))
        self.assertIsNone(footer.large_ratio("claude-sonnet-5-5", "high", data))

    def test_the_dollars_price_each_model_at_its_own_rate(self):
        call, result = dispatch("c1", "ag1")
        path = write_transcript(self.tmp / "p.jsonl", [user("Summarise every module"), call, result, assistant("done", tokens=0)])
        subagent_file(path, "ag1", [1_000_000])  # one million fresh input tokens on the haiku worker: $0.10, not an opus $4
        tally = usage.tally(usage.reply_window(transcript.entries(path)), path)
        self.assertAlmostEqual(tally["agents_cost"], 0.10, places=4)
        self.assertAlmostEqual(tally["main_cost"], (100 * 4 + 10 * 20 + 10 * 20) / 1e6, places=6)

    def test_cache_reads_and_writes_have_their_own_price(self):
        from token_beggar import catalog

        opus = catalog.find("opus")
        cost = opus.cost({"input_tokens": 0, "output_tokens": 0, "cache_read_input_tokens": 1_000_000, "cache_creation_input_tokens": 1_000_000})
        self.assertAlmostEqual(cost, opus.cache_read_per_mtok + opus.cache_write_per_mtok)
        self.assertLess(opus.cache_read_per_mtok, opus.input_per_mtok)

    def test_a_losing_kind_is_reported_honestly(self):
        line = self.build(self.reply("Rename foo to bar", [assistant("e", [edit("/p/a.py")], tokens=10)]))
        self.assertIn("alone would likely cost less", line)

    def test_edits_made_by_a_worker_still_count_as_an_edit_kind(self):
        line = self.build(self.reply("Rename foo to bar"))
        self.assertIn("alone would likely cost less", line)
        self.assertIn("exact edits", line)

    def test_interpolated_cells_are_labelled(self):
        self.assertIn("interpolated", self.build(self.reply("Summarise every module"), effort="medium"))

    def test_a_kind_without_data_states_the_cost_and_no_multiple(self):
        line = self.build(self.reply("Design the cache and weigh the trade-offs"))
        self.assertIn("no measured ratio", line)
        self.assertNotIn("x less quota", line)

    def test_a_ratio_below_the_noise_floor_states_no_multiple(self):
        pool = {"claude-opus-5-5": {"bulk-read": {"ratio": 1.05}}}
        line = self.build(self.reply("Summarise every module"), pool=pool)
        self.assertIn("no measurable saving", line)
        self.assertNotIn("1.05", line)

    def test_external_calls_are_named_and_add_no_cost_or_token_count(self):
        usage.record("f1", kind="external", tool="agy", model="gemini-3.8-flash-low", tokens=1500, source="reported")
        path = write_transcript(self.tmp / "e.jsonl", [user("Summarise every module"), assistant("ok", tokens=500)])
        line = self.build(path)
        self.assertIn("agy", line)
        self.assertIn("outside AI calls cost no Claude quota", line)
        self.assertNotIn("1.5k", line)

    def test_an_unfinished_transcript_gives_a_lower_bound(self):
        path = self.reply("Summarise every module")
        top = {"model": "claude-opus-5-5", "effort": "high", "known": True}
        from unittest import mock

        with (
            mock.patch.object(footer.ceiling_mod, "resolve", return_value=top),
            mock.patch.object(footer, "matrix", return_value=MATRIX),
            mock.patch.object(footer, "pooled", return_value=None),
        ):
            line = footer.build(self.payload(path), transcript.entries(path), complete=False)
        self.assertIn("saved at least ", line)

    def test_the_hook_waits_for_the_final_message(self):
        from token_beggar import hooks

        path = self.reply("Summarise every module")
        items = transcript.entries(path)
        self.assertTrue(hooks._settled(items, {"last_assistant_message": "done"}))
        self.assertFalse(hooks._settled(items, {"last_assistant_message": "a message that is not written yet"}))
        self.assertTrue(hooks._settled(items, {}))
