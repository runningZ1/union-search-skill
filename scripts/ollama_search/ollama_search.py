import argparse
import json
import os
from typing import Any, Dict, List, Optional

import requests
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), ".env"))

DEFAULT_ENDPOINT = "https://ollama.com/api/web_search"
MAX_RESULTS = 10


class OllamaSearchClient:
    """Ollama Web Search 客户端，接口文档 https://docs.ollama.com/capabilities/web-search"""

    ENGINE_NAME = "ollama"
    ENGINE_DISPLAY_NAME = "Ollama Web Search"
    REQUIRES_API_KEY = True

    def __init__(self, api_key: Optional[str] = None, endpoint: Optional[str] = None):
        self.api_key = api_key or os.environ.get("OLLAMA_API_KEY")
        if not self.api_key:
            raise ValueError("Ollama API Key 未配置，请设置 OLLAMA_API_KEY 环境变量")
        if self.api_key.lower().startswith("bearer "):
            self.api_key = self.api_key.split(None, 1)[1]

        self.endpoint = endpoint or os.environ.get("OLLAMA_WEB_SEARCH_ENDPOINT") or DEFAULT_ENDPOINT
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        })

    def search(
        self,
        query: str,
        max_results: int = 5,
        timeout: int = 30,
    ) -> List[Dict[str, Any]]:
        if not query.strip():
            raise ValueError("搜索关键词不能为空")

        limit = max(1, min(max_results, MAX_RESULTS))
        response = self.session.post(
            self.endpoint,
            json={"query": query, "max_results": limit},
            timeout=timeout,
        )
        if response.status_code != 200:
            detail = response.text.strip()[:500]
            raise RuntimeError(f"Ollama 搜索请求失败：HTTP {response.status_code} {detail}")

        payload = response.json()
        raw_results = payload.get("results")
        if not isinstance(raw_results, list):
            raise RuntimeError(f"Ollama 响应缺少 results 字段：{payload}")

        results = []
        for item in raw_results[:limit]:
            url = (item.get("url") or "").strip()
            if not url:
                continue
            results.append({
                "title": (item.get("title") or url).strip(),
                "href": url,
                "body": (item.get("content") or "").strip(),
                "engine": self.ENGINE_NAME,
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
            if item.get("body"):
                body = item["body"]
                output.append(f"    📝 {body[:200]}{'...' if len(body) > 200 else ''}")
            output.append("")
        return "\n".join(output)


def search_ollama(
    query: str,
    max_results: int = 5,
    api_key: Optional[str] = None,
    **kwargs,
) -> List[Dict[str, Any]]:
    client = OllamaSearchClient(api_key=api_key)
    return client.search(query=query, max_results=max_results, **kwargs)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ollama Web Search API")
    parser.add_argument("query", help="搜索关键词")
    parser.add_argument("-m", "--max-results", type=int, default=5, help="结果数量，1-10，默认 5")
    parser.add_argument("--api-key", help="Ollama API Key")
    parser.add_argument("--endpoint", help="接口地址，默认 https://ollama.com/api/web_search")
    parser.add_argument("--timeout", type=int, default=30, help="请求超时秒数")
    parser.add_argument("--json", action="store_true", help="JSON 输出")

    args = parser.parse_args()

    client = OllamaSearchClient(api_key=args.api_key, endpoint=args.endpoint)
    results = client.search(
        query=args.query,
        max_results=args.max_results,
        timeout=args.timeout,
    )

    if args.json:
        print(json.dumps({"results": results}, ensure_ascii=False, indent=2))
    else:
        print(client.format_results(results, args.query))
