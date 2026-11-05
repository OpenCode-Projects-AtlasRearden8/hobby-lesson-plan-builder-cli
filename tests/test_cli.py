import io
import os
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

from lesson_builder import cli


class CliTests(unittest.TestCase):
    def _write_topics(self, text):
        fd, path = tempfile.mkstemp(suffix=".txt")
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(text)
        self.addCleanup(os.unlink, path)
        return path

    def run_cli(self, argv):
        buf = io.StringIO()
        with mock.patch("sys.stdout", buf):
            code = cli.main(argv)
        return code, buf.getvalue()

    def test_text_output_to_stdout(self):
        path = self._write_topics("- what is a prompt\n- writing first prompts")
        code, out = self.run_cli([path, "--format", "text"])
        self.assertEqual(code, 0)
        self.assertIn("Session 1", out)
        self.assertIn("[ ]", out)

    def test_markdown_output_to_file(self):
        path = self._write_topics("- what is a prompt\n- writing first prompts")
        out_path = tempfile.mktemp(suffix=".md")
        self.addCleanup(lambda: os.path.exists(out_path) and os.unlink(out_path))
        code, out = self.run_cli([path, "--format", "markdown", "--output", out_path])
        self.assertEqual(code, 0)
        with open(out_path, encoding="utf-8") as fh:
            content = fh.read()
        self.assertTrue(content.startswith("# Your Learning Plan"))
        self.assertIn("- [ ] what is a prompt", content)

    def test_missing_file_exit_code_2(self):
        code, _ = self.run_cli(["/nonexistent/topics.txt"])
        self.assertEqual(code, 2)

    def test_no_topics_exit_code_2(self):
        path = self._write_topics("# only a heading\n\n")
        code, _ = self.run_cli([path])
        self.assertEqual(code, 2)

    def test_empty_extra_supplies_ok(self):
        path = self._write_topics("- what is a prompt")
        code, _ = self.run_cli([path, "--supplies", ""])
        self.assertEqual(code, 0)

    def test_draft_disabled_by_default(self):
        path = self._write_topics("- what is a prompt\n- writing first prompts")
        with mock.patch("lesson_builder.cli.draft_session_notes") as draft:
            code, _ = self.run_cli([path])
        self.assertEqual(code, 0)
        draft.assert_not_called()

    def test_draft_opt_in_calls_model(self):
        path = self._write_topics("- what is a prompt\n- writing first prompts")
        with mock.patch(
            "lesson_builder.cli.draft_session_notes",
            return_value="First things first:\n  - Open the chat.",
        ) as draft:
            code, out = self.run_cli([path, "--draft", "--api-base", "http://localhost:9999/v1"])
        self.assertEqual(code, 0)
        self.assertTrue(draft.called)

    def test_module_invocation_works(self):
        path = self._write_topics("- what is a prompt")
        result = subprocess.run(
            [sys.executable, "-m", "lesson_builder", path, "--format", "markdown"],
            capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("- [ ] what is a prompt", result.stdout)


if __name__ == "__main__":
    unittest.main()
