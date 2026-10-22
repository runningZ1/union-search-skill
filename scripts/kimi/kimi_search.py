import argparse
import json
import os
from typing import Any, Dict, List, Optional

import requests
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), ".env"))

DEFAULT_BASE_URL = "https://api.moonshot.cn/v1"
DEFAULT_TIER = "search"
ALLOWED_TIERS = ("search", "search_pro")
MAX_LIMIT = 20
MAX_SITES = 5


class KimiSearchClient:
    """Kimi 独立搜索客户端，接口文档 https://platform.kimi.com/docs/guide/best-practices-for-web-search"""

    ENGINE_NAME = "kimi"
    ENGINE_DISPLAY_NAME = "Kimi 搜索"
    REQUIRES_API_KEY = True

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        self.api_key = api_key or os.environ.get("MOONSHOT_API_KEY")
        if not self.api_key:
            raise ValueError("Kimi API Key 未配置，请设置 MOONSHOT_API_KEY 环境变量")
        if self.api_key.lower().startswith("bearer "):
            self.api_key = self.api_key.split(None, 1)[1]

        self.base_url = (base_url or os.environ.get("MOONSHOT_API_BASE_URL") or DEFAULT_BASE_URL).rstrip("/")
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        })

    def search(
        self,
        query: str,
        max_results: int = 5,
        tier: Optional[str] = None,
        include_content: bool = False,
        sites: Optional[List[str]] = None,
        start: Optional[str] = None,
        end: Optional[str] = None,
        timeout: int = 30,
    ) -> List[Dict[str, Any]]:
        text = query.strip()
        if not text:
            raise ValueError("搜索关键词不能为空")

        tier = tier or os.environ.get("KIMI_SEARCH_TIER") or DEFAULT_TIER
        if tier not in ALLOWED_TIERS:
            raise ValueError(f"tier 只能是 {', '.join(ALLOWED_TIERS)}")

        limit = max(1, min(max_results, MAX_LIMIT))
        body: Dict[str, Any] = {"text_query": text, "limit": limit, "timeout_seconds": timeout}
        if tier == "search":
            body["include_content"] = include_content
        if sites:
            if len(sites) > MAX_SITES:
                raise ValueError(f"sites 最多 {MAX_SITES} 个")
            body["sites"] = sites
        if start or end:
            window: Dict[str, str] = {}
            if start:
                window["start"] = start
            if end:
                window["end"] = end
            body["time_window"] = window

        response = self.session.post(f"{self.base_url}/tools/{tier}", json=body, timeout=timeout + 5)
        if response.status_code != 200:
            detail = response.text.strip()[:500]
            raise RuntimeError(f"Kimi 搜索请求失败：HTTP {response.status_code} {detail}")

        payload = response.json()
        raw_results = payload.get("search_results")
        if not isinstance(raw_results, list):
            raise RuntimeError(f"Kimi 响应缺少 search_results 字段：{payload}")

        results = []
        for item in raw_results[:limit]:
            url = (item.get("url") or "").strip()
            if not url:
                continue
            chunks = item.get("chunks") or []
            chunk_text = "\n".join(
                chunk.get("text", "").strip()
                for chunk in chunks
                if isinstance(chunk, dict) and chunk.get("text")
            )
            body_text = chunk_text or (item.get("content") or item.get("snippet") or "").strip()
            results.append({
                "title": (item.get("title") or url).strip(),
                "href": url,
                "body": body_text,
                "engine": self.ENGINE_NAME,
                "site_name": item.get("site_name") or "",
                "publish_date": item.get("date") or "",
                "tier": tier,
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
            if item.get("site_name"):
                output.append(f"    📰 来源：{item['site_name']}")
            if item.get("publish_date"):
                output.append(f"    📅 {item['publish_date']}")
            if item.get("body"):
                body = item["body"]
                output.append(f"    📝 {body[:200]}{'...' if len(body) > 200 else ''}")
            output.append("")
        return "\n".join(output)


def search_kimi(
    query: str,
    max_results: int = 5,
    api_key: Optional[str] = None,
    **kwargs,
) -> List[Dict[str, Any]]:
    client = KimiSearchClient(api_key=api_key)
    return client.search(query=query, max_results=max_results, **kwargs)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Kimi 独立搜索 API")
    parser.add_argument("query", help="搜索关键词，按原文检索")
    parser.add_argument("-m", "--max-results", type=int, default=5, help="结果数量，1-20")
    parser.add_argument("--tier", choices=ALLOWED_TIERS, help="search 基础搜索，search_pro 专业搜索")
    parser.add_argument("--include-content", action="store_true", help="基础搜索附带页面正文")
    parser.add_argument("--site", action="append", dest="sites", help="限定站点，最多 5 个，可重复传入")
    parser.add_argument("--start", help="时间窗口起点，年、年月或日期")
    parser.add_argument("--end", help="时间窗口终点，年、年月或日期")
    parser.add_argument("--api-key", help="Kimi API Key")
    parser.add_argument("--base-url", help="接口根地址，默认 https://api.moonshot.cn/v1")
    parser.add_argument("--timeout", type=int, default=30, help="服务端超时秒数，1-60")
    parser.add_argument("--json", action="store_true", help="JSON 输出")

    args = parser.parse_args()

    client = KimiSearchClient(api_key=args.api_key, base_url=args.base_url)
    results = client.search(
        query=args.query,
        max_results=args.max_results,
        tier=args.tier,
        include_content=args.include_content,
        sites=args.sites,
        start=args.start,
        end=args.end,
        timeout=args.timeout,
    )

    if args.json:
        print(json.dumps({"results": results}, ensure_ascii=False, indent=2))
    else:
        print(client.format_results(results, args.query))
