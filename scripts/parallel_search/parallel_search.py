import argparse
import json
import os
from typing import Any, Dict, List, Optional

import requests
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), ".env"))

DEFAULT_ENDPOINT = "https://api.parallel.ai/v1/search"
DEFAULT_MODE = "fast"
ALLOWED_MODES = ("turbo", "fast", "basic", "advanced")


class ParallelSearchClient:
    """Parallel Search 客户端，接口文档 https://docs.parallel.ai/api-reference/search/search"""

    ENGINE_NAME = "parallel"
    ENGINE_DISPLAY_NAME = "Parallel Search"
    REQUIRES_API_KEY = True

    def __init__(self, api_key: Optional[str] = None, endpoint: Optional[str] = None):
        self.api_key = api_key or os.environ.get("PARALLEL_API_KEY")
        if not self.api_key:
            raise ValueError("Parallel API Key 未配置，请设置 PARALLEL_API_KEY 环境变量")

        self.endpoint = endpoint or os.environ.get("PARALLEL_SEARCH_ENDPOINT") or DEFAULT_ENDPOINT
        self.session = requests.Session()
        self.session.headers.update({
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
        })

    def search(
        self,
        query: str,
        max_results: int = 10,
        objective: Optional[str] = None,
        search_queries: Optional[List[str]] = None,
        mode: Optional[str] = None,
        location: Optional[str] = None,
        include_domains: Optional[List[str]] = None,
        exclude_domains: Optional[List[str]] = None,
        after_date: Optional[str] = None,
        timeout: int = 30,
    ) -> List[Dict[str, Any]]:
        if not query.strip() and not search_queries:
            raise ValueError("搜索关键词不能为空")

        mode = mode or os.environ.get("PARALLEL_SEARCH_MODE") or DEFAULT_MODE
        if mode not in ALLOWED_MODES:
            raise ValueError(f"mode 只能是 {', '.join(ALLOWED_MODES)}")

        queries = [item.strip() for item in (search_queries or [query]) if item and item.strip()]
        if not queries:
            raise ValueError("search_queries 不能为空")

        body: Dict[str, Any] = {
            "objective": (objective or query).strip(),
            "search_queries": queries,
            "mode": mode,
            "advanced_settings": {"max_results": max_results},
        }
        if location:
            body["advanced_settings"]["location"] = location

        source_policy: Dict[str, Any] = {}
        if include_domains:
            source_policy["include_domains"] = include_domains
        elif exclude_domains:
            source_policy["exclude_domains"] = exclude_domains
        if after_date:
            source_policy["after_date"] = after_date
        if source_policy:
            body["advanced_settings"]["source_policy"] = source_policy

        response = self.session.post(self.endpoint, json=body, timeout=timeout)
        if response.status_code != 200:
            detail = response.text.strip()[:500]
            raise RuntimeError(f"Parallel 搜索请求失败：HTTP {response.status_code} {detail}")

        payload = response.json()
        raw_results = payload.get("results")
        if not isinstance(raw_results, list):
            raise RuntimeError(f"Parallel 响应缺少 results 字段：{payload}")

        warnings = payload.get("warnings") or []
        warning_text = "；".join(
            item.get("message", "") for item in warnings if isinstance(item, dict) and item.get("message")
        )

        results = []
        for item in raw_results[:max_results]:
            url = (item.get("url") or "").strip()
            if not url:
                continue
            excerpts = item.get("excerpts") or []
            body_text = "\n".join(text.strip() for text in excerpts if isinstance(text, str) and text.strip())
            results.append({
                "title": (item.get("title") or url).strip(),
                "href": url,
                "body": body_text,
                "engine": self.ENGINE_NAME,
                "publish_date": item.get("publish_date"),
                "search_id": payload.get("search_id"),
                "session_id": payload.get("session_id"),
                "warnings": warning_text,
            })
        return results

    def format_results(self, results: List[Dict[str, Any]], query: str) -> str:
        output = [
            f"🔍 {self.ENGINE_DISPLAY_NAME}: {query}",
            f"📊 找到 {len(results)} 条结果",
            "",
        ]
        for i, item in enumerate(results, 1):
            output.append(f"[{i}] {item.get('title', '')}")
            output.append(f"    🔗 {item.get('href', '')}")
            if item.get("publish_date"):
                output.append(f"    📅 {item['publish_date']}")
            if item.get("body"):
                body = item["body"]
                output.append(f"    📝 {body[:200]}{'...' if len(body) > 200 else ''}")
            output.append("")
        if results and results[0].get("warnings"):
            output.append(f"⚠️ {results[0]['warnings']}")
        return "\n".join(output)


def search_parallel(
    query: str,
    max_results: int = 10,
    api_key: Optional[str] = None,
    **kwargs,
) -> List[Dict[str, Any]]:
    client = ParallelSearchClient(api_key=api_key)
    return client.search(query=query, max_results=max_results, **kwargs)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Parallel Search API")
    parser.add_argument("query", help="搜索关键词，同时作为 objective")
    parser.add_argument("-m", "--max-results", type=int, default=10, help="结果数量上限")
    parser.add_argument("--objective", help="自然语言搜索目标，默认使用 query")
    parser.add_argument("--search-query", action="append", dest="search_queries", help="关键词短语，可重复传入")
    parser.add_argument("--mode", choices=ALLOWED_MODES, help="搜索模式，默认 fast")
    parser.add_argument("--location", help="ISO 3166-1 alpha-2 国家代码，如 us、jp")
    parser.add_argument("--include-domain", action="append", dest="include_domains", help="只保留这些域名，可重复传入")
    parser.add_argument("--exclude-domain", action="append", dest="exclude_domains", help="排除这些域名，可重复传入")
    parser.add_argument("--after-date", help="只保留该日期之后发布的结果，格式 YYYY-MM-DD")
    parser.add_argument("--api-key", help="Parallel API Key")
    parser.add_argument("--endpoint", help="接口地址，默认 https://api.parallel.ai/v1/search")
    parser.add_argument("--timeout", type=int, default=30, help="请求超时秒数")
    parser.add_argument("--json", action="store_true", help="JSON 输出")

    args = parser.parse_args()

    client = ParallelSearchClient(api_key=args.api_key, endpoint=args.endpoint)
    results = client.search(
        query=args.query,
        max_results=args.max_results,
        objective=args.objective,
        search_queries=args.search_queries,
        mode=args.mode,
        location=args.location,
        include_domains=args.include_domains,
        exclude_domains=args.exclude_domains,
        after_date=args.after_date,
        timeout=args.timeout,
    )

    if args.json:
        print(json.dumps({"results": results}, ensure_ascii=False, indent=2))
    else:
        print(client.format_results(results, args.query))
