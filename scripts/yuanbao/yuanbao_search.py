import argparse
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent.parent / ".env")

DEFAULT_ENDPOINT = "https://api.wsa.cloud.tencent.com/SearchPro"
ALLOWED_CNT = (10, 20, 30, 40, 50)
ALLOWED_INDUSTRY = ("gov", "news", "acad", "finance")


def _resolve_cnt(max_results: int) -> int:
    if max_results <= ALLOWED_CNT[0]:
        return ALLOWED_CNT[0]
    for value in ALLOWED_CNT:
        if max_results <= value:
            return value
    return ALLOWED_CNT[-1]


class YuanbaoSearchClient:
    """腾讯元宝搜索（腾讯云联网搜索 Web Search API），接口文档 https://cloud.tencent.com/document/api/1806/121811"""

    ENGINE_NAME = "yuanbao"
    ENGINE_DISPLAY_NAME = "腾讯元宝搜索"
    REQUIRES_API_KEY = True

    def __init__(self, api_key: Optional[str] = None, endpoint: Optional[str] = None):
        self.api_key = api_key or os.environ.get("TENCENTCLOUD_WSA_APIKEY")
        if not self.api_key:
            raise ValueError("腾讯元宝搜索 API Key 未配置，请设置 TENCENTCLOUD_WSA_APIKEY 环境变量")

        self.endpoint = endpoint or os.environ.get("TENCENTCLOUD_WSA_ENDPOINT") or DEFAULT_ENDPOINT
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json; charset=utf-8",
        })

    def search(
        self,
        query: str,
        max_results: int = 10,
        mode: Optional[int] = None,
        site: Optional[str] = None,
        industry: Optional[str] = None,
        freshness: Optional[str] = None,
        deeplinks: bool = False,
        timeout: int = 30,
    ) -> List[Dict[str, Any]]:
        if not query.strip():
            raise ValueError("搜索关键词不能为空")
        if mode is not None and mode not in (0, 1, 2):
            raise ValueError("Mode 只能是 0（公开网页）、1（权威垂直信源）、2（混合）")
        if industry is not None and industry not in ALLOWED_INDUSTRY:
            raise ValueError(f"Industry 只能是 {', '.join(ALLOWED_INDUSTRY)}")

        body: Dict[str, Any] = {
            "Query": query,
            "Cnt": _resolve_cnt(max_results),
        }
        if mode is not None:
            body["Mode"] = mode
        if site:
            body["Site"] = site
        if industry:
            body["Industry"] = industry
        if freshness:
            body["Freshness"] = freshness
        if deeplinks:
            body["Deeplinks"] = True

        response = self.session.post(self.endpoint, json=body, timeout=timeout)
        if response.status_code != 200:
            detail = response.text.strip()[:500]
            raise RuntimeError(f"腾讯元宝搜索请求失败：HTTP {response.status_code} {detail}")

        payload = response.json()
        result = payload.get("Response")
        if not isinstance(result, dict):
            raise RuntimeError(f"腾讯元宝搜索响应缺少 Response 字段：{payload}")
        if result.get("Error"):
            error = result["Error"]
            raise RuntimeError(f"腾讯元宝搜索返回错误：{error.get('Code')} {error.get('Message')}")

        pages = result.get("Pages")
        if not isinstance(pages, list):
            raise RuntimeError(f"腾讯元宝搜索响应缺少 Pages 字段：{payload}")

        results = []
        for raw_page in pages:
            item = json.loads(raw_page)
            url = (item.get("url") or "").strip()
            if not url:
                continue
            results.append({
                "title": (item.get("title") or url).strip(),
                "href": url,
                "body": (item.get("passage") or item.get("content") or "").strip(),
                "engine": self.ENGINE_NAME,
                "content": item.get("content", ""),
                "site": item.get("site") or "",
                "date": item.get("date"),
                "score": item.get("score"),
                "authority_level": item.get("authority_level"),
                "favicon": item.get("favicon") or "",
                "images": item.get("pics") or item.get("images") or [],
                "deeplinks": item.get("deeplinks") or [],
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
            if item.get("site"):
                output.append(f"    📰 来源：{item['site']}")
            if item.get("date"):
                output.append(f"    🕒 {item['date']}")
            if item.get("score") is not None:
                output.append(f"    ⭐ 相关度：{item['score']}")
            if item.get("authority_level") is not None:
                output.append(f"    🏛 权威度：{item['authority_level']}")
            if item.get("body"):
                body = item["body"]
                output.append(f"    📝 {body[:200]}{'...' if len(body) > 200 else ''}")
            output.append("")
        return "\n".join(output)


def search_yuanbao(
    query: str,
    max_results: int = 10,
    api_key: Optional[str] = None,
    **kwargs,
) -> List[Dict[str, Any]]:
    client = YuanbaoSearchClient(api_key=api_key)
    return client.search(query=query, max_results=max_results, **kwargs)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="腾讯元宝搜索（腾讯云联网搜索 API）")
    parser.add_argument("query", help="搜索关键词")
    parser.add_argument("-m", "--max-results", type=int, default=10, help="结果数量，接口按 10 条取整，最多 50")
    parser.add_argument("--mode", type=int, choices=[0, 1, 2], help="结果类型：0 公开网页、1 权威垂直信源、2 混合")
    parser.add_argument("--site", help="限定域名，如 zhihu.com；排除用 exclude:qq.com|sohu.com")
    parser.add_argument("--industry", choices=list(ALLOWED_INDUSTRY), help="垂直领域")
    parser.add_argument("--freshness", help="时间范围，如 d3、m1、y1、2026-01-01,2026-02-01")
    parser.add_argument("--deeplinks", action="store_true", help="返回子链接（旗舰版）")
    parser.add_argument("--api-key", help="服务 API Key")
    parser.add_argument("--endpoint", help="接口地址，默认 https://api.wsa.cloud.tencent.com/SearchPro")
    parser.add_argument("--timeout", type=int, default=30, help="请求超时秒数")
    parser.add_argument("--json", action="store_true", help="JSON 输出")

    args = parser.parse_args()

    client = YuanbaoSearchClient(api_key=args.api_key, endpoint=args.endpoint)
    results = client.search(
        query=args.query,
        max_results=args.max_results,
        mode=args.mode,
        site=args.site,
        industry=args.industry,
        freshness=args.freshness,
        deeplinks=args.deeplinks,
        timeout=args.timeout,
    )

    if args.json:
        print(json.dumps({"results": results}, ensure_ascii=False, indent=2))
    else:
        print(client.format_results(results, args.query))
