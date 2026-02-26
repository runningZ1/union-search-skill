#!/usr/bin/env python3
"""
Jina 搜索模块

使用 Jina Search API 进行搜索。
"""

import os
import sys
import json
import argparse
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List

import requests
from dotenv import load_dotenv

# 加载环境变量
script_dir = os.path.dirname(os.path.abspath(__file__))
skill_root = os.path.dirname(os.path.dirname(script_dir))
load_dotenv(os.path.join(skill_root, ".env"))


class JinaSearch:
    """Jina Search API 客户端"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("JINA_API_KEY", "")
        self.base_url = "https://s.jina.ai/"
        if not self.api_key:
            raise ValueError("未找到 JINA_API_KEY，请在 .env 中配置或通过 --api-key 传入")

    def search(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "X-Respond-With": "no-content",
            "Accept": "application/json",
        }
        params = {"q": query}

        response = requests.get(self.base_url, headers=headers, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()

        raw_items = data.get("data", []) if isinstance(data, dict) else []
        results: List[Dict[str, Any]] = []
        for item in raw_items[:max_results]:
            if not isinstance(item, dict):
                continue
            body = item.get("description") or item.get("content") or ""
            results.append(
                {
                    "title": item.get("title", ""),
                    "href": item.get("url", ""),
                    "body": body,
                }
            )

        return results

    def save_response(self, query: str, output_data: Dict[str, Any]) -> str:
        responses_dir = Path(__file__).parent / "responses"
        responses_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_query = "".join(c if c.isalnum() else "_" for c in query)[:50]
        filename = responses_dir / f"{timestamp}_{safe_query}.json"

        with open(filename, "w", encoding="utf-8") as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        return str(filename)

    def format_results(self, results: List[Dict[str, Any]], query: str) -> str:
        output = []
        output.append(f"🔍 Jina 搜索: {query}")
        output.append(f"📊 找到 {len(results)} 条结果")
        output.append("")

        for i, item in enumerate(results, 1):
            output.append(f"[{i}] {item.get('title', '')}")
            output.append(f"    🔗 {item.get('href', '')}")
            if item.get("body"):
                output.append(f"    📝 {item.get('body', '')}")
            output.append("")

        return "\n".join(output)


def main():
    parser = argparse.ArgumentParser(description="Jina 搜索")
    parser.add_argument("query", help="搜索关键词")
    parser.add_argument("-m", "--max-results", type=int, default=10, help="最大结果数 (默认: 10)")
    parser.add_argument("--api-key", help="Jina API Key")
    parser.add_argument("--save-response", action="store_true", help="保存响应到 scripts/jina/responses")
    parser.add_argument("--json", action="store_true", help="JSON 格式输出")
    parser.add_argument("--pretty", action="store_true", help="格式化 JSON")
    args = parser.parse_args()

    try:
        client = JinaSearch(api_key=args.api_key)
        results = client.search(query=args.query, max_results=args.max_results)
        output_data = {
            "query": args.query,
            "total_results": len(results),
            "results": results,
        }

        saved_file = None
        if args.save_response:
            saved_file = client.save_response(args.query, output_data)

        if args.json:
            if args.pretty:
                print(json.dumps(output_data, indent=2, ensure_ascii=False))
            else:
                print(json.dumps(output_data, ensure_ascii=False))
            if saved_file:
                print(f"\nSaved: {saved_file}", file=sys.stderr)
        else:
            print(client.format_results(results, args.query))
            if saved_file:
                print(f"\n响应已保存: {saved_file}")

    except Exception as e:
        print(f"错误: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
