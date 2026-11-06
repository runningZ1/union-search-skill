import argparse
import json
import os
from typing import Any, Dict, List, Optional

import requests
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), ".env"))

DEFAULT_ENDPOINT = "https://api.keenable.ai/v1/search"
# 免 Key 公共端点要求用 X-Keenable-Title 标明调用方
APP_TITLE = "union-search-skill"
# 接口单次 max_results 上限
MAX_RESULTS_LIMIT = 50


class KeenableSearchClient:
    """Keenable 网页搜索客户端，接口文档 https://docs.keenable.ai/api-reference/search

    不配置 KEENABLE_API_KEY 时调用免 Key 公共端点 <endpoint>/public（按 IP 限流）；
    配置后调用带 X-API-Key 的正式端点，额度更高。
    """

    ENGINE_NAME = "keenable"
    ENGINE_DISPLAY_NAME = "Keenable"
    REQUIRES_API_KEY = False

    def __init__(self, api_key: Optional[str] = None, endpoint: Optional[str] = None):
        self.api_key = (api_key or os.environ.get("KEENABLE_API_KEY") or "").strip()
        base = (endpoint or os.environ.get("KEENABLE_SEARCH_ENDPOINT") or DEFAULT_ENDPOINT).rstrip("/")
        self.endpoint = base if self.api_key else f"{base}/public"
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json", "Accept": "application/json"})
        if self.api_key:
            self.session.headers["X-API-Key"] = self.api_key
        else:
            self.session.headers["X-Keenable-Title"] = APP_TITLE

    def search(
        self,
        query: str,
        max_results: Optional[int] = None,
        site: Optional[str] = None,
        published_after: Optional[str] = None,
        published_before: Optional[str] = None,
        timeout: int = 30,
    ) -> List[Dict[str, Any]]:
        if not query.strip():
            raise ValueError("搜索关键词不能为空")

        body: Dict[str, Any] = {
            "query": query.strip(),
            "max_results": MAX_RESULTS_LIMIT if max_results is None else max(1, min(max_results, MAX_RESULTS_LIMIT)),
        }
        if site:
            body["site"] = site
        if published_after:
            body["published_after"] = published_after
        if published_before:
            body["published_before"] = published_before

        response = self.session.post(self.endpoint, json=body, timeout=timeout)
        if response.status_code != 200:
            detail = response.text.strip()[:500]
            if response.status_code == 429:
                retry_after = response.headers.get("Retry-After")
                if retry_after:
                    detail += f"; Retry-After: {retry_after}"
                else:
                    detail += "; Retry-After missing; cool down for 300 seconds"
            raise RuntimeError(f"Keenable 搜索请求失败：HTTP {response.status_code} {detail}")

        payload = response.json()
        raw_results = payload.get("results")
        if not isinstance(raw_results, list):
            raise RuntimeError(f"Keenable 响应缺少 results 字段：{payload}")

        results = []
        for item in raw_results:
            url = (item.get("url") or "").strip()
            if not url:
                continue
            results.append({
                "title": (item.get("title") or url).strip(),
                "href": url,
                "body": (item.get("snippet") or item.get("description") or "").strip(),
                "engine": self.ENGINE_NAME,
                "publish_date": item.get("published_at"),
            })
        return results[:max_results] if max_results is not None else results

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
        return "\n".join(output)


def search_keenable(
    query: str,
    max_results: Optional[int] = None,
    api_key: Optional[str] = None,
    **kwargs,
) -> List[Dict[str, Any]]:
    client = KeenableSearchClient(api_key=api_key, endpoint=kwargs.pop("endpoint", None))
    return client.search(query=query, max_results=max_results, **kwargs)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Keenable 网页搜索（无需 API Key，可选 KEENABLE_API_KEY 提高额度）")
    parser.add_argument("query", help="搜索关键词")
    parser.add_argument("-m", "--max-results", type=int, default=None, help="结果数量上限，默认取接口上限 50")
    parser.add_argument("--site", help="只保留该域名的结果，如 github.com")
    parser.add_argument("--published-after", help="发布时间下限：YYYY-MM-DD 或相对时间 1d、7d、1mo、1y")
    parser.add_argument("--published-before", help="发布时间上限：YYYY-MM-DD")
    parser.add_argument("--api-key", help="Keenable API Key（可选，优先于环境变量）")
    parser.add_argument("--endpoint", help="接口地址，默认 https://api.keenable.ai/v1/search")
    parser.add_argument("--timeout", type=int, default=30, help="请求超时秒数")
    parser.add_argument("--json", action="store_true", help="JSON 输出")

    args = parser.parse_args()

    client = KeenableSearchClient(api_key=args.api_key, endpoint=args.endpoint)
    results = client.search(
        query=args.query,
        max_results=args.max_results,
        site=args.site,
        published_after=args.published_after,
        published_before=args.published_before,
        timeout=args.timeout,
    )

    if args.json:
        print(json.dumps({"results": results}, ensure_ascii=False, indent=2))
    else:
        print(client.format_results(results, args.query))
