import os
import subprocess
import sys
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest import mock

from token_beggar import doctor, paths
from token_beggar.__main__ import main

from .helpers import Isolated


def statuses() -> dict[str, str]:
    return {name: status for name, status, _ in doctor.run()}


class DoctorTests(Isolated):
    def test_clean_setup_has_no_failures(self):
        self.settings(model="claude-opus-5-5")
        found = statuses()
        self.assertNotIn(doctor.FAIL, found.values())
        self.assertEqual(found["hook entry"], doctor.OK)

    def test_subagent_model_override_is_flagged(self):
        with mock.patch.dict(os.environ, {"CLAUDE_CODE_SUBAGENT_MODEL": "haiku"}):
            self.assertEqual(statuses()["worker model override"], doctor.WARN)

    def test_off_switch_is_flagged(self):
        (paths.home() / "off").write_text("")
        self.assertEqual(statuses()["switch"], doctor.WARN)

    def test_unknown_chat_model_and_missing_window_are_flagged(self):
        found = statuses()
        self.assertEqual((found["ceiling"], found["compaction window"]), (doctor.WARN, doctor.WARN))

    def test_hook_errors_are_surfaced(self):
        (paths.home() / "errors.log").write_text("2026-10-22 10:00:00 prompt\nValueError: boom\n")
        results = {name: detail for name, _, detail in doctor.run()}
        self.assertIn("ValueError: boom", results["hook errors"])

    def test_unwritable_state_directory_fails_and_sets_exit_code(self):
        with mock.patch.object(Path, "write_text", side_effect=OSError(13, "Permission denied")):
            self.assertEqual(statuses()["state directory"], doctor.FAIL)

    def test_command_exit_code_follows_failures(self):
        with redirect_stdout(StringIO()):
            with mock.patch.object(doctor, "CHECKS", [("x", lambda: (doctor.FAIL, "broken"))]):
                self.assertEqual(main(["doctor"]), 1)
            with mock.patch.object(doctor, "CHECKS", [("x", lambda: (doctor.WARN, "hmm"))]):
                self.assertEqual(main(["doctor"]), 0)

    def test_old_python_gets_one_clear_line(self):
        root = str(paths.PACKAGE_ROOT)
        code = f"import sys; sys.version_info = (3, 9, 1); sys.path.insert(0, {root!r}); import token_beggar"
        done = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
        self.assertEqual(done.returncode, 1)
        self.assertIn("needs Python 3.10 or newer", done.stderr)
        self.assertNotIn("Traceback", done.stderr)

    def test_empty_error_log_is_fine(self):
        (paths.home() / "errors.log").write_text("\n")
        self.assertEqual(statuses()["hook errors"], doctor.OK)

    def test_a_crashing_check_becomes_a_failure_not_a_traceback(self):
        def boom():
            raise PermissionError("nope")

        with mock.patch.object(doctor, "CHECKS", [("x", boom), ("y", lambda: (doctor.OK, "fine"))]):
            results = doctor.run()
        self.assertEqual([status for _, status, _ in results], [doctor.FAIL, doctor.OK])

    def test_hook_check_fails_when_the_plugin_root_is_wrong(self):
        broken = self.tmp / "plugin"
        (broken / "hooks").mkdir(parents=True)
        (broken / "hooks" / "hooks.json").write_text(
            '{"hooks": {"UserPromptSubmit": [{"hooks": [{"command": "PYTHONPATH=\\"${CLAUDE_PLUGIN_ROOT}\\" python3 -m token_beggar hook prompt"}]}]}}'
        )
        with mock.patch.object(paths, "PACKAGE_ROOT", broken):
            status, detail = doctor._hook()
        self.assertEqual(status, doctor.FAIL, detail)
