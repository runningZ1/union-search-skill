#!/usr/bin/env python3
"""
秘塔搜索 (Metaso) API 客户端
用于执行网络搜索并返回结构化结果

使用方法:
    python metaso_search.py "搜索关键词" [--size 10] [--summary] [--raw-content]

环境变量:
    METASO_API_KEY: 秘塔搜索 API 密钥 (必需)
"""

import http.client
import json
import os
import sys
import argparse
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from datetime import datetime


@dataclass
class WebpageResult:
    """单个搜索结果"""
    title: str
    link: str
    score: str
    summary: Optional[str] = None
    snippet: Optional[str] = None
    position: int = 0
    date: Optional[str] = None
    authors: Optional[List[str]] = None


@dataclass
class SearchResult:
    """搜索响应"""
    credits: int
    query: str
    total: int
    webpages: List[WebpageResult]
    search_parameters: Dict[str, Any]


class MetasoClient:
    """秘塔搜索 API 客户端"""

    API_HOST = "metaso.cn"
    API_ENDPOINT = "/api/v1/search"

    def __init__(self, api_key: Optional[str] = None):
        """
        初始化客户端

        Args:
            api_key: API 密钥，如未提供则从环境变量 METASO_API_KEY 获取
        """
        self.api_key = api_key or os.environ.get("METASO_API_KEY")
        if not self.api_key:
            raise ValueError(
                "API 密钥未设置。请通过以下方式之一提供:\n"
                "1. 传入 api_key 参数\n"
                "2. 设置环境变量 METASO_API_KEY\n"
                "3. 创建 .env 文件并添加 METASO_API_KEY=your_key"
            )

    def search(
        self,
        query: str,
        size: int = 10,
        scope: str = "webpage",
        include_summary: bool = True,
        include_raw_content: bool = False,
        concise_snippet: bool = True
    ) -> SearchResult:
        """
        执行搜索

        Args:
            query: 搜索关键词
            size: 返回结果数量 (1-50)
            scope: 搜索范围 ("webpage" 或 "file")
            include_summary: 是否包含 AI 生成的摘要
            include_raw_content: 是否包含原始网页内容
            concise_snippet: 是否使用简洁的片段

        Returns:
            SearchResult 对象
        """
        payload = {
            "q": query,
            "scope": scope,
            "includeSummary": include_summary,
            "size": str(size),
            "includeRawContent": include_raw_content,
            "conciseSnippet": concise_snippet
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

        conn = http.client.HTTPSConnection(self.API_HOST)
        try:
            conn.request("POST", self.API_ENDPOINT, json.dumps(payload), headers)
            response = conn.getresponse()
            data = json.loads(response.read().decode("utf-8"))

            if response.status != 200:
                raise Exception(f"API 请求失败: {response.status} - {data}")

            return self._parse_response(data)
        finally:
            conn.close()

    def _parse_response(self, data: Dict[str, Any]) -> SearchResult:
        """解析 API 响应"""
        webpages = []
        for wp in data.get("webpages", []):
            webpages.append(WebpageResult(
                title=wp.get("title", ""),
                link=wp.get("link", ""),
                score=wp.get("score", ""),
                summary=wp.get("summary"),
                snippet=wp.get("snippet"),
                position=wp.get("position", 0),
                date=wp.get("date"),
                authors=wp.get("authors")
            ))

        return SearchResult(
            credits=data.get("credits", 0),
            query=data.get("searchParameters", {}).get("q", ""),
            total=data.get("total", 0),
            webpages=webpages,
            search_parameters=data.get("searchParameters", {})
        )


def format_markdown(result: SearchResult) -> str:
    """将搜索结果格式化为 Markdown"""
    lines = [
        f"# 搜索结果: {result.query}",
        "",
        f"**找到 {result.total} 条结果，显示前 {len(result.webpages)} 条** | 剩余积分: {result.credits}",
        "",
        "---",
        ""
    ]

    for wp in result.webpages:
        lines.append(f"## {wp.position}. {wp.title}")
        lines.append(f"**链接**: {wp.link}")
        if wp.date:
            lines.append(f"**日期**: {wp.date}")
        lines.append(f"**相关度**: {wp.score}")
        lines.append("")

        if wp.summary:
            lines.append("**摘要**:")
            lines.append(wp.summary)
            lines.append("")
        elif wp.snippet:
            lines.append("**片段**:")
            lines.append(wp.snippet)
            lines.append("")

        lines.append("---")
        lines.append("")

    return "\n".join(lines)


def format_json(result: SearchResult) -> str:
    """将搜索结果格式化为 JSON"""
    data = {
        "query": result.query,
        "total": result.total,
        "credits": result.credits,
        "webpages": [
            {
                "position": wp.position,
                "title": wp.title,
                "link": wp.link,
                "score": wp.score,
                "date": wp.date,
                "summary": wp.summary,
                "snippet": wp.snippet,
                "authors": wp.authors
            }
            for wp in result.webpages
        ]
    }
    return json.dumps(data, ensure_ascii=False, indent=2)


def format_brief(result: SearchResult) -> str:
    """将搜索结果格式化为简要列表"""
    lines = [f"搜索 '{result.query}' 找到 {result.total} 条结果:"]
    for wp in result.webpages:
        lines.append(f"  {wp.position}. [{wp.title}]({wp.link})")
    return "\n".join(lines)


def main():
    """命令行入口"""
    parser = argparse.ArgumentParser(
        description="秘塔搜索 (Metaso) API 客户端",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python metaso_search.py "如何学习 Python"
  python metaso_search.py "AI 发展趋势" --size 20 --format markdown
  python metaso_search.py "机器学习教程" --no-summary --format json
        """
    )

    parser.add_argument("query", help="搜索关键词")
    parser.add_argument("--size", type=int, default=10, help="返回结果数量 (默认: 10)")
    parser.add_argument("--summary", action="store_true", default=True,
                        help="包含 AI 摘要 (默认: 启用)")
    parser.add_argument("--no-summary", action="store_true", help="不包含 AI 摘要")
    parser.add_argument("--raw-content", action="store_true", help="包含原始网页内容")
    parser.add_argument("--format", choices=["markdown", "json", "brief"],
                        default="markdown", help="输出格式 (默认: markdown)")
    parser.add_argument("--scope", choices=["webpage", "file"], default="webpage",
                        help="搜索范围 (默认: webpage)")

    args = parser.parse_args()

    # 处理参数冲突
    include_summary = args.summary and not args.no_summary

    try:
        client = MetasoClient()
        result = client.search(
            query=args.query,
            size=args.size,
            scope=args.scope,
            include_summary=include_summary,
            include_raw_content=args.raw_content
        )

        if args.format == "markdown":
            print(format_markdown(result))
        elif args.format == "json":
            print(format_json(result))
        else:
            print(format_brief(result))

    except ValueError as e:
        print(f"错误: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"搜索失败: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
