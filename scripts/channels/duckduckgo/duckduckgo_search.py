#!/usr/bin/env python3
"""
DuckDuckGo 搜索模块

使用 DuckDuckGo HTML 版本进行网络搜索
"""

import os
import sys
import json
import argparse
import requests
from typing import Optional, Dict, Any, List
from lxml import html
from dotenv import load_dotenv

# 加载环境变量
script_dir = os.path.dirname(os.path.abspath(__file__))
skill_root = os.path.dirname(os.path.dirname(os.path.dirname(script_dir)))
load_dotenv(os.path.join(skill_root, '.env'))


class DuckDuckGoSearch:
    """DuckDuckGo 搜索客户端"""

    def __init__(self, proxy: Optional[str] = None):
        """
        初始化客户端

        Args:
            proxy: 代理地址 (如 http://127.0.0.1:7890)
        """
        self.proxy = proxy or os.getenv("DUCKDUCKGO_PROXY")
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        if self.proxy:
            self.session.proxies = {'http': self.proxy, 'https': self.proxy}

    def search(
        self,
        query: str,
        page: int = 1,
        region: str = "wt-wt",
        timelimit: Optional[str] = None,
        max_results: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        执行搜索

        Args:
            query: 搜索关键词
            page: 页码
            region: 地区代码 (默认: wt-wt 全球)
            timelimit: 时间限制 (d=天, w=周, m=月, y=年)
            max_results: 最大结果数

        Returns:
            搜索结果列表
        """
        search_url = "https://html.duckduckgo.com/html/"

        # 构建 POST 数据
        data = {
            "q": query,
            "b": "",
            "l": region
        }

        if page > 1:
            # DuckDuckGo 分页: 第1页=0, 第2页=10, 第3页=25, 第4页=40...
            data["s"] = str(10 + (page - 2) * 15) if page > 1 else "0"

        if timelimit:
            data["df"] = timelimit

        try:
            response = self.session.post(search_url, data=data, timeout=15)
            response.raise_for_status()

            tree = html.fromstring(response.content)
            results = []

            # 使用 XPath 提取结果
            items = tree.xpath("//div[contains(@class, 'result')]")

            for item in items[:max_results]:
                try:
                    title_elements = item.xpath(".//h2//a//text()")
                    href_elements = item.xpath(".//h2//a/@href")
                    body_elements = item.xpath(".//a[@class='result__snippet']//text()")

                    if title_elements and href_elements:
                        title = ''.join(title_elements).strip()
                        href = href_elements[0]
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
            raise Exception(f"DuckDuckGo 搜索失败: {str(e)}")

    def format_results(self, results: List[Dict[str, Any]], query: str) -> str:
        """格式化搜索结果"""
        output = []
        output.append(f"🔍 DuckDuckGo 搜索: {query}")
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
    parser = argparse.ArgumentParser(description="DuckDuckGo 搜索")
    parser.add_argument("query", help="搜索关键词")
    parser.add_argument("-p", "--page", type=int, default=1, help="页码 (默认: 1)")
    parser.add_argument("-m", "--max-results", type=int, default=None, help="最大结果数 (默认: 不限)")
    parser.add_argument("-r", "--region", default="wt-wt", help="地区代码 (默认: wt-wt)")
    parser.add_argument("-t", "--timelimit", choices=['d', 'w', 'm', 'y'], help="时间限制 (d=天, w=周, m=月, y=年)")
    parser.add_argument("--proxy", help="代理地址")
    parser.add_argument("--json", action="store_true", help="JSON 格式输出")
    parser.add_argument("--pretty", action="store_true", help="格式化 JSON")

    args = parser.parse_args()

    try:
        client = DuckDuckGoSearch(proxy=args.proxy)
        results = client.search(
            query=args.query,
            page=args.page,
            region=args.region,
            timelimit=args.timelimit,
            max_results=args.max_results
        )

        if args.json:
            output_data = {
                'query': args.query,
                'page': args.page,
                'region': args.region,
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
