import argparse
import json
import os
from typing import Any, Dict, List, Optional

import requests
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), ".env"))

DEFAULT_ENDPOINT = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
DEFAULT_MODEL = "qwen-plus"
ALLOWED_STRATEGIES = ("turbo", "max", "agent", "agent_max")
ALLOWED_FRESHNESS = (7, 30, 180, 365)


class BailianSearchClient:
    """阿里云百炼联网搜索客户端，接口文档 https://help.aliyun.com/zh/model-studio/web-search"""

    ENGINE_NAME = "bailian"
    ENGINE_DISPLAY_NAME = "阿里云百炼联网搜索"
    REQUIRES_API_KEY = True

    def __init__(self, api_key: Optional[str] = None, endpoint: Optional[str] = None):
        self.api_key = api_key or os.environ.get("DASHSCOPE_API_KEY")
        if not self.api_key:
            raise ValueError("DashScope API Key 未配置，请设置 DASHSCOPE_API_KEY 环境变量")

        self.endpoint = endpoint or os.environ.get("DASHSCOPE_ENDPOINT") or DEFAULT_ENDPOINT
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        })

    def search(
        self,
        query: str,
        max_results: int = 10,
        model: Optional[str] = None,
        strategy: str = "turbo",
        freshness: Optional[int] = None,
        sites: Optional[List[str]] = None,
        vertical: bool = False,
        timeout: int = 60,
    ) -> Dict[str, Any]:
        if not query.strip():
            raise ValueError("搜索关键词不能为空")
        if strategy not in ALLOWED_STRATEGIES:
            raise ValueError(f"search_strategy 只能是 {', '.join(ALLOWED_STRATEGIES)}")
        if freshness is not None and freshness not in ALLOWED_FRESHNESS:
            raise ValueError("freshness 只能是 7、30、180、365 天")

        search_options: Dict[str, Any] = {
            "forced_search": True,
            "enable_source": True,
            "search_strategy": strategy,
        }
        if freshness is not None:
            search_options["freshness"] = freshness
        if sites:
            search_options["assigned_site_list"] = sites
        if vertical:
            search_options["enable_search_extension"] = True

        body = {
            "model": model or os.environ.get("BAILIAN_SEARCH_MODEL") or DEFAULT_MODEL,
            "input": {"messages": [{"role": "user", "content": query}]},
            "parameters": {
                "enable_search": True,
                "result_format": "message",
                "search_options": search_options,
            },
        }

        response = self.session.post(self.endpoint, json=body, timeout=timeout)
        if response.status_code != 200:
            detail = response.text.strip()[:500]
            raise RuntimeError(f"百炼联网搜索请求失败：HTTP {response.status_code} {detail}")

        payload = response.json()
        if payload.get("code"):
            raise RuntimeError(f"百炼联网搜索返回错误：{payload.get('code')} {payload.get('message')}")

        output = payload.get("output") or {}
        choices = output.get("choices") or []
        answer = ""
        if choices:
            answer = (choices[0].get("message") or {}).get("content", "")

        search_info = output.get("search_info")
        if not isinstance(search_info, dict):
            raise RuntimeError(f"百炼联网搜索未返回搜索来源：{json.dumps(payload, ensure_ascii=False)[:500]}")

        raw_results = search_info.get("search_results") or []
        results = []
        for item in raw_results[:max_results]:
            url = (item.get("url") or "").strip()
            if not url:
                continue
            results.append({
                "title": (item.get("title") or url).strip(),
                "href": url,
                "body": "",
                "engine": self.ENGINE_NAME,
                "site_name": item.get("site_name") or "",
                "icon": item.get("icon") or "",
                "index": item.get("index"),
            })

        return {
            "results": results,
            "answer": answer,
            "model": payload.get("model", body["model"]),
            "usage": payload.get("usage", {}),
            "extra_tool_info": search_info.get("extra_tool_info", []),
        }

    def format_results(self, results: List[Dict[str, Any]], query: str, answer: str = "") -> str:
        output = [
            f"🔍 {self.ENGINE_DISPLAY_NAME}: {query}",
            f"📊 找到 {len(results)} 条来源",
            "",
        ]
        for i, item in enumerate(results, 1):
            output.append(f"[{i}] {item.get('title', '')}")
            output.append(f"    🔗 {item.get('href', '')}")
            if item.get("site_name"):
                output.append(f"    📰 来源：{item['site_name']}")
            output.append("")
        if answer:
            output.append("## 模型回答")
            output.append(answer)
        return "\n".join(output)


def search_bailian(
    query: str,
    max_results: int = 10,
    api_key: Optional[str] = None,
    **kwargs,
) -> List[Dict[str, Any]]:
    client = BailianSearchClient(api_key=api_key)
    return client.search(query=query, max_results=max_results, **kwargs)["results"]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="阿里云百炼联网搜索 API")
    parser.add_argument("query", help="搜索关键词")
    parser.add_argument("-m", "--max-results", type=int, default=10, help="来源数量")
    parser.add_argument("--model", help="模型名称，默认 qwen-plus")
    parser.add_argument("--strategy", choices=list(ALLOWED_STRATEGIES), default="turbo", help="检索策略")
    parser.add_argument("--freshness", type=int, choices=list(ALLOWED_FRESHNESS), help="时间范围天数，仅 turbo 支持")
    parser.add_argument("--sites", nargs="+", help="限定站点域名，最多 25 个，仅 turbo 支持")
    parser.add_argument("--vertical", action="store_true", help="启用垂直领域搜索（股票、天气、汇率等）")
    parser.add_argument("--api-key", help="DashScope API Key")
    parser.add_argument("--endpoint", help="接口地址")
    parser.add_argument("--timeout", type=int, default=60, help="请求超时秒数")
    parser.add_argument("--json", action="store_true", help="JSON 输出")

    args = parser.parse_args()

    client = BailianSearchClient(api_key=args.api_key, endpoint=args.endpoint)
    data = client.search(
        query=args.query,
        max_results=args.max_results,
        model=args.model,
        strategy=args.strategy,
        freshness=args.freshness,
        sites=args.sites,
        vertical=args.vertical,
        timeout=args.timeout,
    )

    if args.json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        print(client.format_results(data["results"], args.query, data["answer"]))
