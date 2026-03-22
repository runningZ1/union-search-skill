#!/usr/bin/env python3
"""
Exa AI 神经语义搜索引擎
Exa.ai 提供基于神经网络的语义搜索，能够理解查询意图而非仅仅匹配关键词。

免费额度：1000 次/月（约 33 次/天）
申请 API Key: https://exa.ai/
环境变量：EXA_API_KEY
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


class ExaSearchClient:
    """Exa AI 神经语义搜索客户端"""

    ENGINE_NAME = "exa"
    ENGINE_DISPLAY_NAME = "Exa AI 搜索"
    API_ENDPOINT = "https://api.exa.ai/search"
    REQUIRES_API_KEY = True

    def __init__(self, api_key: Optional[str] = None):
        """
        初始化 Exa 客户端

        Args:
            api_key: API Key，如不传则从环境变量 EXA_API_KEY 读取
        """
        self.api_key = api_key or os.environ.get("EXA_API_KEY")
        if not self.api_key:
            raise ValueError("Exa API Key 未配置，请设置 EXA_API_KEY 环境变量")

        self.session = requests.Session()
        self.session.headers.update({
            'x-api-key': self.api_key,
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        })

    def search(
        self,
        query: str,
        max_results: int = 10,
        search_type: str = "auto",
        include_text: bool = True,
        timeout: int = 15,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        执行神经语义搜索

        Args:
            query: 搜索关键词
            max_results: 最大结果数
            search_type: 搜索类型 (auto | neural | keyword)
            include_text: 是否包含页面文本内容
            timeout: 请求超时时间 (秒)

        Returns:
            搜索结果列表
        """
        # 构建请求体
        body = {
            "query": query,
            "numResults": max_results,
            "type": search_type,
        }

        # 可选：包含文本内容
        if include_text:
            body["contents"] = {"text": {"maxCharacters": 500}}

        try:
            response = self.session.post(
                self.API_ENDPOINT,
                json=body,
                timeout=timeout
            )
            response.raise_for_status()

            data = response.json()
            raw_results = data.get("results", [])

            # 标准化输出格式
            results = []
            for item in raw_results:
                title = item.get("title", "").strip()
                url = item.get("url", "").strip()

                # 获取文本内容（可能在 contents.text 或直接在 item 中）
                contents = item.get("contents") or {}
                snippet = (
                    contents.get("text")
                    or item.get("text")
                    or item.get("excerpt")
                    or item.get("summary")
                    or ""
                ).strip()

                # 截断过长的 snippet
                if len(snippet) > 500:
                    snippet = snippet[:500].rsplit(" ", 1)[0] + "..."

                if title and url:
                    results.append({
                        'title': title,
                        'href': url,
                        'body': snippet,
                        'engine': self.ENGINE_NAME,
                        'score': item.get("score"),
                    })

            return results

        except requests.exceptions.HTTPError as e:
            if e.response.status_code in (401, 403):
                raise Exception("Exa API Key 无效或已过期")
            elif e.response.status_code == 429:
                raise Exception("Exa 请求频率受限，请稍后重试")
            else:
                raise Exception(f"Exa API 请求失败：HTTP {e.response.status_code}")
        except requests.exceptions.Timeout:
            raise Exception("Exa 搜索超时")
        except requests.exceptions.RequestException as e:
            raise Exception(f"Exa 搜索失败：{str(e)}")
        except ValueError as e:
            raise Exception(f"Exa 响应解析失败：{str(e)}")

    def format_results(self, results: List[Dict[str, Any]], query: str) -> str:
        """格式化搜索结果用于终端输出"""
        output = []
        output.append(f"🧠 {self.ENGINE_DISPLAY_NAME}: {query}")
        output.append(f"📊 找到 {len(results)} 条结果")
        output.append("")

        for i, item in enumerate(results, 1):
            title = item.get('title', '')
            href = item.get('href', '')
            body = item.get('body', '')
            score = item.get('score')

            output.append(f"[{i}] {title}")
            output.append(f"    🔗 {href}")
            if score is not None:
                output.append(f"    📈 相关性评分：{score:.2f}")
            if body:
                output.append(f"    📝 {body[:200]}{'...' if len(body) > 200 else ''}")
            output.append("")

        return "\n".join(output)


def search_exa(
    query: str,
    max_results: int = 10,
    api_key: Optional[str] = None,
    search_type: str = "auto",
    include_text: bool = True,
    **kwargs
) -> List[Dict[str, Any]]:
    """搜索函数 (供 union_search.py 调用)"""
    client = ExaSearchClient(api_key=api_key)
    return client.search(
        query=query,
        max_results=max_results,
        search_type=search_type,
        include_text=include_text,
        **kwargs
    )


# CLI 入口
if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Exa AI 神经语义搜索")
    parser.add_argument("query", help="搜索关键词")
    parser.add_argument("-m", "--max-results", type=int, default=10)
    parser.add_argument("--type", dest="search_type", choices=["auto", "neural", "keyword"], default="auto")
    parser.add_argument("--no-text", dest="include_text", action="store_false", help="不包含页面文本")
    parser.add_argument("--api-key", help="Exa API Key（不传则从环境变量读取）")
    parser.add_argument("--json", action="store_true", help="JSON 输出")

    args = parser.parse_args()

    try:
        results = search_exa(
            args.query,
            args.max_results,
            api_key=args.api_key,
            search_type=args.search_type,
            include_text=args.include_text
        )

        if args.json:
            print(json.dumps({'results': results}, ensure_ascii=False, indent=2))
        else:
            client = ExaSearchClient(api_key=args.api_key)
            print(client.format_results(results, args.query))
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
