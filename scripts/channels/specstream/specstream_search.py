import argparse
import json
import os
from typing import Any, Dict, List, Optional

import requests
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), ".env"))

DEFAULT_ENDPOINT = "https://api.specstream.ai/v1/web-search"
# 接口 num 参数范围 1 到 100
MAX_RESULTS_LIMIT = 100


class SpecStreamSearchClient:
    """SpecStream Search API 客户端，接口说明 https://api.specstream.ai/openapi.json

    使用 speed=fast：只返回搜索结果与摘要，不生成答案；news=True 时改为新闻结果。
    """

    ENGINE_NAME = "specstream"
    ENGINE_DISPLAY_NAME = "SpecStream"
    REQUIRES_API_KEY = True

    def __init__(self, api_key: Optional[str] = None, endpoint: Optional[str] = None):
        self.api_key = api_key or os.environ.get("SPECSTREAM_API_KEY")
        if not self.api_key:
            raise ValueError("SpecStream API Key 未配置，请设置 SPECSTREAM_API_KEY 环境变量")

        self.endpoint = endpoint or os.environ.get("SPECSTREAM_SEARCH_ENDPOINT") or DEFAULT_ENDPOINT
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json",
        })

    def search(
        self,
        query: str,
        max_results: Optional[int] = None,
        news: bool = False,
        language: Optional[str] = None,
        country: Optional[str] = None,
        timeout: int = 30,
    ) -> List[Dict[str, Any]]:
        if not query.strip():
            raise ValueError("搜索关键词不能为空")

        params: Dict[str, Any] = {
            "q": query.strip(),
            "num": 10 if max_results is None else max(1, min(max_results, MAX_RESULTS_LIMIT)),
        }
        if news:
            params["news"] = "true"
        else:
            params["speed"] = "fast"
        if language:
            params["language"] = language
        if country:
            params["country"] = country

        response = self.session.get(self.endpoint, params=params, timeout=timeout)
        if response.status_code != 200:
            detail = response.text.strip()[:500]
            retry_after = response.headers.get("Retry-After")
            if retry_after:
                detail += f"; Retry-After: {retry_after}"
            raise RuntimeError(f"SpecStream 搜索请求失败：HTTP {response.status_code} {detail}")

        payload = response.json()
        data = payload.get("data") if isinstance(payload, dict) else None
        raw_results = data.get("sources") if isinstance(data, dict) else None
        if not isinstance(raw_results, list):
            raise RuntimeError(f"SpecStream 响应缺少 data.sources 字段：{payload}")

        results = []
        for item in raw_results:
            url = (item.get("url") or "").strip()
            if not url:
                continue
            results.append({
                "title": (item.get("title") or url).strip(),
                "href": url,
                "body": (item.get("snippet") or "").strip(),
                "engine": self.ENGINE_NAME,
                "publish_date": item.get("published_at") or item.get("published"),
                "site": item.get("site"),
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


def search_specstream(
    query: str,
    max_results: Optional[int] = None,
    api_key: Optional[str] = None,
    **kwargs,
) -> List[Dict[str, Any]]:
    client = SpecStreamSearchClient(api_key=api_key, endpoint=kwargs.pop("endpoint", None))
    return client.search(query=query, max_results=max_results, **kwargs)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SpecStream Search API（需 SPECSTREAM_API_KEY）")
    parser.add_argument("query", help="搜索关键词，支持 site:、-site:、引号短语、filetype:、after:、before:")
    parser.add_argument("-m", "--max-results", type=int, default=None, help="结果数量上限，默认 10，最多 100")
    parser.add_argument("--news", action="store_true", help="返回新闻结果，按发布时间从新到旧")
    parser.add_argument("--language", help="两位 ISO 639-1 语言代码，如 zh、en")
    parser.add_argument("--country", help="两位 ISO 3166-1 国家代码，如 CN、US")
    parser.add_argument("--api-key", help="SpecStream API Key")
    parser.add_argument("--endpoint", help="接口地址，默认 https://api.specstream.ai/v1/web-search")
    parser.add_argument("--timeout", type=int, default=30, help="请求超时秒数")
    parser.add_argument("--json", action="store_true", help="JSON 输出")

    args = parser.parse_args()

    client = SpecStreamSearchClient(api_key=args.api_key, endpoint=args.endpoint)
    results = client.search(
        query=args.query,
        max_results=args.max_results,
        news=args.news,
        language=args.language,
        country=args.country,
        timeout=args.timeout,
    )

    if args.json:
        print(json.dumps({"results": results}, ensure_ascii=False, indent=2))
    else:
        print(client.format_results(results, args.query))
