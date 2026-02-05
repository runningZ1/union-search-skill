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
        # 使用移动版 User-Agent 以获取纯 HTML 响应
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1',
            'Accept-Encoding': 'gzip, deflate'
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

        # 设置 Cookie - 添加更多参数以获取纯 HTML 版本
        cookies = {
            "_EDGE_CD": f"m={lang}-{country}&u={lang}-{country}",
            "_EDGE_S": f"mkt={lang}-{country}&ui={lang}-{country}",
            "SRCHD": "AF=NOFORM",
            "SRCHUID": "V=2",
            "_EDGE_V": "1",
            "MUID": "0",
        }

        # 添加额外的请求头以避免 JavaScript 渲染
        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': f'{lang}-{country},{lang};q=0.9,en;q=0.8',
            'Cache-Control': 'max-age=0',
            'Upgrade-Insecure-Requests': '1',
        }

        try:
            response = self.session.get(
                search_url,
                params=params,
                cookies=cookies,
                headers=headers,
                timeout=15
            )
            response.raise_for_status()

            tree = html.fromstring(response.content)
            results = []

            # 使用 XPath 提取结果 - 移动版使用 div 而不是 li
            items = tree.xpath("//div[contains(@class, 'b_algo')]")

            for item in items[:max_results]:
                try:
                    # 移动版结构: div.b_algo > div.b_algoheader > a > h2
                    title_elements = item.xpath(".//h2//text()")
                    href_elements = item.xpath(".//a/@href")
                    body_elements = item.xpath(".//p//text()")

                    if title_elements and href_elements:
                        title = ''.join(title_elements).strip()
                        href = self._unwrap_bing_url(href_elements[0])
                        body = ''.join(body_elements).strip()

                        if title and href:
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
