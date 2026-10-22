"""Unlimited output means all acquired rows, not unbounded upstream pagination."""

import ast
import importlib
import importlib.util
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts/channels"))
sys.path.insert(0, str(ROOT / "scripts/cli"))
from validators import resolve_limit
from output import render_output
from errors import CliUsageError
from ai_tools import adapter
from ai_tools.native_search.backends.cli_json import search_prompt, hits_from
from ai_tools.native_search.backends.codex import _hits
engine = importlib.import_module("union_search.union_search")


def rows(count=37):
    return [{"title": "Result %s" % i, "url": "https://example.com/%s" % i, "snippet": "source"} for i in range(count)]


class UnlimitedResultsTests(unittest.TestCase):
    def test_limit_normalization(self):
        self.assertIsNone(resolve_limit(None, None))
        self.assertIsNone(resolve_limit(0, "small"))
        self.assertEqual(resolve_limit(100, "small"), 100)
        self.assertEqual(resolve_limit(None, "small"), 3)
        with self.assertRaises(CliUsageError):
            resolve_limit(-1, None)

    def test_ai_defaults_and_zero_preserve_all_rows(self):
        for limit in [None, 0, 100]:
            with patch.object(adapter, "_run", return_value={"results": rows()}) as run:
                result = adapter.search("codex", "test", limit=limit)
            self.assertEqual(len(result), 37)
            self.assertEqual(run.call_args.args[0]["limit"], None if limit in (None, 0) else limit)
        with patch.object(adapter, "_run", return_value={"results": rows()}):
            self.assertEqual(len(adapter.search("codex", "test", limit=2)), 2)

    def test_native_normalizers_do_not_default_to_five_or_twenty(self):
        self.assertEqual(len(hits_from({"results": rows()}, None)), 37)
        self.assertEqual(len(_hits({"results": rows()}, None)), 37)
        self.assertNotIn("最多", search_prompt("test", None, None, None))
        self.assertIn("最多 2 条", search_prompt("test", None, 2, None))

    def test_all_output_formats_preserve_last_rows(self):
        envelope = {"ok": True, "command": "search", "data": {"results": {"channel-%s" % i: {"items": rows()} for i in range(12)}, "platforms": ["platform-%s" % i for i in range(53)]}}
        for fmt in ["json", "markdown", "text"]:
            rendered = render_output(envelope, fmt)
            self.assertIn("channel-11", rendered)
            self.assertIn("Result 36", rendered)
            self.assertIn("platform-52", rendered)

    def test_general_scraper_no_default_ten_row_slice(self):
        from so360.so360_no_api import So360SearchNoAPI
        client = So360SearchNoAPI()
        response = Mock(content=b"<html></html>")
        with patch.object(client.session, "get", return_value=response), patch.object(client, "parse_results", return_value=rows()):
            self.assertEqual(len(client.search("test")), 37)
            self.assertEqual(len(client.search("test", max_results=2)), 2)

    def test_api_response_rows_are_not_cut_to_request_batch_size(self):
        from kimi.kimi_search import KimiSearchClient
        from ollama_search.ollama_search import OllamaSearchClient
        from firecrawl.firecrawl_search import FirecrawlSearchClient
        for factory, field in [(KimiSearchClient, "search_results"), (OllamaSearchClient, "results")]:
            client = factory(api_key="local-test-canary")
            response = Mock(status_code=200)
            response.json.return_value = {field: rows()}
            with patch.object(client.session, "post", return_value=response):
                self.assertEqual(len(client.search("test")), 37)
                self.assertEqual(len(client.search("test", max_results=2)), 2)
        # Firecrawl can combine web/news/image sources; no default aggregate cap.
        client = FirecrawlSearchClient(api_key="local-test-canary")
        self.assertEqual(len(client._normalize(rows(), None)), 37)
        self.assertEqual(len(client._normalize(rows(), 2)), 2)

    def test_registered_result_slice_parsers_have_no_default_cap(self):
        checked = 0
        for platform, meta in engine.PLATFORM_MODULES.items():
            path = engine.CHANNELS_DIR / Path(*meta["module"].split(".")).with_suffix(".py")
            if not path.is_file():
                continue
            checked += 1
            tree = ast.parse(path.read_text(encoding="utf-8-sig"))
            for node in ast.walk(tree):
                if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute) or node.func.attr != "add_argument":
                    continue
                flags = [v.value for v in node.args if isinstance(v, ast.Constant)]
                if "--max-results" in flags or "--limit" in flags:
                    for keyword in node.keywords:
                        if keyword.arg == "default":
                            self.assertIsNone(ast.literal_eval(keyword.value), (platform, flags))
        self.assertGreater(checked, 0)

    def test_cli_defaults_and_explicit_zero_apply_to_all_commands(self):
        spec = importlib.util.spec_from_file_location("unlimited_cli", ROOT / "scripts/cli/main.py")
        cli = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cli)
        for argv in [["search", "test"], ["platform", "codex", "test"], ["codex", "test"], ["download", "https://example.com/video"]]:
            with patch.object(sys, "argv", ["union_search_cli.py", *argv]):
                self.assertIsNone(cli.parse_args().limit)
        with patch.object(sys, "argv", ["union_search_cli.py", "image", "test"]):
            self.assertEqual(cli.parse_args().limit, 0)


if __name__ == "__main__":
    unittest.main()
