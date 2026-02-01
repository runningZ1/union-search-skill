#!/usr/bin/env python3
"""
Anna's Archive 书籍搜索模块

使用 Anna's Archive 搜索电子书
"""

import os
import sys
import json
import argparse
import requests
import re
from typing import Optional, Dict, Any, List
from lxml import html
from dotenv import load_dotenv

# 加载环境变量
script_dir = os.path.dirname(os.path.abspath(__file__))
skill_root = os.path.dirname(os.path.dirname(script_dir))
load_dotenv(os.path.join(skill_root, '.env'))


class AnnasArchiveSearch:
    """Anna's Archive 搜索客户端"""

    BASE_URL = "https://annas-archive.li"

    def __init__(self, proxy: Optional[str] = None):
        """
        初始化客户端

        Args:
            proxy: 代理地址 (如 http://127.0.0.1:7890)
        """
        self.proxy = proxy or os.getenv("ANNASARCHIVE_PROXY")
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
        max_results: int = 10
    ) -> List[Dict[str, Any]]:
        """
        执行搜索

        Args:
            query: 搜索关键词
            page: 页码
            max_results: 最大结果数

        Returns:
            搜索结果列表
        """
        search_url = f"{self.BASE_URL}/search"
        params = {
            "q": query,
            "page": page
        }

        try:
            response = self.session.get(search_url, params=params, timeout=15)
            response.raise_for_status()

            # 移除 HTML 注释
            html_text = re.sub(r'<!--.*?-->', '', response.text, flags=re.DOTALL)
            tree = html.fromstring(html_text)
            results = []

            # 使用 XPath 提取结果
            items = tree.xpath("//div[contains(@class, 'record-list-outer')]/div")

            for item in items[:max_results]:
                try:
                    title_elements = item.xpath(".//a[contains(@class, 'text-lg')]//text()")
                    author_elements = item.xpath(".//a[span[contains(@class, 'user')]]//text()")
                    publisher_elements = item.xpath(".//a[span[contains(@class, 'company')]]//text()")
                    info_elements = item.xpath(".//div[contains(@class, 'text-gray-800')]/text()")
                    url_elements = item.xpath("./a/@href")
                    thumbnail_elements = item.xpath(".//img/@src")

                    title = ''.join(title_elements).strip() if title_elements else ""
                    author = ''.join(author_elements).strip() if author_elements else ""
                    publisher = ''.join(publisher_elements).strip() if publisher_elements else ""
                    info = ''.join(info_elements).strip() if info_elements else ""
                    url = url_elements[0] if url_elements else ""
                    thumbnail = thumbnail_elements[0] if thumbnail_elements else ""

                    # 补全相对 URL
                    if url and not url.startswith('http'):
                        url = f"{self.BASE_URL}{url}"
                    if thumbnail and not thumbnail.startswith('http'):
                        thumbnail = f"{self.BASE_URL}{thumbnail}"

                    if title:
                        results.append({
                            'title': title,
                            'author': author,
                            'publisher': publisher,
                            'info': info,
                            'url': url,
                            'thumbnail': thumbnail
                        })
                except Exception:
                    continue

            return results

        except Exception as e:
            raise Exception(f"Anna's Archive 搜索失败: {str(e)}")

    def format_results(self, results: List[Dict[str, Any]], query: str) -> str:
        """格式化搜索结果"""
        output = []
        output.append(f"📚 Anna's Archive 书籍搜索: {query}")
        output.append(f"📊 找到 {len(results)} 本书")
        output.append("")

        for i, item in enumerate(results, 1):
            output.append(f"[{i}] {item.get('title', '')}")
            if item.get('author'):
                output.append(f"    👤 作者: {item.get('author', '')}")
            if item.get('publisher'):
                output.append(f"    🏢 出版社: {item.get('publisher', '')}")
            if item.get('info'):
                output.append(f"    ℹ️ 信息: {item.get('info', '')}")
            output.append(f"    🔗 {item.get('url', '')}")
            if item.get('thumbnail'):
                output.append(f"    🖼️ 封面: {item.get('thumbnail', '')}")
            output.append("")

        return "\n".join(output)


def main():
    parser = argparse.ArgumentParser(description="Anna's Archive 书籍搜索")
    parser.add_argument("query", help="搜索关键词")
    parser.add_argument("-p", "--page", type=int, default=1, help="页码 (默认: 1)")
    parser.add_argument("-m", "--max-results", type=int, default=10, help="最大结果数 (默认: 10)")
    parser.add_argument("--proxy", help="代理地址")
    parser.add_argument("--json", action="store_true", help="JSON 格式输出")
    parser.add_argument("--pretty", action="store_true", help="格式化 JSON")

    args = parser.parse_args()

    try:
        client = AnnasArchiveSearch(proxy=args.proxy)
        results = client.search(
            query=args.query,
            page=args.page,
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
