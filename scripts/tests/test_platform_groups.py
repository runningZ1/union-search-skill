import importlib
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "cli"))

engine = importlib.import_module("union_search.union_search")
from registry import load_capabilities, load_groups


class PlatformGroupsTest(unittest.TestCase):
    def test_registry_counts_and_credential_partition(self):
        capabilities = load_capabilities()
        caps = {cap.name: cap for cap in capabilities}
        no_api_key = set(engine.PLATFORM_GROUPS["no_api_key"])
        api = set(engine.PLATFORM_GROUPS["api"])
        tools = set(engine.PLATFORM_GROUPS["tools"])
        ai_tools = set(engine.PLATFORM_GROUPS["ai_tools"])
        self.assertEqual(len(capabilities), 52)
        self.assertEqual(len(caps), 52)
        self.assertEqual(len(no_api_key), 25)
        self.assertEqual(len(api), 23)
        self.assertEqual(len(ai_tools), 3)
        self.assertEqual(tools, {"defuddle"})
        partitions = [no_api_key, api, ai_tools, tools]
        for index, partition in enumerate(partitions):
            for other in partitions[index + 1:]:
                self.assertFalse(partition & other)
        self.assertEqual(no_api_key | api | ai_tools | tools, set(caps))
        self.assertEqual(no_api_key | api | ai_tools, set(engine.PLATFORM_GROUPS["all"]))
        self.assertEqual(len(engine.PLATFORM_GROUPS["all"]), 51)
        for name in no_api_key:
            self.assertFalse(caps[name].requires_api_key, name)
            self.assertFalse(caps[name].required_env, name)
            self.assertEqual(caps[name].auth_mode, "anonymous")
        for name in api:
            self.assertTrue(caps[name].requires_api_key, name)
            self.assertTrue(caps[name].required_env, name)
            self.assertEqual(caps[name].auth_mode, "api_key")
        for name in ai_tools:
            self.assertEqual(caps[name].auth_mode, "local_account")
        for name, cap in caps.items():
            self.assertEqual(cap.kind, "tool" if name in tools else "search")

    def test_default_web_groups_have_exact_members_and_order(self):
        expected = [
            "baidu_direct", "so360_direct", "sogou_direct", "duckduckgo",
            "brave", "yahoo", "yandex_direct", "quark_direct",
        ]
        for group in ["general", "search", "preferred"]:
            with self.subTest(group=group):
                self.assertEqual(engine.PLATFORM_GROUPS[group], expected)
        self.assertTrue(set(expected) < set(engine.PLATFORM_GROUPS["no_api_key"]))
        self.assertIn("github", engine.PLATFORM_GROUPS["no_api_key"])

    def test_registry_group_metadata_matches_real_groups(self):
        groups = load_groups()
        self.assertEqual(groups, engine.PLATFORM_GROUPS)
        caps = {cap.name: cap for cap in load_capabilities()}
        for group, names in groups.items():
            self.assertEqual(len(names), len(set(names)), group)
            self.assertTrue(set(names) <= set(caps), group)
        for name, cap in caps.items():
            expected = tuple(sorted(group for group, names in groups.items() if group != "all" and name in names))
            self.assertEqual(cap.groups, expected, name)

    def test_known_credential_requirements_and_optional_keys(self):
        caps = {cap.name: cap for cap in load_capabilities()}
        for name, key in [
            ("exa", "EXA_API_KEY"), ("serper", "SERPER_API_KEY"),
            ("xiaoyuzhoufm", "METASO_API_KEY"), ("anysearch", "ANYSEARCH_API_KEY"),
        ]:
            self.assertEqual(caps[name].required_env, (key,))
            self.assertIn(name, engine.PLATFORM_GROUPS["api"])
        self.assertIn("github", engine.PLATFORM_GROUPS["no_api_key"])
        self.assertTrue(caps["github"].optional_env)
        self.assertIn("zhihu_official", engine.PLATFORM_GROUPS["api"])

    def test_web_compatibility_entries_share_service_implementation(self):
        caps = {cap.name: cap for cap in load_capabilities()}
        for alias, canonical in [
            ("duckduckgo_html", "duckduckgo"),
            ("brave_direct", "brave"),
            ("yahoo_direct", "yahoo"),
        ]:
            with self.subTest(alias=alias):
                self.assertIn(alias, caps)
                self.assertIn(alias, engine.PLATFORM_GROUPS["no_api_key"])
                self.assertNotIn(alias, engine.PLATFORM_GROUPS["general"])
                self.assertEqual(engine.WEB_SOURCE_ALIASES[alias], canonical)
                self.assertEqual(engine.NATIVE_WEB_SCRIPTS[alias], engine.NATIVE_WEB_SCRIPTS[canonical])


if __name__ == "__main__":
    unittest.main()
