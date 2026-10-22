import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent.parent / ".env")

DEFAULT_API_URL = "https://api.firecrawl.dev"


class FirecrawlSearchClient:
    """Firecrawl 搜索客户端，接口文档 https://docs.firecrawl.dev/features/search"""

    ENGINE_NAME = "firecrawl"
    ENGINE_DISPLAY_NAME = "Firecrawl 搜索"
    REQUIRES_API_KEY = True

    def __init__(self, api_key: Optional[str] = None, api_url: Optional[str] = None):
        self.api_key = api_key or os.environ.get("FIRECRAWL_API_KEY")
        if not self.api_key:
            raise ValueError("Firecrawl API Key 未配置，请设置 FIRECRAWL_API_KEY 环境变量")

        self.api_url = (api_url or os.environ.get("FIRECRAWL_API_URL") or DEFAULT_API_URL).rstrip("/")
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        })

    def search(
        self,
        query: str,
        max_results: int = 10,
        sources: Optional[List[str]] = None,
        categories: Optional[List[str]] = None,
        include_domains: Optional[List[str]] = None,
        exclude_domains: Optional[List[str]] = None,
        tbs: Optional[str] = None,
        location: Optional[str] = None,
        country: Optional[str] = None,
        scrape: bool = False,
        formats: Optional[List[str]] = None,
        timeout: int = 60,
    ) -> List[Dict[str, Any]]:
        if not query.strip():
            raise ValueError("搜索关键词不能为空")

        body: Dict[str, Any] = {
            "query": query,
            "limit": max_results,
            "sources": sources or ["web"],
        }
        if categories:
            body["categories"] = categories
        if include_domains:
            body["includeDomains"] = include_domains
        if exclude_domains:
            body["excludeDomains"] = exclude_domains
        if tbs:
            body["tbs"] = tbs
        if location:
            body["location"] = location
        if country:
            body["country"] = country
        if scrape:
            body["scrapeOptions"] = {"formats": formats or ["markdown"]}

        response = self.session.post(
            f"{self.api_url}/v2/search",
            json=body,
            timeout=timeout,
        )
        if response.status_code != 200:
            detail = response.text.strip()[:500]
            raise RuntimeError(f"Firecrawl 搜索请求失败：HTTP {response.status_code} {detail}")

        data = response.json()
        if data.get("success") is False:
            raise RuntimeError(f"Firecrawl 搜索返回失败：{data.get('error') or data}")

        return self._normalize(data.get("data"), max_results)

    def _normalize(self, payload: Any, max_results: int) -> List[Dict[str, Any]]:
        if isinstance(payload, dict):
            web_items = payload.get("web") or []
            news_items = payload.get("news") or []
            image_items = payload.get("images") or []
        elif isinstance(payload, list):
            # v1 接口直接返回结果数组
            web_items, news_items, image_items = payload, [], []
        else:
            raise RuntimeError(f"Firecrawl 响应缺少 data 字段：{payload}")

        results: List[Dict[str, Any]] = []

        for idx, item in enumerate(web_items, 1):
            metadata = item.get("metadata") or {}
            title = (item.get("title") or metadata.get("title") or "").strip()
            url = (item.get("url") or metadata.get("sourceURL") or "").strip()
            body = (item.get("description") or metadata.get("description") or "").strip()
            if not url:
                continue
            record = {
                "title": title or url,
                "href": url,
                "body": body,
                "engine": self.ENGINE_NAME,
                "source_type": "web",
                "position": item.get("position") or idx,
            }
            if item.get("category"):
                record["category"] = item["category"]
            if item.get("markdown"):
                record["markdown"] = item["markdown"]
            if metadata:
                record["metadata"] = metadata
            results.append(record)

        for idx, item in enumerate(news_items, 1):
            url = (item.get("url") or "").strip()
            if not url:
                continue
            results.append({
                "title": (item.get("title") or url).strip(),
                "href": url,
                "body": (item.get("snippet") or item.get("description") or "").strip(),
                "engine": self.ENGINE_NAME,
                "source_type": "news",
                "date": item.get("date"),
                "image": item.get("imageUrl"),
                "position": item.get("position") or idx,
            })

        for idx, item in enumerate(image_items, 1):
            image_url = (item.get("imageUrl") or "").strip()
            page_url = (item.get("url") or "").strip()
            if not image_url:
                continue
            results.append({
                "title": (item.get("title") or image_url).strip(),
                "href": image_url,
                "body": page_url,
                "engine": self.ENGINE_NAME,
                "source_type": "image",
                "page_url": page_url,
                "width": item.get("imageWidth"),
                "height": item.get("imageHeight"),
                "position": item.get("position") or idx,
            })

        return results[:max_results]

    def format_results(self, results: List[Dict[str, Any]], query: str) -> str:
        output = [
            f"🔍 {self.ENGINE_DISPLAY_NAME}: {query}",
            f"📊 找到 {len(results)} 条结果",
            "",
        ]
        for i, item in enumerate(results, 1):
            output.append(f"[{i}] {item.get('title', '')}")
            output.append(f"    🔗 {item.get('href', '')}")
            if item.get("date"):
                output.append(f"    🕒 {item['date']}")
            if item.get("body"):
                body = item["body"]
                output.append(f"    📝 {body[:200]}{'...' if len(body) > 200 else ''}")
            output.append("")
        return "\n".join(output)


def search_firecrawl(
    query: str,
    max_results: int = 10,
    api_key: Optional[str] = None,
    **kwargs,
) -> List[Dict[str, Any]]:
    client = FirecrawlSearchClient(api_key=api_key)
    return client.search(query=query, max_results=max_results, **kwargs)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Firecrawl 搜索 API")
    parser.add_argument("query", help="搜索关键词")
    parser.add_argument("-m", "--max-results", type=int, default=10, help="结果数量")
    parser.add_argument("--sources", nargs="+", default=["web"], choices=["web", "news", "images"], help="结果来源")
    parser.add_argument("--categories", nargs="+", help="结果分类：research pdf developer gov")
    parser.add_argument("--include-domains", nargs="+", help="限定域名")
    parser.add_argument("--exclude-domains", nargs="+", help="排除域名")
    parser.add_argument("--tbs", help="时间过滤，如 qdr:d、qdr:w、sbd:1")
    parser.add_argument("--location", help="地理定位，如 Germany")
    parser.add_argument("--country", help="国家代码，如 CN、US")
    parser.add_argument("--scrape", action="store_true", help="同时抓取网页正文")
    parser.add_argument("--formats", nargs="+", default=["markdown"], help="抓取格式")
    parser.add_argument("--api-key", help="Firecrawl API Key")
    parser.add_argument("--api-url", help="Firecrawl API 地址，默认 https://api.firecrawl.dev")
    parser.add_argument("--timeout", type=int, default=60, help="请求超时秒数")
    parser.add_argument("--json", action="store_true", help="JSON 输出")

    args = parser.parse_args()

    client = FirecrawlSearchClient(api_key=args.api_key, api_url=args.api_url)
    results = client.search(
        query=args.query,
        max_results=args.max_results,
        sources=args.sources,
        categories=args.categories,
        include_domains=args.include_domains,
        exclude_domains=args.exclude_domains,
        tbs=args.tbs,
        location=args.location,
        country=args.country,
        scrape=args.scrape,
        formats=args.formats,
        timeout=args.timeout,
    )

    if args.json:
        print(json.dumps({"results": results}, ensure_ascii=False, indent=2))
    else:
        print(client.format_results(results, args.query))
