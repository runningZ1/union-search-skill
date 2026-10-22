#!/usr/bin/env python3
"""
Yahoo 搜索模块

使用 Yahoo Search 进行网络搜索
"""

import os
import sys
import json
import argparse
import requests
from typing import Optional, Dict, Any, List
from secrets import token_urlsafe
from urllib.parse import urlparse, parse_qs, unquote
from lxml import html
from dotenv import load_dotenv

# 加载环境变量
script_dir = os.path.dirname(os.path.abspath(__file__))
skill_root = os.path.dirname(os.path.dirname(os.path.dirname(script_dir)))
load_dotenv(os.path.join(skill_root, '.env'))


class YahooSearch:
    """Yahoo 搜索客户端"""

    def __init__(self, proxy: Optional[str] = None):
        """
        初始化客户端

        Args:
            proxy: 代理地址 (如 http://127.0.0.1:7890)
        """
        self.proxy = proxy or os.getenv("YAHOO_PROXY")
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        if self.proxy:
            self.session.proxies = {'http': self.proxy, 'https': self.proxy}

    def _unwrap_yahoo_url(self, raw_url: str) -> str:
        """解码 Yahoo 包装的 URL"""
        try:
            parsed = urlparse(raw_url)
            if '/RU=' in raw_url:
                ru_vals = parse_qs(parsed.query).get('RU', [])
                if ru_vals:
                    return unquote(ru_vals[0])
            return raw_url
        except Exception:
            return raw_url

    def search(
        self,
        query: str,
        page: int = 1,
        timelimit: Optional[str] = None,
        max_results: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        执行搜索

        Args:
            query: 搜索关键词
            page: 页码
            timelimit: 时间限制 (d=天, w=周, m=月, y=年)
            max_results: 最大结果数

        Returns:
            搜索结果列表
        """
        # 生成动态 token
        ylt_token = token_urlsafe(24 * 3 // 4)
        ylu_token = token_urlsafe(47 * 3 // 4)

        search_url = f"https://search.yahoo.com/search;_ylt={ylt_token};_ylu={ylu_token}"

        params = {"p": query}
        if page > 1:
            params["b"] = str((page - 1) * 7 + 1)
        if timelimit:
            params["btf"] = timelimit

        try:
            response = self.session.get(search_url, params=params, timeout=15)
            response.raise_for_status()

            tree = html.fromstring(response.content)
            results = []

            # 使用 XPath 提取结果
            items = tree.xpath("//div[contains(@class, 'relsrch')]")

            for item in items[:max_results]:
                try:
                    title_elements = item.xpath(".//div[contains(@class, 'Title')]//h3//text()")
                    href_elements = item.xpath(".//div[contains(@class, 'Title')]//a/@href")
                    body_elements = item.xpath(".//div[contains(@class, 'Text')]//text()")

                    if title_elements and href_elements:
                        title = ''.join(title_elements).strip()
                        href = self._unwrap_yahoo_url(href_elements[0])
                        body = ''.join(body_elements).strip()

                        results.append({
                            'title': title,
                            'href': href,
                            'body': body
                        })
                except Exception as e:
                    continue

            return results

        except Exception as e:
            raise Exception(f"Yahoo 搜索失败: {str(e)}")

    def format_results(self, results: List[Dict[str, Any]], query: str) -> str:
        """格式化搜索结果"""
        output = []
        output.append(f"🔍 Yahoo 搜索: {query}")
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
    parser = argparse.ArgumentParser(description="Yahoo 搜索")
    parser.add_argument("query", help="搜索关键词")
    parser.add_argument("-p", "--page", type=int, default=1, help="页码 (默认: 1)")
    parser.add_argument("-m", "--max-results", type=int, default=None, help="最大结果数 (默认: 不限)")
    parser.add_argument("-t", "--timelimit", choices=['d', 'w', 'm', 'y'], help="时间限制 (d=天, w=周, m=月, y=年)")
    parser.add_argument("--proxy", help="代理地址")
    parser.add_argument("--json", action="store_true", help="JSON 格式输出")
    parser.add_argument("--pretty", action="store_true", help="格式化 JSON")

    args = parser.parse_args()

    try:
        client = YahooSearch(proxy=args.proxy)
        results = client.search(
            query=args.query,
            page=args.page,
            timelimit=args.timelimit,
            max_results=args.max_results
        )

        if args.json:
            output_data = {
                'query': args.query,
                'page': args.page,
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
