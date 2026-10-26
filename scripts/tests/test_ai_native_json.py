import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts" / "channels"))

from ai_tools.native_search.backends.cli_json import parse_object, which
from ai_tools.native_search.errors import BackendError


class JsonTests(unittest.TestCase):
    def test_grok_concatenated_draft_and_final(self):
        draft = {"results": [{"title": "draft", "url": "", "snippet": "searching"}]}
        final = {"results": [{"title": "SQLite", "url": "https://sqlite.org/wal.html", "snippet": "WAL"}]}
        raw = json.dumps({"structuredOutput": None, "text": json.dumps(draft) + '\n' + json.dumps(final)})
        self.assertEqual(parse_object(raw, "grok", "search"), final)

    def test_envelopes_fences_and_braces_in_strings(self):
        page = {"title": "Example", "url": "https://example.com", "markdown": 'Literal {braces} and "quotes"'}
        for raw in (json.dumps({"structured_output": page}),
                    json.dumps({"result": '```json\n' + json.dumps(page) + '\n```'})):
            self.assertEqual(parse_object(raw, "claude", "fetch"), page)

    def test_invalid_or_error_outputs_are_backend_errors(self):
        for raw in ('ask me what to search', '{broken', '{"results": "bad"}',
                    '{"is_error":true,"structured_output":{"results":[]}}'):
            with self.assertRaises(BackendError):
                parse_object(raw, "claude", "search")

    @unittest.skipUnless(os.name == "nt", "Windows npm shim regression")
    def test_npm_shim_resolves_to_native_binary(self):
        binary = which("claude")
        self.assertTrue(binary.lower().endswith(".exe"))
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            child = root / "node_modules/@anthropic-ai/claude-code/bin/claude.exe"
            child.parent.mkdir(parents=True)
            child.touch()
            with patch("shutil.which", return_value=str(root / "claude.CMD")):
                self.assertEqual(which("claude"), str(child))

    @unittest.skipUnless(os.name == "nt", "Windows CMD argument regression")
    def test_native_launch_preserves_arguments_that_cmd_truncates(self):
        import sys
        from ai_tools.native_search.backends.cli_json import run
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            script = root / "argv.py"
            script.write_text("import sys,json; print(json.dumps(sys.argv[1:]))", encoding="utf-8")
            shim = root / "argv.cmd"
            shim.write_text(f'@echo off\n"{sys.executable}" "%~dp0argv.py" %*\n')
            arguments = ["-p", 'first line\nquery: SQLite & 中文', "--json-schema", '{"required":["results"]}']
            broken = subprocess.run([str(shim), *arguments], capture_output=True, text=True)
            with patch("ai_tools.native_search.backends.cli_json.which", return_value=sys.executable):
                actual = run("python", [str(script), *arguments], 10, "test")
            self.assertEqual(json.loads(actual), arguments)
            self.assertNotEqual(broken.stdout.strip(), actual.strip())


if __name__ == "__main__":
    unittest.main()
