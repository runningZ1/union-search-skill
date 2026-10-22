import argparse
import json
import os
import time
from typing import Any, Dict, List, Optional

import requests
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), ".env"))

DEFAULT_BASE_URL = "https://developer.zhihu.com"
ENDPOINTS = {
    "search": "/api/v1/content/zhihu_search",
    "global": "/api/v1/content/global_search",
    "hot": "/api/v1/content/hot_list",
}
COUNT_LIMITS = {"search": 10, "global": 20, "hot": 30}
ASK_MODELS = ("zhida-fast-1p5", "zhida-thinking-1p5", "zhida-agent")


class ZhihuOfficialSearchClient:
    """知乎开放平台客户端，接口文档 https://developer.zhihu.com/docs"""

    ENGINE_NAME = "zhihu_official"
    ENGINE_DISPLAY_NAME = "知乎开放平台搜索"
    REQUIRES_API_KEY = True

    def __init__(self, access_secret: Optional[str] = None, base_url: Optional[str] = None):
        self.access_secret = access_secret or os.environ.get("ZHIHU_ACCESS_SECRET")
        if not self.access_secret:
            raise ValueError("知乎 Access Secret 未配置，请设置 ZHIHU_ACCESS_SECRET 环境变量")

        self.base_url = (base_url or os.environ.get("ZHIHU_OPENAPI_BASE_URL") or DEFAULT_BASE_URL).rstrip("/")
        self.session = requests.Session()

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.access_secret}",
            "X-Request-Timestamp": str(int(time.time())),
        }

    def _get(self, scope: str, params: Dict[str, str], timeout: int) -> Dict[str, Any]:
        response = self.session.get(
            f"{self.base_url}{ENDPOINTS[scope]}",
            params=params,
            headers=self._headers(),
            timeout=timeout,
        )
        if response.status_code != 200:
            detail = response.text.strip()[:500]
            raise RuntimeError(f"知乎接口请求失败：HTTP {response.status_code} {detail}")

        payload = response.json()
        if payload.get("Code") != 0:
            raise RuntimeError(f"知乎接口返回错误：{payload.get('Code')} {payload.get('Message')}")
        return payload

    def search(
        self,
        query: str,
        max_results: int = 10,
        scope: str = "search",
        timeout: int = 10,
    ) -> List[Dict[str, Any]]:
        if not query.strip():
            raise ValueError("搜索关键词不能为空")
        if scope not in ("search", "global"):
            raise ValueError("scope 只能是 search 或 global")

        count = max(1, min(COUNT_LIMITS[scope], max_results))
        payload = self._get(scope, {"Query": query.strip(), "Count": str(count)}, timeout)
        items = ((payload.get("Data") or {}).get("Items")) or []

        results = []
        for item in items:
            url = (item.get("Url") or "").strip()
            if not url:
                continue
            record = {
                "title": (item.get("Title") or url).strip(),
                "href": url,
                "body": (item.get("ContentText") or "").strip(),
                "engine": self.ENGINE_NAME,
                "author_name": item.get("AuthorName") or "",
                "edit_time": item.get("EditTime"),
            }
            if scope == "search":
                record["vote_up_count"] = item.get("VoteUpCount", 0)
                record["comment_count"] = item.get("CommentCount", 0)
            else:
                record["scope"] = "global"
            results.append(record)
        return results

    def hot_list(self, limit: int = 30, timeout: int = 10) -> Dict[str, Any]:
        count = max(1, min(COUNT_LIMITS["hot"], limit))
        payload = self._get("hot", {"Limit": str(count)}, timeout)
        data = payload.get("Data") or {}
        items = data.get("Items") or []

        results = []
        for item in items:
            url = (item.get("Url") or "").strip()
            if not url:
                continue
            results.append({
                "title": (item.get("Title") or url).strip(),
                "href": url,
                "body": (item.get("Summary") or "").strip(),
                "engine": self.ENGINE_NAME,
                "thumbnail_url": item.get("ThumbnailUrl") or "",
            })
        return {"results": results, "total": data.get("Total", len(items))}

    def ask(self, question: str, model: str = "zhida-agent", timeout: int = 60) -> Dict[str, Any]:
        if not question.strip():
            raise ValueError("问题不能为空")

        response = self.session.post(
            f"{self.base_url}/v1/chat/completions",
            json={
                "model": model,
                "messages": [{"role": "user", "content": question}],
                "stream": False,
            },
            headers=self._headers(),
            timeout=timeout,
        )
        if response.status_code != 200:
            detail = response.text.strip()[:500]
            raise RuntimeError(f"知乎直答请求失败：HTTP {response.status_code} {detail}")

        payload = response.json()
        if payload.get("error"):
            error = payload["error"]
            raise RuntimeError(f"知乎直答返回错误：{error.get('code')} {error.get('message')}")

        choices = payload.get("choices") or []
        message = (choices[0].get("message") or {}) if choices else {}
        return {
            "answer": message.get("content", ""),
            "reasoning_content": message.get("reasoning_content", ""),
            "model": payload.get("model", model),
            "id": payload.get("id", ""),
        }

    def format_results(self, results: List[Dict[str, Any]], query: str) -> str:
        output = [
            f"🔍 {self.ENGINE_DISPLAY_NAME}: {query}",
            f"📊 找到 {len(results)} 条结果",
            "",
        ]
        for i, item in enumerate(results, 1):
            output.append(f"[{i}] {item.get('title', '')}")
            output.append(f"    🔗 {item.get('href', '')}")
            if item.get("author_name"):
                output.append(f"    👤 {item['author_name']}")
            if item.get("vote_up_count"):
                output.append(f"    👍 {item['vote_up_count']} 赞同")
            if item.get("body"):
                body = item["body"]
                output.append(f"    📝 {body[:200]}{'...' if len(body) > 200 else ''}")
            output.append("")
        return "\n".join(output)


def search_zhihu_official(
    query: str,
    max_results: int = 10,
    access_secret: Optional[str] = None,
    **kwargs,
) -> List[Dict[str, Any]]:
    client = ZhihuOfficialSearchClient(access_secret=access_secret)
    return client.search(query=query, max_results=max_results, **kwargs)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="知乎开放平台搜索（站内搜索、全网搜索、热榜、直答）")
    subparsers = parser.add_subparsers(dest="command", required=True)

    for name, help_text in (("search", "知乎站内搜索"), ("global", "知乎全网搜索")):
        sub = subparsers.add_parser(name, help=help_text)
        sub.add_argument("query", help="搜索关键词")
        sub.add_argument("-m", "--max-results", type=int, default=10, help="结果数量，站内最多 10，全网最多 20")
        sub.add_argument("--access-secret", help="知乎 Access Secret")
        sub.add_argument("--base-url", help="接口地址，默认 https://developer.zhihu.com")
        sub.add_argument("--timeout", type=int, default=10, help="请求超时秒数")
        sub.add_argument("--json", action="store_true", help="JSON 输出")

    hot_parser = subparsers.add_parser("hot", help="知乎热榜")
    hot_parser.add_argument("-m", "--max-results", type=int, default=30, help="条目数量，最多 30")
    hot_parser.add_argument("--access-secret", help="知乎 Access Secret")
    hot_parser.add_argument("--base-url", help="接口地址")
    hot_parser.add_argument("--timeout", type=int, default=10, help="请求超时秒数")
    hot_parser.add_argument("--json", action="store_true", help="JSON 输出")

    ask_parser = subparsers.add_parser("ask", help="知乎直答")
    ask_parser.add_argument("question", help="问题内容")
    ask_parser.add_argument("--model", choices=list(ASK_MODELS), default="zhida-agent", help="直答模型")
    ask_parser.add_argument("--access-secret", help="知乎 Access Secret")
    ask_parser.add_argument("--base-url", help="接口地址")
    ask_parser.add_argument("--timeout", type=int, default=60, help="请求超时秒数")
    ask_parser.add_argument("--json", action="store_true", help="JSON 输出")

    args = parser.parse_args()

    client = ZhihuOfficialSearchClient(
        access_secret=getattr(args, "access_secret", None),
        base_url=getattr(args, "base_url", None),
    )

    if args.command in ("search", "global"):
        results = client.search(
            query=args.query,
            max_results=args.max_results,
            scope=args.command,
            timeout=args.timeout,
        )
        if args.json:
            print(json.dumps({"results": results}, ensure_ascii=False, indent=2))
        else:
            print(client.format_results(results, args.query))
    elif args.command == "hot":
        data = client.hot_list(limit=args.max_results, timeout=args.timeout)
        if args.json:
            print(json.dumps(data, ensure_ascii=False, indent=2))
        else:
            print(client.format_results(data["results"], "知乎热榜"))
    else:
        data = client.ask(args.question, model=args.model, timeout=args.timeout)
        if args.json:
            print(json.dumps(data, ensure_ascii=False, indent=2))
        else:
            print(data["answer"])
