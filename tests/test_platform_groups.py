"""Credential boundaries and routing checks; no external services are called."""

import contextlib
import importlib.util
import io
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import importlib

engine = importlib.import_module("union_search.union_search")
spec = importlib.util.spec_from_file_location("group_test_cli", ROOT / "scripts/cli/main.py")
cli = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cli)
from registry import load_capabilities
from adapters import run_search


class PlatformGroupsTest(unittest.TestCase):
    def test_credential_partition_covers_only_search_channels(self):
        caps = {cap.name: cap for cap in load_capabilities()}
        general = set(engine.PLATFORM_GROUPS["general"])
        api = set(engine.PLATFORM_GROUPS["api"])
        tools = set(engine.PLATFORM_GROUPS["tools"])
        self.assertFalse(general & api)
        self.assertEqual(general | api | tools, set(caps))
        self.assertEqual(general | api, set(engine.PLATFORM_GROUPS["all"]))
        for name in general:
            self.assertFalse(caps[name].requires_api_key, name)
            self.assertFalse(caps[name].required_env, name)
        for name in api:
            self.assertTrue(caps[name].requires_api_key, name)
            self.assertTrue(caps[name].required_env, name)
        for name in tools:
            self.assertEqual(caps[name].kind, "tool")
            self.assertNotIn(name, general | api)
        for group in engine.PLATFORM_GROUPS.values():
            self.assertEqual(len(group), len(set(group)))
            self.assertTrue(set(group) <= set(caps))

    def test_known_credential_requirements_and_optional_keys(self):
        caps = {cap.name: cap for cap in load_capabilities()}
        for name, key in [("exa", "EXA_API_KEY"), ("serper", "SERPER_API_KEY"), ("xiaoyuzhoufm", "METASO_API_KEY")]:
            self.assertEqual(caps[name].required_env, (key,))
            self.assertIn(name, engine.PLATFORM_GROUPS["api"])
        for name in ["github", "anysearch"]:
            self.assertIn(name, engine.PLATFORM_GROUPS["general"])
            self.assertTrue(caps[name].optional_env)

    def test_default_aliases_and_explicit_api_routing(self):
        for group, platforms, expected in [
            (None, None, "general"),
            ("no_api_key", None, "general"),
            ("search", None, "general"),
            ("api", None, "api"),
            ("all", None, "all"),
            ("general", ["tavily"], None),
        ]:
            with self.subTest(group=group, platforms=platforms):
                with patch.object(engine, "load_env_file"), patch.object(engine, "union_search", return_value={"results": {}, "summary": {}}) as search:
                    run_search("test", platforms, group, 1, 1, 1, False, "unused.env")
                self.assertEqual(search.call_args.kwargs["platforms"], engine.PLATFORM_GROUPS[expected] if expected else ["tavily"])
        with patch.object(cli, "load_capabilities", return_value=load_capabilities()):
            self.assertEqual(cli.handle_schema(None)["data"]["limits"]["default_search_platforms"], "general")

    def test_doctor_reports_missing_keys_for_corrected_channels(self):
        with patch.dict(os.environ, {}, clear=True), patch.object(engine, "load_env_file"), patch.object(sys, "argv", ["union_search_cli.py", "doctor", "--platforms", "exa", "serper", "xiaoyuzhoufm"]):
            result = cli.handle_doctor(cli.parse_args())
        checks = result["data"]["platforms"]
        self.assertEqual(len(checks), 3)
        for check in checks:
            self.assertEqual(check["status"], "warn")
            self.assertIn("missing required env:", check["message"])

    def test_removed_provider_channels_are_rejected_without_network(self):
        for name in ["xiaohongshu", "douyin", "bilibili", "twitter", "weibo", "zhihu", "tiktok"]:
            with self.subTest(name=name):
                self.assertNotIn(name, engine.PLATFORM_MODULES)
                with patch.object(cli, "run_search") as search, patch.object(sys, "argv", ["union_search_cli.py", "search", "test", "--platforms", name]):
                    args = cli.parse_args()
                    with self.assertRaises(cli.CliUsageError):
                        cli.handle_search(args)
                    search.assert_not_called()
        self.assertIn("zhihu_official", engine.PLATFORM_GROUPS["api"])

    def test_legacy_entrypoint_also_defaults_to_general(self):
        result = {"summary": {"successful": 0, "total_platforms": 25, "failed": 0, "total_items": 0}, "results": {}, "final_items": []}
        with patch.object(sys, "argv", ["union_search", "test", "--json"]), patch.object(engine, "load_env_file"), patch.object(engine, "union_search", return_value=result) as search, patch.object(engine, "SearchLogger"), contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            engine.main()
        self.assertEqual(search.call_args.kwargs["platforms"], engine.PLATFORM_GROUPS["general"])


if __name__ == "__main__":
    unittest.main()
