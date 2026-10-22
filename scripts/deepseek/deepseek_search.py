import argparse
import json
import os
from typing import Any, Dict, List, Optional

import requests
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), ".env"))

DEFAULT_API_URL = "https://api.deepseek.com"
MAX_QUERY_LENGTH = 128
MAX_COUNT = 50


class DeepSeekSearchClient:
    """DeepSeek 联网搜索客户端，接口文档 https://api-docs.deepseek.com/zh-cn/api/search/"""

    ENGINE_NAME = "deepseek"
    ENGINE_DISPLAY_NAME = "DeepSeek 联网搜索"
    REQUIRES_API_KEY = True

    def __init__(self, api_key: Optional[str] = None, api_url: Optional[str] = None):
        self.api_key = api_key or os.environ.get("DEEPSEEK_API_KEY")
        if not self.api_key:
            raise ValueError("DeepSeek API Key 未配置，请设置 DEEPSEEK_API_KEY 环境变量")

        self.api_url = (api_url or os.environ.get("DEEPSEEK_API_URL") or DEFAULT_API_URL).rstrip("/")
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        })

    def search(
        self,
        query: str,
        max_results: int = 10,
        ori_question: Optional[str] = None,
        localization: Optional[str] = None,
        need_content: bool = False,
        timeout: int = 30,
    ) -> List[Dict[str, Any]]:
        if not query.strip():
            raise ValueError("搜索关键词不能为空")
        if len(query) > MAX_QUERY_LENGTH:
            raise ValueError(f"搜索关键词最多 {MAX_QUERY_LENGTH} 个字符，当前 {len(query)} 个")
        if not 1 <= max_results <= MAX_COUNT:
            raise ValueError(f"结果数量必须在 1-{MAX_COUNT} 之间")

        body: Dict[str, Any] = {
            "query": query,
            "count": max_results,
            "need_content": need_content,
        }
        if ori_question:
            body["ori_question"] = ori_question
        if localization:
            body["localization"] = localization

        response = self.session.post(
            f"{self.api_url}/v1/tools/search",
            json=body,
            timeout=timeout,
        )
        if response.status_code != 200:
            detail = response.text.strip()[:500]
            raise RuntimeError(f"DeepSeek 搜索请求失败：HTTP {response.status_code} {detail}")

        payload = response.json()
        raw_results = payload.get("results")
        if not isinstance(raw_results, list):
            raise RuntimeError(f"DeepSeek 响应缺少 results 字段：{payload}")

        results = []
        for item in raw_results:
            url = (item.get("url") or "").strip()
            if not url:
                continue
            results.append({
                "title": (item.get("title") or url).strip(),
                "href": url,
                "body": (item.get("snippet") or item.get("summary") or "").strip(),
                "engine": self.ENGINE_NAME,
                "summary": item.get("summary", ""),
                "content": item.get("content", ""),
                "site_name": item.get("site_name"),
                "site_icon": item.get("site_icon"),
                "date": item.get("date"),
                "authority": item.get("authority"),
                "rerank_score": item.get("rerank_score"),
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
            if item.get("date"):
                output.append(f"    🕒 {item['date']}")
            if item.get("rerank_score") is not None:
                output.append(f"    ⭐ 相关度：{item['rerank_score']}")
            if item.get("body"):
                body = item["body"]
                output.append(f"    📝 {body[:200]}{'...' if len(body) > 200 else ''}")
            output.append("")
        return "\n".join(output)


def search_deepseek(
    query: str,
    max_results: int = 10,
    api_key: Optional[str] = None,
    **kwargs,
) -> List[Dict[str, Any]]:
    client = DeepSeekSearchClient(api_key=api_key)
    return client.search(query=query, max_results=max_results, **kwargs)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="DeepSeek 联网搜索 API")
    parser.add_argument("query", help="搜索关键词，最多 128 个字符")
    parser.add_argument("-m", "--max-results", type=int, default=10, help="结果数量 1-50")
    parser.add_argument("--ori-question", help="原始用户问题，帮助提升排序效果")
    parser.add_argument("--localization", help="本地化结果所用 IP 地址")
    parser.add_argument("--need-content", action="store_true", help="返回网页正文")
    parser.add_argument("--api-key", help="DeepSeek API Key")
    parser.add_argument("--api-url", help="DeepSeek API 地址，默认 https://api.deepseek.com")
    parser.add_argument("--timeout", type=int, default=30, help="请求超时秒数")
    parser.add_argument("--json", action="store_true", help="JSON 输出")

    args = parser.parse_args()

    client = DeepSeekSearchClient(api_key=args.api_key, api_url=args.api_url)
    results = client.search(
        query=args.query,
        max_results=args.max_results,
        ori_question=args.ori_question,
        localization=args.localization,
        need_content=args.need_content,
        timeout=args.timeout,
    )

    if args.json:
        print(json.dumps({"results": results}, ensure_ascii=False, indent=2))
    else:
        print(client.format_results(results, args.query))
