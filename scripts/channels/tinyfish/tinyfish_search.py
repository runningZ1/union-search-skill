import argparse
import json
import os
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import requests
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), ".env"))

DEFAULT_ENDPOINT = "https://api.search.tinyfish.ai"


class TinyFishSearchClient:
    """TinyFish 搜索客户端，接口文档 https://www.tinyfish.ai/search"""

    ENGINE_NAME = "tinyfish"
    ENGINE_DISPLAY_NAME = "TinyFish 搜索"
    REQUIRES_API_KEY = True

    def __init__(self, api_key: Optional[str] = None, endpoint: Optional[str] = None):
        self.api_key = api_key or os.environ.get("TINYFISH_API_KEY")
        if not self.api_key:
            raise ValueError("TinyFish API Key 未配置，请设置 TINYFISH_API_KEY 环境变量")

        self.endpoint = (endpoint or os.environ.get("TINYFISH_SEARCH_ENDPOINT") or DEFAULT_ENDPOINT).rstrip("/")
        self.session = requests.Session()
        self.session.headers.update({"X-API-Key": self.api_key})

    def search(
        self,
        query: str,
        max_results: Optional[int] = None,
        location: Optional[str] = None,
        language: Optional[str] = None,
        timeout: int = 15,
    ) -> List[Dict[str, Any]]:
        if not query.strip():
            raise ValueError("搜索关键词不能为空")

        params: Dict[str, str] = {"query": query}
        if location:
            params["location"] = location
        if language:
            params["language"] = language

        response = self.session.get(self.endpoint, params=params, timeout=timeout)
        if response.status_code != 200:
            detail = response.text.strip()[:500]
            raise RuntimeError(f"TinyFish 搜索请求失败：HTTP {response.status_code} {detail}")

        payload = response.json()
        raw_results = payload.get("results")
        if not isinstance(raw_results, list):
            raise RuntimeError(f"TinyFish 响应缺少 results 字段：{payload}")

        results = []
        for idx, item in enumerate(raw_results[:max_results], 1):
            url = (item.get("url") or "").strip()
            if url and not urlparse(url).scheme:
                url = f"https://{url}"
            if not url:
                continue
            results.append({
                "title": (item.get("title") or url).strip(),
                "href": url,
                "body": (item.get("snippet") or "").strip(),
                "engine": self.ENGINE_NAME,
                "site_name": item.get("site_name") or "",
                "position": item.get("position") or idx,
                "total_results": payload.get("total_results"),
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
            if item.get("body"):
                body = item["body"]
                output.append(f"    📝 {body[:200]}{'...' if len(body) > 200 else ''}")
            output.append("")
        return "\n".join(output)


def search_tinyfish(
    query: str,
    max_results: Optional[int] = None,
    api_key: Optional[str] = None,
    **kwargs,
) -> List[Dict[str, Any]]:
    client = TinyFishSearchClient(api_key=api_key)
    return client.search(query=query, max_results=max_results, **kwargs)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="TinyFish 搜索 API")
    parser.add_argument("query", help="搜索关键词")
    parser.add_argument("-m", "--max-results", type=int, default=None, help="结果数量")
    parser.add_argument("--location", help="两位国家代码，如 US、CN")
    parser.add_argument("--language", help="语言代码，如 en、zh")
    parser.add_argument("--api-key", help="TinyFish API Key")
    parser.add_argument("--endpoint", help="接口地址，默认 https://api.search.tinyfish.ai")
    parser.add_argument("--timeout", type=int, default=15, help="请求超时秒数")
    parser.add_argument("--json", action="store_true", help="JSON 输出")

    args = parser.parse_args()

    client = TinyFishSearchClient(api_key=args.api_key, endpoint=args.endpoint)
    results = client.search(
        query=args.query,
        max_results=args.max_results,
        location=args.location,
        language=args.language,
        timeout=args.timeout,
    )

    if args.json:
        print(json.dumps({"results": results}, ensure_ascii=False, indent=2))
    else:
        print(client.format_results(results, args.query))
