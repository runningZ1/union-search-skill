import base64
import importlib
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
cleaning = importlib.import_module("union_search.structured_results")


def item(platform, title, url, content=""):
    return cleaning.normalize_item(
        {"title": title, "url": url, "content": content}, platform, 1,
    )


class ResultCleaningTest(unittest.TestCase):
    def test_redirects_and_www_collapse_to_the_same_page(self):
        target = "https://www.merriam-webster.com/dictionary/sustainable"
        token = "a1" + base64.b64encode(target.encode()).decode()
        bing = "https://www.bing.com/ck/a?!&&p=abc&u=%s&ntb=1" % token
        yahoo = "https://r.search.yahoo.com/_ylt=abc/RV=2/RE=3/RU=%s/RK=4/RS=def" % target
        rows = [
            item("bing", "SUSTAINABLE Definition", bing, "short"),
            item("yahoo", "SUSTAINABLE Definition", target, "a longer snippet"),
            item("duckduckgo", "SUSTAINABLE Definition & Meaning", yahoo),
        ]
        merged, removed = cleaning.merge_items(rows)
        self.assertEqual(removed, 2)
        self.assertEqual(len(merged), 1)
        # 合并后保留首个渠道还原出的真实页面地址
        self.assertEqual(merged[0]["url"], "https://www.merriam-webster.com/dictionary/sustainable")
        self.assertEqual(merged[0]["title"], "SUSTAINABLE Definition")
        self.assertEqual(merged[0]["content"], "a longer snippet")
        self.assertEqual([source["platform"] for source in merged[0]["sources"]], ["bing", "yahoo", "duckduckgo"])

    def test_github_uses_web_url_not_api_url(self):
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

    def test_body_and_href_are_normalized(self):
        row = cleaning.normalize_item({
            "title": "Python Release Python 3.13.0",
            "href": "https://www.python.org/downloads/release/python-3130/",
            "body": "Release date: Oct. 7, 2024.",
        }, "serper", 2)
        self.assertEqual(row["url"], "https://www.python.org/downloads/release/python-3130/")
        self.assertEqual(row["content"], "Release date: Oct. 7, 2024.")
        self.assertEqual(row["sources"][0]["rank"], 2)

    def test_www_and_trailing_slash_merge_but_keep_the_accessible_url(self):
        # 只有 www 主机提供 HTTPS 的网站，去掉 www 后无法访问；规范地址只用于去重
        rows = [
            item("serper", "第一财经", "https://www.yicai.com/news/102453618.html?utm_source=x#top"),
            item("baidu", "第一财经", "https://yicai.com/news/102453618.html/"),
        ]
        merged, removed = cleaning.merge_items(rows)
        self.assertEqual((len(merged), removed), (1, 1))
        self.assertEqual(merged[0]["url"], "https://www.yicai.com/news/102453618.html?utm_source=x")
        self.assertEqual(cleaning.canonical_url(merged[0]["url"]), "https://yicai.com/news/102453618.html")

    def test_similar_titles_on_different_pages_stay_separate(self):
        rows = [
            item("baidu", "4步拆解2025服装爆款公式", "https://example.com/a", "short"),
            item("brave", "4步拆解2025服装爆款公式→", "https://example.com/b", "longer content"),
            item("sogou", "服装店铺爆款复盘", "https://example.com/c"),
        ]
        merged, removed = cleaning.merge_items(rows)
        self.assertEqual((len(merged), removed), (3, 0))
        self.assertEqual(merged[0]["url"], "https://example.com/a")
        self.assertEqual(merged[0]["title"], "4步拆解2025服装爆款公式")
        self.assertEqual(merged[1]["title"], "4步拆解2025服装爆款公式→")


if __name__ == "__main__":
    unittest.main()
