#!/usr/bin/env python3
"""
Yandex 搜索模块 (SerpAPI)

基于 SerpAPI 的 Yandex 引擎进行搜索。
"""

import os
import sys
import json
import argparse
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv

# 加载环境变量
script_dir = os.path.dirname(os.path.abspath(__file__))
skill_root = os.path.dirname(os.path.dirname(script_dir))
load_dotenv(os.path.join(skill_root, '.env'))

try:
    from serpapi import GoogleSearch
except ImportError:
    print(
        "错误: 需要 'google-search-results' 依赖，请先执行: pip install google-search-results",
        file=sys.stderr
    )
    sys.exit(1)


class YandexSerpApiSearch:
    """Yandex 搜索客户端 (SerpAPI)"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_keys: List[str] = []
        if api_key:
            self.api_keys.append(api_key)

        env_keys = {k: v for k, v in os.environ.items() if k.startswith("SERPAPI_API_KEY") and v}
        for key_name in sorted(env_keys.keys()):
            key_value = env_keys[key_name]
            if key_value not in self.api_keys:
                self.api_keys.append(key_value)

        if not self.api_keys:
            raise ValueError("未找到 SerpAPI Key，请设置 SERPAPI_API_KEY_YANDEX 或 SERPAPI_API_KEY，或传入 --api-key")

    def search(
        self,
        query: str,
        page: int = 1,
        max_results: int = 10,
        yandex_domain: str = "yandex.com",
        lang: str = "en",
        lr: str = "84"
    ) -> List[Dict[str, Any]]:
        last_error: Optional[Exception] = None
        for current_key in self.api_keys:
            params = {
                "engine": "yandex",
                "text": query,
                "yandex_domain": yandex_domain,
                "lang": lang,
                "lr": lr,
                "api_key": current_key,
            }

            if page > 1:
                params["p"] = page - 1

            try:
                search = GoogleSearch(params)
                data = search.get_dict()

                if "error" in data:
                    raise Exception(data["error"])

                organic_results = data.get("organic_results", [])
                results: List[Dict[str, Any]] = []
                for item in organic_results[:max_results]:
                    results.append({
                        "title": item.get("title", ""),
                        "href": item.get("link", ""),
                        "body": item.get("snippet", ""),
                        "displayed_link": item.get("displayed_link", "")
                    })
                return results
            except Exception as exc:
                last_error = exc
                continue

        raise Exception(f"SerpAPI 返回错误: {last_error}")

    def format_results(self, results: List[Dict[str, Any]], query: str) -> str:
        output = []
        output.append(f"🔍 Yandex 搜索: {query}")
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
    parser = argparse.ArgumentParser(description="Yandex 搜索 (SerpAPI)")
    parser.add_argument("query", help="搜索关键词")
    parser.add_argument("-p", "--page", type=int, default=1, help="页码 (默认: 1)")
    parser.add_argument("-m", "--max-results", type=int, default=10, help="最大结果数 (默认: 10)")
    parser.add_argument("--yandex-domain", default="yandex.com", help="Yandex 域名 (默认: yandex.com)")
    parser.add_argument("-l", "--lang", default="en", help="语言代码 (默认: en)")
    parser.add_argument("--lr", default="84", help="地域参数 (默认: 84)")
    parser.add_argument("--api-key", help="SerpAPI Key")
    parser.add_argument("--json", action="store_true", help="JSON 格式输出")
    parser.add_argument("--pretty", action="store_true", help="格式化 JSON")

    args = parser.parse_args()

    try:
        client = YandexSerpApiSearch(api_key=args.api_key)
        results = client.search(
            query=args.query,
            page=args.page,
            max_results=args.max_results,
            yandex_domain=args.yandex_domain,
            lang=args.lang,
            lr=args.lr
        )

        if args.json:
            output_data = {
                "query": args.query,
                "page": args.page,
                "lang": args.lang,
                "lr": args.lr,
                "total_results": len(results),
                "results": results
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
