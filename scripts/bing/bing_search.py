#!/usr/bin/env python3
"""
Bing 搜索模块

使用 Bing Search 进行网络搜索
"""

import os
import sys
import json
import argparse
import requests
import base64
from typing import Optional, Dict, Any, List
from urllib.parse import urlparse, parse_qs
from lxml import html
from dotenv import load_dotenv

# 加载环境变量
script_dir = os.path.dirname(os.path.abspath(__file__))
skill_root = os.path.dirname(os.path.dirname(script_dir))
load_dotenv(os.path.join(skill_root, '.env'))


class BingSearch:
    """Bing 搜索客户端"""

    def __init__(self, proxy: Optional[str] = None):
        """
        初始化客户端

        Args:
            proxy: 代理地址 (如 http://127.0.0.1:7890)
        """
        self.proxy = proxy or os.getenv("BING_PROXY")
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        if self.proxy:
            self.session.proxies = {'http': self.proxy, 'https': self.proxy}

    def _unwrap_bing_url(self, raw_url: str) -> Optional[str]:
        """解码 Bing 包装的 URL"""
        try:
            parsed = urlparse(raw_url)
            u_vals = parse_qs(parsed.query).get("u", [])
            if not u_vals:
                return raw_url
            u = u_vals[0]
            if len(u) <= 2:
                return raw_url
            b64_part = u[2:]
            padding = "=" * (-len(b64_part) % 4)
            decoded = base64.urlsafe_b64decode(b64_part + padding)
            return decoded.decode()
        except Exception:
            return raw_url

    def search(
        self,
        query: str,
        page: int = 1,
        lang: str = "en",
        country: str = "us",
        timelimit: Optional[str] = None,
        max_results: int = 10
    ) -> List[Dict[str, Any]]:
        """
        执行搜索

        Args:
            query: 搜索关键词
            page: 页码
            lang: 语言代码 (默认: en)
            country: 国家代码 (默认: us)
            timelimit: 时间限制 (d=天, w=周, m=月, y=年)
            max_results: 最大结果数

        Returns:
            搜索结果列表
        """
        search_url = "https://www.bing.com/search"

        params = {
            "q": query,
            "pq": query,
            "cc": f"{lang}-{country}",
            "FORM": "QBRE"
        }

        if page > 1:
            params["first"] = str((page - 1) * 10)

        # 时间限制过滤器
        if timelimit:
            time_map = {
                'd': 'ex1:"ez1"',
                'w': 'ex1:"ez2"',
                'm': 'ex1:"ez3"',
                'y': 'ex1:"ez5"'
            }
            params["filters"] = time_map.get(timelimit, '')

        # 设置 Cookie
        cookies = {
            "_EDGE_CD": f"m={lang}-{country}&u={lang}-{country}",
            "_EDGE_S": f"mkt={lang}-{country}&ui={lang}-{country}",
        }

        try:
            response = self.session.get(
                search_url,
                params=params,
                cookies=cookies,
                timeout=15
            )
            response.raise_for_status()

            tree = html.fromstring(response.content)
            results = []

            # 使用 XPath 提取结果
            items = tree.xpath("//li[contains(@class, 'b_algo')]")

            for item in items[:max_results]:
                try:
                    title_elements = item.xpath(".//h2/a//text()")
                    href_elements = item.xpath(".//h2/a/@href")
                    body_elements = item.xpath(".//p//text()")

                    if title_elements and href_elements:
                        title = ''.join(title_elements).strip()
                        href = self._unwrap_bing_url(href_elements[0])
                        body = ''.join(body_elements).strip()

                        results.append({
                            'title': title,
                            'href': href,
                            'body': body
                        })
                except Exception:
                    continue

            return results

        except Exception as e:
            raise Exception(f"Bing 搜索失败: {str(e)}")

    def format_results(self, results: List[Dict[str, Any]], query: str) -> str:
        """格式化搜索结果"""
        output = []
        output.append(f"🔍 Bing 搜索: {query}")
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
    parser = argparse.ArgumentParser(description="Bing 搜索")
    parser.add_argument("query", help="搜索关键词")
    parser.add_argument("-p", "--page", type=int, default=1, help="页码 (默认: 1)")
    parser.add_argument("-m", "--max-results", type=int, default=10, help="最大结果数 (默认: 10)")
    parser.add_argument("-l", "--lang", default="en", help="语言代码 (默认: en)")
    parser.add_argument("-c", "--country", default="us", help="国家代码 (默认: us)")
    parser.add_argument("-t", "--timelimit", choices=['d', 'w', 'm', 'y'], help="时间限制 (d=天, w=周, m=月, y=年)")
    parser.add_argument("--proxy", help="代理地址")
    parser.add_argument("--json", action="store_true", help="JSON 格式输出")
    parser.add_argument("--pretty", action="store_true", help="格式化 JSON")

    args = parser.parse_args()

    try:
        client = BingSearch(proxy=args.proxy)
        results = client.search(
            query=args.query,
            page=args.page,
            lang=args.lang,
            country=args.country,
            timelimit=args.timelimit,
            max_results=args.max_results
        )

        if args.json:
            output_data = {
                'query': args.query,
                'page': args.page,
                'lang': args.lang,
                'country': args.country,
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
