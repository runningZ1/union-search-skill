#!/usr/bin/env python3
"""
Mojeek 搜索引擎 - 无需 API Key 版本
通过网页抓取获取搜索结果，无需 API Key

Mojeek 是一个独立的搜索引擎，拥有自己的网络爬虫和索引，
不提供 Google/Bing 的结果，适合获取差异化的搜索结果。
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from typing import Dict, Any, List
from lxml import html
from urllib.parse import quote
import requests


class MojeekSearchNoAPI:
    """Mojeek 搜索引擎 (无需 API Key)"""

    ENGINE_NAME = "mojeek"
    ENGINE_DISPLAY_NAME = "Mojeek 搜索"
    SEARCH_URL = "https://www.mojeek.com/search?q={keyword}"
    REQUIRES_PROXY = False

    def __init__(self, proxy=None):
        self.proxy = proxy
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
        })
        if self.proxy:
            self.session.proxies = {'http': self.proxy, 'https': self.proxy}

    def build_search_url(self, query: str, **kwargs) -> str:
        """构建搜索 URL"""
        encoded_query = quote(query)
        return self.SEARCH_URL.replace('{keyword}', encoded_query)

    def parse_results(self, tree: html.HtmlElement) -> List[Dict[str, Any]]:
        """解析 HTML 搜索结果"""
        results = []

        # Mojeek 搜索结果容器 - 使用标准的结果列表结构
        items = tree.xpath("//ul[contains(@class, 'results-standard')]//li")

        for item in items:
            try:
                # 标题和链接从 h2 > a.title 获取
                title_elems = item.xpath(".//h2//a[@class='title']//text() | .//h2//a[contains(@class, 'title')]//text()")
                href_elems = item.xpath(".//h2//a[@class='title']/@href | .//h2//a[contains(@class, 'title')]/@href")

                # 摘要从 p.s 获取 (Mojeek 的描述类名)
                body_elems = item.xpath(".//p[contains(@class, 's')]//text() | .//p[@class='s']//text()")

                if title_elems and href_elems:
                    title = ''.join(title_elems).strip()
                    href = ''.join(href_elems).strip()
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

    def search(self, query: str, max_results: int = 10, timeout: int = 15, **kwargs) -> List[Dict[str, Any]]:
        """
        执行搜索

        Args:
            query: 搜索关键词
            max_results: 最大结果数
            timeout: 请求超时时间 (秒)

        Returns:
            搜索结果列表
        """
        search_url = self.build_search_url(query)

        try:
            response = self.session.get(search_url, timeout=timeout)
            response.raise_for_status()

            tree = html.fromstring(response.content)
            results = self.parse_results(tree)

            return results[:max_results]

        except requests.exceptions.Timeout:
            raise Exception(f"{self.ENGINE_DISPLAY_NAME} 搜索超时")
        except requests.exceptions.RequestException as e:
            raise Exception(f"{self.ENGINE_DISPLAY_NAME} 搜索失败：{str(e)}")

    def format_results(self, results: List[Dict[str, Any]], query: str) -> str:
        """格式化搜索结果用于终端输出"""
        output = []
        output.append(f"🔍 {self.ENGINE_DISPLAY_NAME}: {query}")
        output.append(f"📊 找到 {len(results)} 条结果")
        output.append("")

        for i, item in enumerate(results, 1):
            title = item.get('title', '')
            href = item.get('href', '')
            body = item.get('body', '')

            output.append(f"[{i}] {title}")
            output.append(f"    🔗 {href}")
            if body:
                output.append(f"    📝 {body}")
            output.append("")

        return "\n".join(output)


def search_mojeek(query: str, max_results: int = 10, proxy: str = None, **kwargs):
    """搜索函数 (供 union_search.py 调用)"""
    engine = MojeekSearchNoAPI(proxy=proxy)
    return engine.search(query, max_results=max_results, **kwargs)


# CLI 入口
if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Mojeek 搜索 (无需 API Key)")
    parser.add_argument("query", help="搜索关键词")
    parser.add_argument("-m", "--max-results", type=int, default=10)
    parser.add_argument("--proxy", help="代理地址")
    parser.add_argument("--json", action="store_true", help="JSON 输出")

    args = parser.parse_args()

    results = search_mojeek(args.query, args.max_results, args.proxy)

    if args.json:
        print(json.dumps({'results': results}, ensure_ascii=False, indent=2))
    else:
        engine = MojeekSearchNoAPI()
        print(engine.format_results(results, args.query))
