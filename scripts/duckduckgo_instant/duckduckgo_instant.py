#!/usr/bin/env python3
"""
DuckDuckGo Instant Answer API - 无需 API Key 版本
使用 DuckDuckGo Instant Answer API 获取即时答案和相关内容

适合事实性问题、定义查询、百科类查询。
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from typing import Dict, Any, List
import requests
from urllib.parse import quote


class DuckDuckGoInstantSearch:
    """DuckDuckGo Instant Answer 搜索 (无需 API Key)"""

    ENGINE_NAME = "duckduckgo_instant"
    ENGINE_DISPLAY_NAME = "DuckDuckGo 即时答案"
    API_URL = "https://api.duckduckgo.com/?q={keyword}&format=json&no_redirect=1&no_html=1"
    REQUIRES_PROXY = False

    def __init__(self, proxy=None):
        self.proxy = proxy
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json,text/javascript,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
        })
        if self.proxy:
            self.session.proxies = {'http': self.proxy, 'https': self.proxy}

    def build_search_url(self, query: str, **kwargs) -> str:
        """构建搜索 URL"""
        encoded_query = quote(query)
        return self.API_URL.replace('{keyword}', encoded_query)

    def parse_results(self, data: dict) -> List[Dict[str, Any]]:
        """解析 JSON 响应结果"""
        results = []

        # 1. Abstract (主要答案)
        abstract_text = data.get('AbstractText', '').strip()
        abstract_url = data.get('AbstractURL', '').strip()
        abstract_source = data.get('AbstractSource', '').strip()

        if abstract_text and abstract_url:
            results.append({
                'title': abstract_source or abstract_text[:50],
                'href': abstract_url,
                'body': abstract_text,
                'engine': self.ENGINE_NAME,
                'type': 'abstract'
            })

        # 2. Results (主要结果列表)
        for result in data.get('Results', []):
            text = result.get('Text', '').strip()
            url = result.get('FirstURL', '').strip()
            if text and url:
                results.append({
                    'title': text.split(' - ')[0].strip()[:80],
                    'href': url,
                    'body': text,
                    'engine': self.ENGINE_NAME,
                    'type': 'result'
                })

        # 3. RelatedTopics (相关主题 - 递归处理)
        def collect_topics(topics: list, depth: int = 0):
            for topic in topics:
                if 'Topics' in topic:  # 嵌套的主题组
                    collect_topics(topic['Topics'], depth + 1)
                else:
                    text = topic.get('Text', '').strip()
                    url = topic.get('FirstURL', '').strip()
                    if text and url and depth < 2:  # 限制递归深度
                        results.append({
                            'title': text.split(' - ')[0].strip()[:80],
                            'href': url,
                            'body': text,
                            'engine': self.ENGINE_NAME,
                            'type': 'related'
                        })

        collect_topics(data.get('RelatedTopics', []))

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

            data = response.json()
            all_results = self.parse_results(data)

            return all_results[:max_results]

        except requests.exceptions.Timeout:
            raise Exception(f"{self.ENGINE_DISPLAY_NAME} 搜索超时")
        except requests.exceptions.RequestException as e:
            raise Exception(f"{self.ENGINE_DISPLAY_NAME} 搜索失败：{str(e)}")
        except ValueError as e:
            raise Exception(f"{self.ENGINE_DISPLAY_NAME} 响应解析失败：{str(e)}")

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
            result_type = item.get('type', '')

            type_icon = "📌" if result_type == 'abstract' else "🔗"
            output.append(f"{type_icon} [{i}] {title}")
            output.append(f"    🔗 {href}")
            if body:
                output.append(f"    📝 {body[:200]}{'...' if len(body) > 200 else ''}")
            output.append("")

        return "\n".join(output)


def search_duckduckgo_instant(query: str, max_results: int = 10, proxy: str = None, **kwargs):
    """搜索函数 (供 union_search.py 调用)"""
    engine = DuckDuckGoInstantSearch(proxy=proxy)
    return engine.search(query, max_results=max_results, **kwargs)


# CLI 入口
if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser(description="DuckDuckGo 即时答案 (无需 API Key)")
    parser.add_argument("query", help="搜索关键词")
    parser.add_argument("-m", "--max-results", type=int, default=10)
    parser.add_argument("--proxy", help="代理地址")
    parser.add_argument("--json", action="store_true", help="JSON 输出")

    args = parser.parse_args()

    results = search_duckduckgo_instant(args.query, args.max_results, args.proxy)

    if args.json:
        print(json.dumps({'results': results}, ensure_ascii=False, indent=2))
    else:
        engine = DuckDuckGoInstantSearch()
        print(engine.format_results(results, args.query))
