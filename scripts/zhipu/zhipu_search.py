import argparse
import json
import os
from typing import Any, Dict, List, Optional

import requests
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), ".env"))

DEFAULT_ENDPOINT = "https://open.bigmodel.cn/api/paas/v4/web_search"
DEFAULT_ENGINE = "search_std"
ALLOWED_ENGINES = ("search_std", "search_pro", "search_pro_sogou", "search_pro_quark")
ALLOWED_RECENCY = ("oneDay", "oneWeek", "oneMonth", "oneYear", "noLimit")
ALLOWED_CONTENT_SIZE = ("medium", "high")
SOGOU_COUNTS = (10, 20, 30, 40, 50)
MAX_QUERY_LENGTH = 70


class ZhipuSearchClient:
    """智谱网络搜索客户端，接口文档 https://docs.bigmodel.cn/api-reference/工具-api/网络搜索"""

    ENGINE_NAME = "zhipu"
    ENGINE_DISPLAY_NAME = "智谱网络搜索"
    REQUIRES_API_KEY = True

    def __init__(self, api_key: Optional[str] = None, endpoint: Optional[str] = None):
        self.api_key = api_key or os.environ.get("ZHIPU_API_KEY")
        if not self.api_key:
            raise ValueError("智谱 API Key 未配置，请设置 ZHIPU_API_KEY 环境变量")
        if self.api_key.lower().startswith("bearer "):
            self.api_key = self.api_key.split(None, 1)[1]

        self.endpoint = endpoint or os.environ.get("ZHIPU_WEB_SEARCH_ENDPOINT") or DEFAULT_ENDPOINT
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        })

    def search(
        self,
        query: str,
        max_results: int = 10,
        search_engine: Optional[str] = None,
        domain: Optional[str] = None,
        recency: Optional[str] = None,
        content_size: Optional[str] = None,
        search_intent: bool = False,
        timeout: int = 30,
    ) -> List[Dict[str, Any]]:
        text = query.strip()
        if not text:
            raise ValueError("搜索关键词不能为空")
        if len(text) > MAX_QUERY_LENGTH:
            raise ValueError(f"搜索关键词最长 {MAX_QUERY_LENGTH} 个字符")

        search_engine = search_engine or os.environ.get("ZHIPU_SEARCH_ENGINE") or DEFAULT_ENGINE
        if search_engine not in ALLOWED_ENGINES:
            raise ValueError(f"search_engine 只能是 {', '.join(ALLOWED_ENGINES)}")
        if recency and recency not in ALLOWED_RECENCY:
            raise ValueError(f"recency 只能是 {', '.join(ALLOWED_RECENCY)}")
        if content_size and content_size not in ALLOWED_CONTENT_SIZE:
            raise ValueError(f"content_size 只能是 {', '.join(ALLOWED_CONTENT_SIZE)}")

        count = max(1, min(max_results, 50))
        if search_engine == "search_pro_sogou":
            count = min(SOGOU_COUNTS, key=lambda step: abs(step - count))

        body: Dict[str, Any] = {
            "search_query": text,
            "search_engine": search_engine,
            "search_intent": search_intent,
            "count": count,
        }
        if domain:
            body["search_domain_filter"] = domain
        if recency:
            body["search_recency_filter"] = recency
        if content_size:
            body["content_size"] = content_size

        response = self.session.post(self.endpoint, json=body, timeout=timeout)
        if response.status_code != 200:
            detail = response.text.strip()[:500]
            raise RuntimeError(f"智谱搜索请求失败：HTTP {response.status_code} {detail}")

        payload = response.json()
        if payload.get("error"):
            error = payload["error"]
            raise RuntimeError(f"智谱搜索返回错误：{error.get('code')} {error.get('message')}")

        raw_results = payload.get("search_result")
        if not isinstance(raw_results, list):
            raise RuntimeError(f"智谱响应缺少 search_result 字段：{payload}")

        intents = payload.get("search_intent") or []
        keywords = ""
        if intents and isinstance(intents[0], dict):
            keywords = intents[0].get("keywords") or ""

        results = []
        for item in raw_results[:count]:
            link = (item.get("link") or "").strip()
            if not link:
                continue
            results.append({
                "title": (item.get("title") or link).strip(),
                "href": link,
                "body": (item.get("content") or "").strip(),
                "engine": self.ENGINE_NAME,
                "media": item.get("media") or "",
                "publish_date": item.get("publish_date") or "",
                "refer": item.get("refer"),
                "keywords": keywords,
                "request_id": payload.get("request_id") or payload.get("id"),
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
            if item.get("media"):
                output.append(f"    📰 来源：{item['media']}")
            if item.get("publish_date"):
                output.append(f"    📅 {item['publish_date']}")
            if item.get("body"):
                body = item["body"]
                output.append(f"    📝 {body[:200]}{'...' if len(body) > 200 else ''}")
            output.append("")
        return "\n".join(output)


def search_zhipu(
    query: str,
    max_results: int = 10,
    api_key: Optional[str] = None,
    **kwargs,
) -> List[Dict[str, Any]]:
    client = ZhipuSearchClient(api_key=api_key)
    return client.search(query=query, max_results=max_results, **kwargs)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="智谱网络搜索 API")
    parser.add_argument("query", help="搜索关键词，最长 70 个字符")
    parser.add_argument("-m", "--max-results", type=int, default=10, help="结果数量，1-50")
    parser.add_argument("--engine", choices=ALLOWED_ENGINES, help="搜索引擎，默认 search_std")
    parser.add_argument("--domain", help="只保留该域名，如 www.example.com")
    parser.add_argument("--recency", choices=ALLOWED_RECENCY, help="时间范围")
    parser.add_argument("--content-size", choices=ALLOWED_CONTENT_SIZE, help="摘要长度")
    parser.add_argument("--search-intent", action="store_true", help="先做意图识别，无搜索意图时不检索")
    parser.add_argument("--api-key", help="智谱 API Key")
    parser.add_argument("--endpoint", help="接口地址")
    parser.add_argument("--timeout", type=int, default=30, help="请求超时秒数")
    parser.add_argument("--json", action="store_true", help="JSON 输出")

    args = parser.parse_args()

    client = ZhipuSearchClient(api_key=args.api_key, endpoint=args.endpoint)
    results = client.search(
        query=args.query,
        max_results=args.max_results,
        search_engine=args.engine,
        domain=args.domain,
        recency=args.recency,
        content_size=args.content_size,
        search_intent=args.search_intent,
        timeout=args.timeout,
    )

    if args.json:
        print(json.dumps({"results": results}, ensure_ascii=False, indent=2))
    else:
        print(client.format_results(results, args.query))
