#!/usr/bin/env python3
"""
Serper Google 搜索 API
Serper 提供 Google 搜索 API 接口，免费额度 2500 次/天。

申请 API Key: https://serper.dev/
环境变量：SERPER_API_KEY
"""

import sys
import os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from typing import Dict, Any, List, Optional
import requests
from dotenv import load_dotenv

# 加载环境变量
script_dir = Path(__file__).parent.parent.parent
load_dotenv(script_dir / '.env')


class SerperSearchClient:
    """Serper Google 搜索客户端"""

    ENGINE_NAME = "serper"
    ENGINE_DISPLAY_NAME = "Serper Google 搜索"
    API_ENDPOINT = "https://google.serper.dev/search"
    REQUIRES_API_KEY = True

    def __init__(self, api_key: Optional[str] = None):
        """
        初始化 Serper 客户端

        Args:
            api_key: API Key，如不传则从环境变量 SERPER_API_KEY 读取
        """
        self.api_key = api_key or os.environ.get("SERPER_API_KEY")
        if not self.api_key:
            raise ValueError("Serper API Key 未配置，请设置 SERPER_API_KEY 环境变量")

        self.session = requests.Session()
        self.session.headers.update({
            'X-API-KEY': self.api_key,
            'Content-Type': 'application/json',
        })

    def search(
        self,
        query: str,
        max_results: int = 10,
        num: int = 10,
        page: int = 1,
        gl: str = "us",
        hl: str = "en",
        location: Optional[str] = None,
        timeout: int = 15,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        执行 Google 搜索

        Args:
            query: 搜索关键词
            max_results: 最大结果数
            num: 每页结果数（最大 100）
            page: 页码（从 1 开始）
            gl: 国家/地区代码 (默认 us)
            hl: 语言代码 (默认 en)
            location: 特定地理位置（如 "New York, NY"）
            timeout: 请求超时时间 (秒)

        Returns:
            搜索结果列表
        """
        # 构建请求体
        body = {
            "q": query,
            "num": min(num, 100),
            "gl": gl,
            "hl": hl,
            "page": page,
        }

        # 可选：指定地理位置
        if location:
            body["location"] = location

        try:
            response = self.session.post(
                self.API_ENDPOINT,
                json=body,
                timeout=timeout
            )
            response.raise_for_status()

            data = response.json()

            # Serper 返回的有机搜索结果在 organic 字段
            raw_results = data.get("organic", [])

            # 标准化输出格式
            results = []
            for idx, item in enumerate(raw_results[:max_results]):
                title = item.get("title", "").strip()
                url = item.get("link", "").strip()
                snippet = item.get("snippet", "").strip()

                # 额外信息
                position = item.get("position")
                source = item.get("source")

                if title and url:
                    results.append({
                        'title': title,
                        'href': url,
                        'body': snippet,
                        'engine': self.ENGINE_NAME,
                        'position': position,
                        'source': source,
                    })

            return results

        except requests.exceptions.HTTPError as e:
            if e.response.status_code in (401, 403):
                raise Exception("Serper API Key 无效或已过期")
            elif e.response.status_code == 429:
                raise Exception("Serper 请求频率受限，请稍后重试")
            else:
                raise Exception(f"Serper API 请求失败：HTTP {e.response.status_code}")
        except requests.exceptions.Timeout:
            raise Exception("Serper 搜索超时")
        except requests.exceptions.RequestException as e:
            raise Exception(f"Serper 搜索失败：{str(e)}")
        except ValueError as e:
            raise Exception(f"Serper 响应解析失败：{str(e)}")

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
            position = item.get('position')
            source = item.get('source')

            position_str = f"#{position}" if position else f"[{i}]"
            output.append(f"{position_str} {title}")
            output.append(f"    🔗 {href}")
            if source:
                output.append(f"    📰 来源：{source}")
            if body:
                output.append(f"    📝 {body[:200]}{'...' if len(body) > 200 else ''}")
            output.append("")

        return "\n".join(output)


def search_serper(
    query: str,
    max_results: int = 10,
    api_key: Optional[str] = None,
    **kwargs
) -> List[Dict[str, Any]]:
    """搜索函数 (供 union_search.py 调用)"""
    client = SerperSearchClient(api_key=api_key)
    return client.search(query=query, max_results=max_results, **kwargs)


# CLI 入口
if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Serper Google 搜索 API")
    parser.add_argument("query", help="搜索关键词")
    parser.add_argument("-m", "--max-results", type=int, default=10)
    parser.add_argument("--page", type=int, default=1, help="页码")
    parser.add_argument("--gl", default="us", help="国家/地区代码")
    parser.add_argument("--hl", default="en", help="语言代码")
    parser.add_argument("--location", help="特定地理位置")
    parser.add_argument("--api-key", help="Serper API Key")
    parser.add_argument("--json", action="store_true", help="JSON 输出")

    args = parser.parse_args()

    try:
        results = search_serper(
            args.query,
            args.max_results,
            api_key=args.api_key,
            page=args.page,
            gl=args.gl,
            hl=args.hl,
            location=args.location
        )

        if args.json:
            print(json.dumps({'results': results}, ensure_ascii=False, indent=2))
        else:
            client = SerperSearchClient(api_key=args.api_key)
            print(client.format_results(results, args.query))
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
