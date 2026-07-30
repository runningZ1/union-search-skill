import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class DocumentationContractTests(unittest.TestCase):
    def test_readme_recommends_the_current_repository(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")

        self.assertIn(
            "https://github.com/runningZ1/union-search-skill",
            readme,
        )
        self.assertNotIn(
            "https://github.com/anyangrc/union-search-skill",
            readme,
        )

    def test_skill_local_links_resolve(self):
        skill_path = ROOT / "SKILL.md"
        skill = skill_path.read_text(encoding="utf-8")
        local_targets = [
            target.split("#", 1)[0]
            for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", skill)
            if "://" not in target
        ]

        missing = [
            target
            for target in local_targets
            if not (skill_path.parent / target).exists()
        ]

        self.assertEqual([], missing)

    def test_removed_platform_is_not_advertised(self):
        documented_contract = "\n".join(
            (ROOT / path).read_text(encoding="utf-8")
            for path in ("SKILL.md", ".env.example", "ENV_TEMPLATE.txt")
        )

        self.assertNotIn("Anna's Archive", documented_contract)
        self.assertNotIn("ANNASARCHIVE_PROXY", documented_contract)


if __name__ == "__main__":
    unittest.main()
