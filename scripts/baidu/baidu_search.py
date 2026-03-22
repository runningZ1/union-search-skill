#!/usr/bin/env python3
"""
百度千帆 AI Search（基于 baidu-search-1.1.3 迁移）

调用方式：
python scripts/baidu/baidu_search.py '{"query":"人工智能","count":10,"freshness":"pd"}'

输出：JSON 数组（references 列表）
"""

import json
import os
import re
import sys
from datetime import datetime, timedelta
from typing import Any, Dict, List

import requests

API_ENV_KEYS = ("BAIDU_API_KEY", "BAIDU_QIANFAN_API_KEY")
API_URL = "https://qianfan.baidubce.com/v2/ai_search/web_search"


def _resolve_api_key() -> str:
    for key in API_ENV_KEYS:
        value = os.getenv(key)
        if value:
            return value
    return ""


def _build_search_filter(freshness: str) -> Dict[str, Any]:
    current_time = datetime.now()
    end_date = (current_time + timedelta(days=1)).strftime("%Y-%m-%d")
    pattern = r"\d{4}-\d{2}-\d{2}to\d{4}-\d{2}-\d{2}"

    if freshness in {"pd", "pw", "pm", "py"}:
        if freshness == "pd":
            start_date = (current_time - timedelta(days=1)).strftime("%Y-%m-%d")
        elif freshness == "pw":
            start_date = (current_time - timedelta(days=6)).strftime("%Y-%m-%d")
        elif freshness == "pm":
            start_date = (current_time - timedelta(days=30)).strftime("%Y-%m-%d")
        else:
            start_date = (current_time - timedelta(days=364)).strftime("%Y-%m-%d")
        return {"range": {"page_time": {"gte": start_date, "lt": end_date}}}

    if re.fullmatch(pattern, freshness):
        start_date, parsed_end_date = freshness.split("to", 1)
        return {"range": {"page_time": {"gte": start_date, "lt": parsed_end_date}}}

    raise ValueError(f"freshness ({freshness}) must be pd/pw/pm/py or YYYY-MM-DDtoYYYY-MM-DD")


def baidu_search(api_key: str, request_body: Dict[str, Any]) -> List[Dict[str, Any]]:
    headers = {
        "Authorization": f"Bearer {api_key}",
        "X-Appbuilder-From": "openclaw",
        "Content-Type": "application/json",
    }

    response = requests.post(API_URL, json=request_body, headers=headers, timeout=30)
    response.raise_for_status()
    data = response.json()

    if isinstance(data, dict) and data.get("code"):
        raise RuntimeError(data.get("message", "Baidu API returned error"))

    references = data.get("references", []) if isinstance(data, dict) else []
    for item in references:
        if isinstance(item, dict) and "snippet" in item:
            del item["snippet"]
    return references


def _parse_request_payload(raw: str) -> Dict[str, Any]:
    payload = json.loads(raw)
    if not isinstance(payload, dict):
        raise ValueError("request body must be a JSON object")
    if "query" not in payload or not str(payload["query"]).strip():
        raise ValueError("query must be present in request body")
    return payload


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python baidu_search.py <Json>", file=sys.stderr)
        return 1

    try:
        payload = _parse_request_payload(sys.argv[1])
    except Exception as exc:
        print(f"JSON parse error: {exc}", file=sys.stderr)
        return 1

    count = int(payload.get("count", 10))
    if count <= 0:
        count = 10
    elif count > 50:
        count = 50

    search_filter: Dict[str, Any] = {}
    freshness = payload.get("freshness")
    if freshness is not None:
        try:
            search_filter = _build_search_filter(str(freshness))
        except ValueError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1

    api_key = _resolve_api_key()
    if not api_key:
        print("Error: BAIDU_API_KEY (or BAIDU_QIANFAN_API_KEY) must be set.", file=sys.stderr)
        return 1

    request_body = {
        "messages": [{"content": str(payload["query"]), "role": "user"}],
        "search_source": "baidu_search_v2",
        "resource_type_filter": [{"type": "web", "top_k": count}],
        "search_filter": search_filter,
    }

    try:
        results = baidu_search(api_key, request_body)
        print(json.dumps(results, indent=2, ensure_ascii=False))
        return 0
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
