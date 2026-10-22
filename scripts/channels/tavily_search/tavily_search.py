#!/usr/bin/env python3
"""
Tavily Search - 综合搜索模块

使用 Tavily AI 搜索引擎进行网络搜索
"""

import os
import sys
import json
import argparse
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv

# 加载环境变量 - 从 union-search-skill 根目录
script_dir = os.path.dirname(os.path.abspath(__file__))
skill_root = os.path.dirname(os.path.dirname(os.path.dirname(script_dir)))
load_dotenv(os.path.join(skill_root, '.env'))


class TavilySearchClient:
    """Tavily 搜索客户端"""

    def __init__(self, api_key: str = None):
        """
        初始化客户端

        Args:
            api_key: Tavily API Key
        """
        self.api_key = api_key or os.getenv("TAVILY_API_KEY")

        if not self.api_key:
            raise ValueError("未找到 TAVILY_API_KEY，请检查 .env 文件")

        # 导入 Tavily 客户端
        try:
            from tavily import TavilyClient
            self.client = TavilyClient(api_key=self.api_key)
        except ImportError:
            raise ImportError("请安装 tavily-python: pip install tavily-python")

    def search(
        self,
        query: str,
        max_results: Optional[int] = None,
        search_depth: str = None,
        topic: str = None,
        include_answer: bool = False
    ) -> Dict[str, Any]:
        """
        执行搜索

        Args:
            query: 搜索关键词
            max_results: 最大结果数量
            search_depth: 搜索深度 (basic, advanced, fast)
            topic: 搜索主题 (general, news, finance)
            include_answer: 是否包含 AI 答案

        Returns:
            搜索结果字典
        """
        kwargs = {"query": query}
        if max_results is not None:
            kwargs["max_results"] = max_results

        if search_depth:
            kwargs["search_depth"] = search_depth
        if topic:
            kwargs["topic"] = topic
        if include_answer:
            kwargs["include_answer"] = True

        return self.client.search(**kwargs)

    def format_results(self, data: Dict[str, Any]) -> str:
        """格式化搜索结果"""
        output = []

        output.append(f"🔍 搜索: {data.get('query', '')}")
        output.append("")

        if data.get('answer'):
            output.append(f"💡 AI 答案: {data['answer']}")
            output.append("")

        output.append(f"📊 找到 {len(data.get('results', []))} 条结果:")
        output.append("")

        for i, item in enumerate(data.get('results', []), 1):
            output.append(f"[{i}] {item.get('title', 'N/A')}")
            output.append(f"    🔗 {item.get('url', 'N/A')}")

            content = item.get('content', '')
            if content:
                # 限制内容长度
                display_content = content[:150] + "..." if len(content) > 150 else content
                output.append(f"    📝 {display_content}")

            output.append("")

        return "\n".join(output)


def main():
    parser = argparse.ArgumentParser(description="Tavily AI 搜索")
    parser.add_argument("query", help="搜索关键词")
    parser.add_argument("--max-results", type=int, default=None, help="最大结果数量")
    parser.add_argument("--search-depth", choices=["basic", "advanced", "fast"], help="搜索深度")
    parser.add_argument("--topic", choices=["general", "news", "finance"], help="搜索主题")
    parser.add_argument("--include-answer", action="store_true", help="包含 AI 生成的答案")
    parser.add_argument("--json", action="store_true", help="JSON 格式输出")
    parser.add_argument("--pretty", action="store_true", help="格式化 JSON")

    args = parser.parse_args()

    try:
        client = TavilySearchClient()

        result = client.search(
            query=args.query,
            max_results=args.max_results,
            search_depth=args.search_depth,
            topic=args.topic,
            include_answer=args.include_answer
        )

        if args.json:
            if args.pretty:
                print(json.dumps(result, indent=2, ensure_ascii=False))
            else:
                print(json.dumps(result, ensure_ascii=False))
        else:
            print(client.format_results(result))

    except Exception as e:
        print(f"错误: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
