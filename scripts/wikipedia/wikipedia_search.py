#!/usr/bin/env python3
"""
Wikipedia 搜索模块

使用 Wikipedia API 进行搜索
"""

import os
import sys
import json
import argparse
import requests
import re
from typing import Optional, Dict, Any, List
from html import unescape
from dotenv import load_dotenv

# 加载环境变量
script_dir = os.path.dirname(os.path.abspath(__file__))
skill_root = os.path.dirname(os.path.dirname(script_dir))
load_dotenv(os.path.join(skill_root, '.env'))


class WikipediaSearch:
    """Wikipedia 搜索客户端"""

    def __init__(self, lang: str = "en", proxy: Optional[str] = None):
        """
        初始化客户端

        Args:
            lang: 语言代码 (默认: en)
            proxy: 代理地址 (如 http://127.0.0.1:7890)
        """
        self.lang = lang
        self.proxy = proxy or os.getenv("WIKIPEDIA_PROXY")
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        if self.proxy:
            self.session.proxies = {'http': self.proxy, 'https': self.proxy}

    def search(
        self,
        query: str,
        max_results: int = 10
    ) -> List[Dict[str, Any]]:
        """
        执行搜索

        Args:
            query: 搜索关键词
            max_results: 最大结果数

        Returns:
            搜索结果列表
        """
        search_url = f"https://{self.lang}.wikipedia.org/w/api.php"

        params = {
            "action": "query",
            "format": "json",
            "list": "search",
            "srsearch": query,
            "srlimit": max_results,
            "utf8": "1",
            "srprop": "snippet"
        }

        try:
            response = self.session.get(search_url, params=params, timeout=15)
            response.raise_for_status()

            json_data = response.json()
            results = []
            search_items = json_data.get("query", {}).get("search", [])
            for item in search_items:
                title = item.get("title", "")
                pageid = item.get("pageid")
                snippet = item.get("snippet", "")
                body = unescape(re.sub(r"<[^>]+>", "", snippet)).strip()
                results.append({
                    'title': title,
                    'href': f"https://{self.lang}.wikipedia.org/?curid={pageid}" if pageid else "",
                    'body': body
                })

            return results

        except Exception as e:
            raise Exception(f"Wikipedia 搜索失败: {str(e)}")

    def format_results(self, results: List[Dict[str, Any]], query: str) -> str:
        """格式化搜索结果"""
        output = []
        output.append(f"📖 Wikipedia 搜索: {query}")
        output.append(f"📊 找到 {len(results)} 条结果")
        output.append("")

        for i, item in enumerate(results, 1):
            output.append(f"[{i}] {item.get('title', '')}")
            output.append(f"    🔗 {item.get('href', '')}")
            if item.get('body'):
                output.append(f"    📝 {item.get('body', '')}")
            output.append("")

        return "\n".join(output)


def main():
    parser = argparse.ArgumentParser(description="Wikipedia 搜索")
    parser.add_argument("query", help="搜索关键词")
    parser.add_argument("-l", "--lang", default="en", help="语言代码 (默认: en, 中文: zh)")
    parser.add_argument("-m", "--max-results", type=int, default=10, help="最大结果数 (默认: 10)")
    parser.add_argument("--proxy", help="代理地址")
    parser.add_argument("--json", action="store_true", help="JSON 格式输出")
    parser.add_argument("--pretty", action="store_true", help="格式化 JSON")

    args = parser.parse_args()

    try:
        client = WikipediaSearch(lang=args.lang, proxy=args.proxy)
        results = client.search(
            query=args.query,
            max_results=args.max_results
        )

        if args.json:
            output_data = {
                'query': args.query,
                'lang': args.lang,
                'total_results': len(results),
                'results': results
            }
            if args.pretty:
                print(json.dumps(output_data, indent=2, ensure_ascii=False))
            else:
                print(json.dumps(output_data, ensure_ascii=False))
        else:
            print(client.format_results(results, args.query))

    except Exception as e:
        print(f"错误: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
