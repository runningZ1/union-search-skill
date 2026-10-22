import argparse
import json
import os
from typing import Any, Dict, List, Optional

import requests
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), ".env"))

DEFAULT_ENDPOINT = "https://api.anysearch.com/v1/search"
ALLOWED_FRESHNESS = ("day", "week", "month", "year")
ALLOWED_ZONES = ("cn", "intl")


class AnySearchClient:
    """AnySearch 搜索客户端，接口文档 https://anysearch.com/docs"""

    ENGINE_NAME = "anysearch"
    ENGINE_DISPLAY_NAME = "AnySearch 实时搜索"
    REQUIRES_API_KEY = False

    def __init__(self, api_key: Optional[str] = None, endpoint: Optional[str] = None):
        # 未配置密钥时走匿名访问，速率限制更低
        self.api_key = api_key or os.environ.get("ANYSEARCH_API_KEY")
        self.endpoint = endpoint or os.environ.get("ANYSEARCH_ENDPOINT") or DEFAULT_ENDPOINT
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        if self.api_key:
            self.session.headers.update({"Authorization": f"Bearer {self.api_key}"})

    def search(
        self,
        query: str,
        max_results: Optional[int] = None,
        domains: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        content_types: Optional[List[str]] = None,
        zone: Optional[str] = None,
        freshness: Optional[str] = None,
        timeout: int = 30,
    ) -> List[Dict[str, Any]]:
        if not query.strip():
            raise ValueError("搜索关键词不能为空")
        if zone and zone not in ALLOWED_ZONES:
            raise ValueError(f"zone 只能是 {', '.join(ALLOWED_ZONES)}")
        if freshness and freshness not in ALLOWED_FRESHNESS:
            raise ValueError(f"freshness 只能是 {', '.join(ALLOWED_FRESHNESS)}")

        body: Dict[str, Any] = {"query": query, "max_results": 10 if max_results is None else max_results}
        if domains:
            body["domains"] = domains
        if tags:
            body["tags"] = tags
        if content_types:
            body["content_types"] = content_types
        if zone:
            body["zone"] = zone
        if freshness:
            body["constraint"] = {"freshness": freshness}

        response = self.session.post(self.endpoint, json=body, timeout=timeout)
        if response.status_code != 200:
            detail = response.text.strip()[:500]
            raise RuntimeError(f"AnySearch 搜索请求失败：HTTP {response.status_code} {detail}")

        payload = response.json()
        if payload.get("code") != 0:
            raise RuntimeError(f"AnySearch 搜索返回错误：{payload.get('code')} {payload.get('message')}")

        data = payload.get("data") or {}
        raw_results = data.get("results")
        if not isinstance(raw_results, list):
            raise RuntimeError(f"AnySearch 响应缺少 results 字段：{payload}")

        metadata = data.get("metadata") or {}
        results = []
        for item in raw_results[:max_results]:
            url = (item.get("url") or "").strip()
            if not url:
                continue
            snippet = (item.get("snippet") or "").strip()
            content = (item.get("content") or "").strip()
            results.append({
                "title": (item.get("title") or url).strip(),
                "href": url,
                "body": snippet or content[:300],
                "engine": self.ENGINE_NAME,
                "content": content,
                "score": item.get("score"),
                "quality_score": item.get("quality_score"),
                "source": item.get("source") or "",
                "published_at": item.get("published_at") or "",
                "total_results": metadata.get("total_results"),
                "search_time_ms": metadata.get("search_time_ms"),
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
            if item.get("source"):
                output.append(f"    📰 来源：{item['source']}")
            if item.get("published_at"):
                output.append(f"    🕒 {item['published_at']}")
            if item.get("body"):
                body = item["body"]
                output.append(f"    📝 {body[:200]}{'...' if len(body) > 200 else ''}")
            output.append("")
        return "\n".join(output)


def search_anysearch(
    query: str,
    max_results: Optional[int] = None,
    api_key: Optional[str] = None,
    **kwargs,
) -> List[Dict[str, Any]]:
    client = AnySearchClient(api_key=api_key)
    return client.search(query=query, max_results=max_results, **kwargs)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AnySearch 实时搜索 API")
    parser.add_argument("query", help="搜索关键词；垂直搜索按 list_domains 返回的 query_format 填写")
    parser.add_argument("-m", "--max-results", type=int, default=None, help="结果数量")
    parser.add_argument("--domains", nargs="+", help="限定域名或领域，如 finance、academic")
    parser.add_argument("--tags", nargs="+", help="子领域标签，如 finance.us_stock")
    parser.add_argument("--content-types", nargs="+", help="内容类型，如 web news code doc academic data image video audio")
    parser.add_argument("--zone", choices=list(ALLOWED_ZONES), help="区域：cn 中国、intl 国际")
    parser.add_argument("--freshness", choices=list(ALLOWED_FRESHNESS), help="时间范围")
    parser.add_argument("--api-key", help="AnySearch API Key，缺省时匿名访问")
    parser.add_argument("--endpoint", help="接口地址，默认 https://api.anysearch.com/v1/search")
    parser.add_argument("--timeout", type=int, default=30, help="请求超时秒数")
    parser.add_argument("--json", action="store_true", help="JSON 输出")

    args = parser.parse_args()

    client = AnySearchClient(api_key=args.api_key, endpoint=args.endpoint)
    results = client.search(
        query=args.query,
        max_results=args.max_results,
        domains=args.domains,
        tags=args.tags,
        content_types=args.content_types,
        zone=args.zone,
        freshness=args.freshness,
        timeout=args.timeout,
    )

    if args.json:
        print(json.dumps({"results": results}, ensure_ascii=False, indent=2))
    else:
        print(client.format_results(results, args.query))
