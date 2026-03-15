#!/usr/bin/env python3
"""
Wolfram Alpha 知识引擎 - 无需 API Key 版本
通过网页抓取获取搜索结果，无需 API Key
 提供计算知识和事实查询
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from base_engine import BaseNoApiKeySearchEngine
from typing import Dict, Any, List
from lxml import html
from urllib.parse import quote


class WolframSearchNoAPI(BaseNoApiKeySearchEngine):
    """Wolfram Alpha 知识引擎 (无需 API Key)"""

    ENGINE_NAME = "wolfram"
    ENGINE_DISPLAY_NAME = "Wolfram Alpha"
    SEARCH_URL = "https://www.wolframalpha.com/input?i={keyword}"
    REQUIRES_PROXY = True

    def __init__(self, proxy: str = None):
        super().__init__(proxy)
        self.session.headers.update({
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
        })

    def build_search_url(self, query: str, **kwargs) -> str:
        """构建搜索 URL"""
        encoded_query = quote(query)
        return self.SEARCH_URL.replace('{keyword}', encoded_query)

    def parse_results(self, tree: html.HtmlElement) -> List[Dict[str, Any]]:
        """解析 HTML 搜索结果"""
        results = []

        items = tree.xpath("//div[contains(@class, 'result')] | //div[contains(@class, 'pod')]")

        for item in items:
            try:
                title_elems = item.xpath(".//h2//text() | .//div[contains(@class, 'pod-title')]//text()")
                body_elems = item.xpath(".//div[contains(@class, 'result-content')]//text() | .//div[contains(@class, 'pod-content')]//text()")

                title = ''.join(title_elems).strip() if title_elems else ''
                body = ''.join(body_elems).strip() if body_elems else ''

                if body:
                    results.append({
                        'title': title if title else 'Wolfram Alpha 结果',
                        'href': '',
                        'body': body,
                        'engine': self.ENGINE_NAME
                    })
            except Exception:
                continue

        return results


def search_wolfram(query: str, max_results: int = 10, proxy: str = None, **kwargs):
    """搜索函数 (供 union_search.py 调用)"""
    engine = WolframSearchNoAPI(proxy=proxy)
    return engine.search(query, max_results=max_results, **kwargs)


# CLI 入口
if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Wolfram Alpha 知识引擎 (无需 API Key)")
    parser.add_argument("query", help="搜索关键词")
    parser.add_argument("-m", "--max-results", type=int, default=10)
    parser.add_argument("--proxy", help="代理地址")
    parser.add_argument("--json", action="store_true", help="JSON 输出")

    args = parser.parse_args()

    results = search_wolfram(args.query, args.max_results, args.proxy)

    if args.json:
        print(json.dumps({'results': results}, ensure_ascii=False, indent=2))
    else:
        engine = WolframSearchNoAPI()
        print(engine.format_results(results, args.query))