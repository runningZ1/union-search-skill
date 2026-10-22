import argparse
import json
import os
from typing import Any, Dict, List, Optional

import requests
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), ".env"))

DEFAULT_BASE_URL = "https://api.cloudflare.com/client/v4"
DEFAULT_GATEWAY_ID = "default"
DEFAULT_PROVIDER = "ceramic"
ALLOWED_PROVIDERS = ("ceramic", "exa", "linkup")
MAX_LIMIT = 10


class CloudflareSearchClient:
    """Cloudflare Web Search 客户端，接口文档 https://developers.cloudflare.com/web-search/how-to-use/"""

    ENGINE_NAME = "cloudflare"
    ENGINE_DISPLAY_NAME = "Cloudflare Web Search"
    REQUIRES_API_KEY = True

    def __init__(
        self,
        api_token: Optional[str] = None,
        account_id: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        self.api_token = api_token or os.environ.get("CLOUDFLARE_API_TOKEN")
        if not self.api_token:
            raise ValueError("Cloudflare API Token 未配置，请设置 CLOUDFLARE_API_TOKEN 环境变量")

        self.account_id = account_id or os.environ.get("CLOUDFLARE_ACCOUNT_ID")
        if not self.account_id:
            raise ValueError("Cloudflare Account ID 未配置，请设置 CLOUDFLARE_ACCOUNT_ID 环境变量")

        self.base_url = (base_url or os.environ.get("CLOUDFLARE_API_BASE_URL") or DEFAULT_BASE_URL).rstrip("/")
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json",
        })

    def search(
        self,
        query: str,
        max_results: int = 10,
        provider: Optional[str] = None,
        gateway_id: Optional[str] = None,
        byok_alias: Optional[str] = None,
        timeout: int = 30,
    ) -> List[Dict[str, Any]]:
        if not query.strip():
            raise ValueError("搜索关键词不能为空")
        if len(query) > 1024:
            raise ValueError("搜索关键词最长 1024 个字符")

        provider = provider or os.environ.get("CLOUDFLARE_WEBSEARCH_PROVIDER") or DEFAULT_PROVIDER
        if provider not in ALLOWED_PROVIDERS:
            raise ValueError(f"provider 只能是 {', '.join(ALLOWED_PROVIDERS)}")

        limit = max(1, min(max_results, MAX_LIMIT))
        gateway_id = gateway_id or os.environ.get("CLOUDFLARE_GATEWAY_ID") or DEFAULT_GATEWAY_ID
        byok_alias = byok_alias or os.environ.get("CLOUDFLARE_BYOK_ALIAS")

        body: Dict[str, Any] = {
            "query": query,
            "provider": provider,
            "limit": limit,
            "options": {"gateway": {"id": gateway_id}},
        }
        if byok_alias:
            body["byokAlias"] = byok_alias

        url = f"{self.base_url}/accounts/{self.account_id}/ai/websearch/"
        response = self.session.post(url, json=body, timeout=timeout)
        if response.status_code != 200:
            detail = response.text.strip()[:500]
            raise RuntimeError(f"Cloudflare 搜索请求失败：HTTP {response.status_code} {detail}")

        payload = response.json()
        raw_results = payload.get("items")
        if not isinstance(raw_results, list):
            raise RuntimeError(f"Cloudflare 响应缺少 items 字段：{payload}")

        metadata = payload.get("metadata") or {}
        results = []
        for item in raw_results[:limit]:
            href = (item.get("url") or "").strip()
            if not href:
                continue
            results.append({
                "title": (item.get("title") or href).strip(),
                "href": href,
                "body": (item.get("description") or "").strip(),
                "engine": self.ENGINE_NAME,
                "provider": provider,
                "request_id": metadata.get("requestId"),
                "latency_ms": metadata.get("latencyMs"),
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


def search_cloudflare(
    query: str,
    max_results: int = 10,
    api_token: Optional[str] = None,
    **kwargs,
) -> List[Dict[str, Any]]:
    client = CloudflareSearchClient(api_token=api_token)
    return client.search(query=query, max_results=max_results, **kwargs)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Cloudflare Web Search API")
    parser.add_argument("query", help="搜索关键词，最长 1024 字符")
    parser.add_argument("-m", "--max-results", type=int, default=10, help="结果数量，1-10")
    parser.add_argument("--provider", choices=ALLOWED_PROVIDERS, help="搜索提供商，默认 ceramic")
    parser.add_argument("--gateway-id", help="AI Gateway ID，默认 default")
    parser.add_argument("--byok-alias", help="网关上已保存的提供商密钥别名")
    parser.add_argument("--api-token", help="Cloudflare API Token")
    parser.add_argument("--account-id", help="Cloudflare Account ID")
    parser.add_argument("--base-url", help="接口根地址，默认 https://api.cloudflare.com/client/v4")
    parser.add_argument("--timeout", type=int, default=30, help="请求超时秒数")
    parser.add_argument("--json", action="store_true", help="JSON 输出")

    args = parser.parse_args()

    client = CloudflareSearchClient(
        api_token=args.api_token,
        account_id=args.account_id,
        base_url=args.base_url,
    )
    results = client.search(
        query=args.query,
        max_results=args.max_results,
        provider=args.provider,
        gateway_id=args.gateway_id,
        byok_alias=args.byok_alias,
        timeout=args.timeout,
    )

    if args.json:
        print(json.dumps({"results": results}, ensure_ascii=False, indent=2))
    else:
        print(client.format_results(results, args.query))
