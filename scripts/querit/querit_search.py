import argparse
import json
import os
from typing import Any, Dict, List, Optional

import requests
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), ".env"))

DEFAULT_BASE_URL = "https://api.querit.ai"
DEFAULT_PATH = "/v1/search"
ALLOWED_LANGUAGES = ("english", "japanese", "korean", "german", "french", "spanish", "portuguese")
ALLOWED_COUNTRIES = (
    "argentina", "australia", "brazil", "canada", "colombia", "france", "germany",
    "india", "indonesia", "japan", "mexico", "nigeria", "philippines", "south korea",
    "spain", "united kingdom", "united states",
)


class QueritSearchClient:
    """Querit 搜索客户端，请求体与官方 SDK querit 0.1.5 一致"""

    ENGINE_NAME = "querit"
    ENGINE_DISPLAY_NAME = "Querit 搜索"
    REQUIRES_API_KEY = True

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        self.api_key = api_key or os.environ.get("QUERIT_API_KEY")
        if not self.api_key:
            raise ValueError("Querit API Key 未配置，请设置 QUERIT_API_KEY 环境变量")
        if self.api_key.lower().startswith("bearer "):
            self.api_key = self.api_key.split(None, 1)[1]

        self.base_url = (base_url or os.environ.get("QUERIT_API_BASE_URL") or DEFAULT_BASE_URL).rstrip("/")
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        })

    def search(
        self,
        query: str,
        max_results: int = 10,
        languages: Optional[List[str]] = None,
        countries: Optional[List[str]] = None,
        include_sites: Optional[List[str]] = None,
        exclude_sites: Optional[List[str]] = None,
        time_range: Optional[str] = None,
        timeout: int = 60,
    ) -> List[Dict[str, Any]]:
        if not query.strip():
            raise ValueError("搜索关键词不能为空")

        languages = languages or []
        countries = countries or []
        unknown_languages = [item for item in languages if item not in ALLOWED_LANGUAGES]
        if unknown_languages:
            raise ValueError(f"不支持的语言：{', '.join(unknown_languages)}")
        unknown_countries = [item for item in countries if item not in ALLOWED_COUNTRIES]
        if unknown_countries:
            raise ValueError(f"不支持的国家：{', '.join(unknown_countries)}")

        body: Dict[str, Any] = {"query": query, "count": max_results}
        filters: Dict[str, Any] = {}
        if languages:
            filters["languages"] = {"include": languages}
        if countries:
            filters["geo"] = {"countries": {"include": countries}}
        sites: Dict[str, List[str]] = {}
        if include_sites:
            sites["include"] = include_sites
        if exclude_sites:
            sites["exclude"] = exclude_sites
        if sites:
            filters["sites"] = sites
        if time_range:
            filters["timeRange"] = {"date": time_range}
        if filters:
            body["filters"] = filters

        response = self.session.post(f"{self.base_url}{DEFAULT_PATH}", json=body, timeout=timeout)
        if response.status_code != 200:
            detail = response.text.strip()[:500]
            raise RuntimeError(f"Querit 搜索请求失败：HTTP {response.status_code} {detail}")

        payload = response.json()
        error_code = payload.get("error_code")
        if error_code:
            raise RuntimeError(f"Querit 搜索返回错误：{error_code} {payload.get('error_msg')}")

        result_block = payload.get("results") or {}
        raw_results = result_block.get("result") if isinstance(result_block, dict) else None
        if not isinstance(raw_results, list):
            raise RuntimeError(f"Querit 响应缺少 results.result 字段：{payload}")

        results = []
        for item in raw_results[:max_results]:
            url = (item.get("url") or "").strip()
            if not url:
                continue
            results.append({
                "title": (item.get("title") or url).strip(),
                "href": url,
                "body": (item.get("snippet") or "").strip(),
                "engine": self.ENGINE_NAME,
                "page_time": item.get("page_time"),
                "page_age": item.get("page_age"),
                "language": item.get("language"),
                "site_auth_level": item.get("site_auth_level"),
                "search_id": payload.get("search_id"),
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
            if item.get("page_age"):
                output.append(f"    📅 {item['page_age']}")
            if item.get("body"):
                body = item["body"]
                output.append(f"    📝 {body[:200]}{'...' if len(body) > 200 else ''}")
            output.append("")
        return "\n".join(output)


def search_querit(
    query: str,
    max_results: int = 10,
    api_key: Optional[str] = None,
    **kwargs,
) -> List[Dict[str, Any]]:
    client = QueritSearchClient(api_key=api_key)
    return client.search(query=query, max_results=max_results, **kwargs)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Querit Search API")
    parser.add_argument("query", help="搜索关键词")
    parser.add_argument("-m", "--max-results", type=int, default=10, help="结果数量")
    parser.add_argument("--language", action="append", dest="languages", help="语言，可重复传入，如 english")
    parser.add_argument("--country", action="append", dest="countries", help="国家，可重复传入，如 united states")
    parser.add_argument("--include-site", action="append", dest="include_sites", help="只保留这些站点，可重复传入")
    parser.add_argument("--exclude-site", action="append", dest="exclude_sites", help="排除这些站点，可重复传入")
    parser.add_argument("--time-range", help="时间范围，如 d1")
    parser.add_argument("--api-key", help="Querit API Key")
    parser.add_argument("--base-url", help="接口根地址，默认 https://api.querit.ai")
    parser.add_argument("--timeout", type=int, default=60, help="请求超时秒数")
    parser.add_argument("--json", action="store_true", help="JSON 输出")

    args = parser.parse_args()

    client = QueritSearchClient(api_key=args.api_key, base_url=args.base_url)
    results = client.search(
        query=args.query,
        max_results=args.max_results,
        languages=args.languages,
        countries=args.countries,
        include_sites=args.include_sites,
        exclude_sites=args.exclude_sites,
        time_range=args.time_range,
        timeout=args.timeout,
    )

    if args.json:
        print(json.dumps({"results": results}, ensure_ascii=False, indent=2))
    else:
        print(client.format_results(results, args.query))
