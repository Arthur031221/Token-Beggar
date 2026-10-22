import json
import os
import time

from token_beggar import stats
from token_beggar.__main__ import main

from .helpers import Isolated, assistant, user, write_transcript


def spawn(call: str, model: str = "claude-opus-5-5") -> dict:
    entry = assistant(tools=[("Agent", {"subagent_type": "token-beggar:beggar-worker"})], model=model)
    entry["message"]["content"][-1]["id"] = call
    return entry


def finished(call: str, agent: str = "a1", worker: str = "claude-haiku-5-5", agent_type: str = "token-beggar:beggar-worker", **usage) -> dict:
    usage = usage or {"input_tokens": 1000, "output_tokens": 1000}
    return {
        "type": "user",
        "message": {"role": "user", "content": [{"type": "tool_result", "tool_use_id": call, "content": "done"}]},
        "toolUseResult": {"agentType": agent_type, "agentId": agent, "resolvedModel": worker, "usage": usage},
    }


class StatsTests(Isolated):
    def project(self, name: str, items: list[dict], age_days: float = 0):
        folder = self.tmp / "claude" / "projects" / "p"
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / f"{name}.jsonl"
        write_transcript(path, items)
        if age_days:
            old = time.time() - age_days * 86400
            os.utime(path, (old, old))
        return path

    def test_prices_a_worker_against_the_chat_model(self):
        self.project("s", [user("go"), spawn("c1"), finished("c1")])
        data = stats.summarize(stats.transcripts(7))
        row = data["workers"]["haiku"]
        self.assertEqual((row["runs"], row["tokens"]), (1, 2000))
        self.assertAlmostEqual(row["worker_usd"], (1000 * 0.1 + 1000 * 0.5) / 1e6)
        self.assertAlmostEqual(row["chat_usd"], (1000 * 4.0 + 1000 * 20.0) / 1e6)

    def test_cached_tokens_use_the_cache_prices(self):
        self.project("s", [spawn("c1"), finished("c1", cache_read_input_tokens=1000, cache_creation_input_tokens=1000)])
        row = stats.summarize(stats.transcripts(7))["workers"]["haiku"]
        self.assertAlmostEqual(row["worker_usd"], 1000 * (0.01 + 0.2) / 1e6)

    def test_counts_each_agent_once_and_ignores_other_agents(self):
        items = [spawn("c1"), finished("c1"), finished("c1"), finished("c1", agent="b", agent_type="Explore")]
        self.project("s", items)
        self.assertEqual(stats.summarize(stats.transcripts(7))["total"]["runs"], 1)

    def test_background_launch_without_usage_is_not_counted(self):
        launch = finished("c1")
        del launch["toolUseResult"]["usage"]
        self.project("s", [spawn("c1"), launch])
        self.assertEqual(stats.summarize(stats.transcripts(7))["total"]["runs"], 0)

    def test_old_sessions_are_left_out(self):
        self.project("new", [spawn("c1"), finished("c1")])
        self.project("old", [spawn("c1"), finished("c1")], age_days=30)
        self.assertEqual(stats.summarize(stats.transcripts(7))["sessions"], 1)

    def test_unknown_models_are_reported_not_priced(self):
        self.project("s", [spawn("c1"), finished("c1", worker="some-other-model")])
        data = stats.summarize(stats.transcripts(7))
        self.assertEqual((data["total"]["runs"], data["skipped"]), (0, 1))
        self.assertIn("missing from the catalog", stats.render(data, 7))

    def test_run_whose_spawning_call_is_missing_is_reported_not_priced(self):
        self.project("s", [finished("nope")])
        self.assertEqual(stats.summarize(stats.transcripts(7))["skipped"], 1)

    def test_same_agent_in_two_files_counts_once(self):
        for name in ("a", "b"):
            self.project(name, [spawn("c1"), finished("c1")])
        self.assertEqual(stats.summarize(stats.transcripts(7))["total"]["runs"], 1)

    def test_null_usage_fields_do_not_crash(self):
        self.project("s", [spawn("c1"), finished("c1", input_tokens=None, output_tokens=10)])
        self.assertEqual(stats.summarize(stats.transcripts(7))["total"]["tokens"], 10)

    def test_empty_history_says_so(self):
        self.assertIn("No Token Beggar workers", stats.render(stats.summarize([]), 7))

    def test_command_prints_json(self):
        self.project("s", [spawn("c1"), finished("c1")])
        from contextlib import redirect_stdout
        from io import StringIO

        out = StringIO()
        with redirect_stdout(out):
            self.assertEqual(main(["stats", "--json"]), 0)
        self.assertEqual(json.loads(out.getvalue())["total"]["runs"], 1)
