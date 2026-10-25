"""Native search boundary, backend isolation and child timeout regression tests."""

import importlib
import json
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts" / "channels"))
from ai_tools import adapter, worker
from ai_tools.native_search.errors import BackendError
from ai_tools.native_search.backends.cli_json import require_tool_call
engine = importlib.import_module("union_search.union_search")


class AiToolsTests(unittest.TestCase):
    def test_native_tool_evidence_is_required(self):
        final = json.dumps({"type": "result", "result": '{"results":[]} '})
        with self.assertRaises(BackendError):
            require_tool_call(final, "claude", {"WebSearch"})
        event = {"type": "assistant", "message": {"content": [{"type": "tool_use", "name": "WebSearch"}]}}
        require_tool_call(json.dumps(event) + "\n" + final, "claude", {"WebSearch"})
        with self.assertRaises(BackendError):
            require_tool_call(json.dumps(event), "grok", {"web_search"})

    def test_each_channel_calls_exact_bundled_backend(self):
        for platform, backend in adapter.BACKENDS.items():
            module = Mock()
            module.search.return_value = {"backend": backend, "results": [{"title": "SQLite", "url": "https://sqlite.org/wal.html", "snippet": "WAL"}]}
            with patch.object(worker.importlib, "import_module", return_value=module) as load:
                result = worker.execute({"operation": "search", "backend": backend, "query": "WAL", "limit": 1})
            load.assert_called_once_with("ai_tools.native_search.backends." + backend)
            self.assertEqual(result["backend"], backend)
            self.assertTrue(result["untrusted"])

    def test_failure_never_switches_backend(self):
        module = Mock()
        module.search.side_effect = BackendError("claude", "unavailable", 503, True)
        with patch.object(worker.importlib, "import_module", return_value=module) as load:
            with self.assertRaises(BackendError):
                worker.execute({"operation": "search", "backend": "claude", "query": "test", "limit": 1})
        self.assertEqual(load.call_count, 1)

    def test_results_are_bounded_and_params_forwarded_as_data(self):
        with patch.object(adapter, "_run", return_value={"results": [{"title": "x"}, {"title": "y"}]}) as run:
            rows = adapter.search("codex", '中文 & "quotes"\nsecond line', 1, 5, domains="sqlite.org,python.org", recency_days="7")
        self.assertEqual(len(rows), 1)
        request = run.call_args.args[0]
        self.assertEqual(request["domains"], ["sqlite.org", "python.org"])
        self.assertEqual(request["recency_days"], 7)
        self.assertEqual(rows[0]["backend"], "codex")

    def test_invalid_inputs_do_not_launch_child(self):
        for params in [{"limit": -1}, {"limit": True}, {"recency_days": -1}, {"domains": 12}, {"command": "echo bad"}]:
            with patch.object(adapter, "_run") as run:
                with self.assertRaises((ValueError, TypeError)):
                    adapter.search("codex", "test", **params)
                run.assert_not_called()

    def test_worker_does_not_emit_credentials_from_exception(self):
        path = Path(worker.__file__)
        result = subprocess.run([sys.executable, str(path)], input=json.dumps({"operation": "search", "backend": "secret-canary"}), capture_output=True, text=True, encoding="utf-8")
        self.assertNotIn("secret-canary", result.stdout + result.stderr)
        self.assertFalse(json.loads(result.stdout)["ok"])

    def test_timeout_terminates_process_tree(self):
        child = Mock(pid=12345, returncode=-1)
        child.communicate.side_effect = [subprocess.TimeoutExpired("worker", 1), ("", "")]
        with patch.object(adapter.subprocess, "Popen", return_value=child), patch.object(adapter.subprocess, "run") as kill, patch.object(adapter.os, "killpg", create=True) as killpg:
            with self.assertRaises(TimeoutError):
                adapter._run({"operation": "check", "backend": "codex"}, 1)
        child.kill.assert_called_once()
        self.assertTrue(kill.called or killpg.called)

    def test_engine_preserves_backend_and_excludes_default_groups(self):
        for platform in adapter.BACKENDS:
            for group in ["general", "api", "no_api_key", "reference", "community"]:
                self.assertNotIn(platform, engine.PLATFORM_GROUPS[group])
            with patch.object(adapter, "search", return_value=[{"title": "native", "url": "https://example.com/native"}]) as run:
                _, result = engine.search_platform(platform, "test", 2, timeout=7)
            self.assertTrue(result["success"])
            run.assert_called_once_with(platform, "test", 2, timeout=7)


if __name__ == "__main__":
    unittest.main()
