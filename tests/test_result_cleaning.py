import base64
import importlib
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
cleaning = importlib.import_module("union_search.structured_results")


def item(platform, title, url, content=""):
    return cleaning.normalize_item(
        {"title": title, "url": url, "content": content}, platform, 1,
    )


class ResultCleaningTest(unittest.TestCase):
    def test_channel_urls_collapse_to_the_same_page(self):
        target = "https://www.merriam-webster.com/dictionary/sustainable"
        token = "a1" + base64.b64encode(target.encode()).decode()
        bing = "https://www.bing.com/ck/a?!&&p=abc&u=%s&ntb=1" % token
        yahoo = "https://r.search.yahoo.com/_ylt=abc/RV=2/RE=3/RU=%s/RK=4/RS=def" % target
        rows = [
            item("bing", "SUSTAINABLE Definition", bing),
            item("yahoo", "SUSTAINABLE Definition", "https://www." + target[8:]),
            item("duckduckgo", "SUSTAINABLE Definition & Meaning", yahoo),
        ]
        merged, removed = cleaning.merge_items(rows)
        self.assertEqual(removed, 2)
        self.assertEqual(merged[0]["url"], "https://merriam-webster.com/dictionary/sustainable")
        self.assertEqual([source["platform"] for source in merged[0]["sources"]], ["bing", "yahoo", "duckduckgo"])

    def test_github_uses_web_url_and_keeps_distinct_titles(self):
        row = cleaning.normalize_item({
            "name": "apparel-data",
            "full_name": "owner/apparel-data",
            "url": "https://api.github.com/repos/owner/apparel-data",
            "html_url": "https://github.com/owner/apparel-data",
            "description": "<b>apparel</b>   data",
        }, "github", 1)
        self.assertEqual(row["title"], "apparel-data")
        self.assertEqual(row["url"], "https://github.com/owner/apparel-data")
        self.assertEqual(row["content"], "apparel data")
        other = item("web", "服装爆款怎么打造", "https://example.com/other")
        merged, removed = cleaning.merge_items([row, other])
        self.assertEqual((len(merged), removed), (2, 0))

    def test_similar_titles_merge_without_chaining(self):
        rows = [
            item("baidu", "4步拆解2025服装爆款公式", "https://example.com/a", "short"),
            item("brave", "4步拆解2025服装爆款公式→", "https://example.com/b", "longer content"),
            item("sogou", "服装店铺爆款复盘", "https://example.com/c"),
        ]
        merged, removed = cleaning.merge_items(rows)
        self.assertEqual(removed, 1)
        self.assertEqual(len(merged), 2)
        self.assertEqual(merged[0]["content"], "longer content")
        self.assertEqual(merged[0]["title"], "4步拆解2025服装爆款公式→")


if __name__ == "__main__":
    unittest.main()
