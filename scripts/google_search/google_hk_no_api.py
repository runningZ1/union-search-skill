#!/usr/bin/env python3
"""
Google 香港搜索引擎 - 无需 API Key 版本
通过网页抓取获取搜索结果，无需 API Key
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from base_engine import BaseNoApiKeySearchEngine
from typing import Dict, Any, List
from lxml import html
from urllib.parse import quote


class GoogleHkSearchNoAPI(BaseNoApiKeySearchEngine):
    """Google 香港搜索引擎 (无需 API Key)"""

    ENGINE_NAME = "google_hk"
    ENGINE_DISPLAY_NAME = "Google 香港"
    SEARCH_URL = "https://www.google.com.hk/search?q={keyword}"
    REQUIRES_PROXY = True

    def __init__(self, proxy: str = None):
        super().__init__(proxy)
        self.session.headers.update({
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'zh-HK,zh;q=0.9,zh-CN;q=0.8,en;q=0.7',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
        })

    def build_search_url(self, query: str, **kwargs) -> str:
        """构建搜索 URL"""
        encoded_query = quote(query)
        return self.SEARCH_URL.replace('{keyword}', encoded_query)

    def parse_results(self, tree: html.HtmlElement) -> List[Dict[str, Any]]:
        """解析 HTML 搜索结果"""
        results = []

        items = tree.xpath("//div[contains(@class, 'g')] | //div[contains(@class, 'tF2Cxc')]")

        for item in items:
            try:
                title_elems = item.xpath(".//h3//text()")
                href_elems = item.xpath(".//a/@href")
                body_elems = item.xpath(".//div[contains(@class, 'IsZvec')]//text() | .//div[contains(@class, 'VwiK3b')]//text()")

                if title_elems and href_elems:
                    title = ''.join(title_elems).strip()
                    href = ''.join(href_elems).strip()

                    if not href or not href.startswith('http'):
                        continue

                    body = ''.join(body_elems).strip() if body_elems else ''

                    if title and href:
                        results.append({
                            'title': title,
                            'href': href,
                            'body': body,
                            'engine': self.ENGINE_NAME
                        })
            except Exception:
                continue

        return results


def search_google_hk(query: str, max_results: int = 10, proxy: str = None, **kwargs):
    """搜索函数 (供 union_search.py 调用)"""
    engine = GoogleHkSearchNoAPI(proxy=proxy)
    return engine.search(query, max_results=max_results, **kwargs)


# CLI 入口
if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Google 香港搜索 (无需 API Key)")
    parser.add_argument("query", help="搜索关键词")
    parser.add_argument("-m", "--max-results", type=int, default=10)
    parser.add_argument("--proxy", help="代理地址")
    parser.add_argument("--json", action="store_true", help="JSON 输出")

    args = parser.parse_args()

    results = search_google_hk(args.query, args.max_results, args.proxy)

    if args.json:
        print(json.dumps({'results': results}, ensure_ascii=False, indent=2))
    else:
        engine = GoogleHkSearchNoAPI()
        print(engine.format_results(results, args.query))