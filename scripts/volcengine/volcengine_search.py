#!/usr/bin/env python3
"""
火山引擎融合信息搜索 API 客户端

提供 Web 搜索和 Web 搜索总结版功能
"""

import argparse
import json
import sys
import os
import requests
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path


def load_api_key() -> Optional[str]:
    """
    从环境变量或 .env 文件加载 API Key

    优先级:
    1. 环境变量 VOLCENGINE_API_KEY
    2. 当前目录的 .env 文件
    3. 技能根目录的 .env 文件

    Returns:
        API Key 或 None
    """
    # 1. 尝试从环境变量读取
    api_key = os.getenv("VOLCENGINE_API_KEY")
    if api_key:
        return api_key

    # 2. 尝试从当前目录的 .env 文件读取
    env_paths = [
        Path.cwd() / ".env",  # 当前工作目录
        Path(__file__).parent / ".env",  # volcengine 目录
        Path(__file__).parent.parent / ".env",  # scripts 目录
        Path(__file__).parent.parent.parent / ".env",  # 技能根目录
    ]

    for env_path in env_paths:
        if env_path.exists():
            try:
                with open(env_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            if '=' in line:
                                key, value = line.split('=', 1)
                                key = key.strip()
                                value = value.strip().strip('"').strip("'")
                                if key == "VOLCENGINE_API_KEY":
                                    return value
            except Exception as e:
                print(f"Warning: Failed to read {env_path}: {e}", file=sys.stderr)

    return None


class VolcengineSearchClient:
    """火山引擎搜索 API 客户端"""
    
    def __init__(self, api_key: str):
        """
        初始化客户端
        
        Args:
            api_key: API Key (从火山引擎控制台获取)
        """
        self.api_key = api_key
        self.base_url = "https://open.feedcoopapi.com/search_api/web_search"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

    @staticmethod
    def _validate_query(query: str) -> None:
        if not isinstance(query, str) or not query.strip():
            raise ValueError("Query 不能为空")
        if len(query) > 100:
            raise ValueError("Query 长度不能超过 100 个字符")

    @staticmethod
    def _validate_count(search_type: str, count: int) -> None:
        if count <= 0:
            raise ValueError("Count 必须大于 0")
        if search_type in ("web", "web_summary") and count > 50:
            raise ValueError("web/web_summary 的 Count 最大为 50")

    @staticmethod
    def _validate_time_range(time_range: Optional[str]) -> None:
        if not time_range:
            return
        allowed = {"OneDay", "OneWeek", "OneMonth", "OneYear"}
        if time_range in allowed:
            return
        # 简单校验 YYYY-MM-DD..YYYY-MM-DD
        if ".." in time_range and len(time_range) == 22:
            return
        raise ValueError("TimeRange 非法，请使用 OneDay/OneWeek/OneMonth/OneYear 或 YYYY-MM-DD..YYYY-MM-DD")

    @staticmethod
    def _validate_domains(domains: Optional[List[str]], field_name: str) -> None:
        if not domains:
            return
        if len(domains) > 5:
            raise ValueError(f"{field_name} 最多支持 5 个域名")
        for d in domains:
            if not d or "." not in d:
                raise ValueError(f"{field_name} 中存在非法域名: {d}")

    @staticmethod
    def _validate_auth_info_level(auth_info_level: int) -> None:
        if auth_info_level not in (0, 1):
            raise ValueError("AuthInfoLevel 仅支持 0 或 1")

    @staticmethod
    def _validate_industry(industry: Optional[str]) -> None:
        if industry and industry not in ("finance", "game"):
            raise ValueError("Industry 仅支持 finance 或 game")
    
    def web_search(
        self,
        query: str,
        count: int = 10,
        need_content: bool = False,
        need_url: bool = False,
        need_summary: bool = False,
        time_range: Optional[str] = None,
        sites: Optional[List[str]] = None,
        block_hosts: Optional[List[str]] = None,
        auth_info_level: int = 0,
        query_rewrite: bool = False,
        industry: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        执行 Web 搜索
        
        Args:
            query: 搜索关键词 (1-100字符)
            count: 返回结果数量 (最多50条)
            need_content: 是否需要正文内容
            need_url: 是否需要原文链接
            need_summary: 是否需要精准摘要
            time_range: 时间范围 (OneDay/OneWeek/OneMonth/OneYear/YYYY-MM-DD..YYYY-MM-DD)
            sites: 指定搜索站点列表
            block_hosts: 屏蔽站点列表
            auth_info_level: 权威度级别 (0:不限制, 1:非常权威)
            query_rewrite: 是否开启Query改写
            industry: 行业类型 (finance/game)
        
        Returns:
            搜索结果字典
        """
        self._validate_query(query)
        self._validate_count("web", count)
        self._validate_time_range(time_range)
        self._validate_domains(sites, "Sites")
        self._validate_domains(block_hosts, "BlockHosts")
        self._validate_auth_info_level(auth_info_level)
        self._validate_industry(industry)

        payload = {
            "Query": query,
            "SearchType": "web",
            "Count": count,
            "Filter": {
                "NeedContent": need_content,
                "NeedUrl": need_url,
                "AuthInfoLevel": auth_info_level
            },
            "NeedSummary": need_summary,
            "QueryControl": {
                "QueryRewrite": query_rewrite
            }
        }
        
        if time_range:
            payload["TimeRange"] = time_range
        
        if sites:
            payload["Filter"]["Sites"] = "|".join(sites)
        
        if block_hosts:
            payload["Filter"]["BlockHosts"] = "|".join(block_hosts)
        
        if industry:
            payload["Industry"] = industry
        
        return self._make_request(payload)
    
    def web_search_summary(
        self,
        query: str,
        count: int = 10,
        need_content: bool = False,
        need_url: bool = False,
        time_range: Optional[str] = None,
        sites: Optional[List[str]] = None,
        block_hosts: Optional[List[str]] = None,
        auth_info_level: int = 0,
        query_rewrite: bool = False,
        industry: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        执行 Web 搜索总结版 (包含大模型总结)
        
        Args:
            query: 搜索关键词 (1-100字符)
            count: 返回结果数量 (最多50条)
            need_content: 是否需要正文内容
            need_url: 是否需要原文链接
            time_range: 时间范围 (OneDay/OneWeek/OneMonth/OneYear/YYYY-MM-DD..YYYY-MM-DD)
            sites: 指定搜索站点列表
            block_hosts: 屏蔽站点列表
            auth_info_level: 权威度级别 (0:不限制, 1:非常权威)
            query_rewrite: 是否开启Query改写
            industry: 行业类型 (finance/game)
        
        Returns:
            搜索结果字典 (包含 Choices 字段的总结内容)
        """
        self._validate_query(query)
        self._validate_count("web_summary", count)
        self._validate_time_range(time_range)
        self._validate_domains(sites, "Sites")
        self._validate_domains(block_hosts, "BlockHosts")
        self._validate_auth_info_level(auth_info_level)
        self._validate_industry(industry)

        payload = {
            "Query": query,
            "SearchType": "web_summary",
            "Count": count,
            "Filter": {
                "NeedContent": need_content,
                "NeedUrl": need_url,
                "AuthInfoLevel": auth_info_level
            },
            "NeedSummary": True,  # 总结版必须为 True
            "QueryControl": {
                "QueryRewrite": query_rewrite
            }
        }
        
        if time_range:
            payload["TimeRange"] = time_range
        
        if sites:
            payload["Filter"]["Sites"] = "|".join(sites)
        
        if block_hosts:
            payload["Filter"]["BlockHosts"] = "|".join(block_hosts)
        
        if industry:
            payload["Industry"] = industry
        
        return self._make_request(payload)

    def _make_request(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        发送 API 请求
        
        Args:
            payload: 请求体
        
        Returns:
            响应数据
        
        Raises:
            requests.exceptions.RequestException: 请求失败
        """
        try:
            response = requests.post(
                self.base_url,
                headers=self.headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            content_type = (response.headers.get("content-type") or "").lower()
            if "text/event-stream" in content_type:
                # API may omit charset and cause mojibake when requests guesses latin-1.
                sse_text = response.content.decode("utf-8", errors="replace")
                parsed = self._parse_sse_response(sse_text)
                if parsed is not None:
                    return parsed
                return {
                    "error": "Failed to parse SSE response as JSON",
                    "status_code": response.status_code,
                    "content_type": response.headers.get("content-type")
                }

            try:
                return response.json()
            except json.JSONDecodeError:
                body_preview = response.text[:500] if response.text else ""
                return {
                    "error": "Invalid JSON response",
                    "status_code": response.status_code,
                    "content_type": response.headers.get("content-type"),
                    "body_preview": body_preview
                }
        except requests.exceptions.RequestException as e:
            return {
                "error": str(e),
                "status_code": getattr(e.response, 'status_code', None) if hasattr(e, 'response') else None
            }

    @staticmethod
    def _parse_sse_response(raw_text: str) -> Optional[Dict[str, Any]]:
        """
        解析 text/event-stream 格式响应，聚合流式 Delta 内容。
        """
        events: List[str] = []
        buffer: List[str] = []

        for line in raw_text.splitlines():
            line = line.rstrip("\r")
            if line.startswith("data:"):
                buffer.append(line[5:].lstrip())
            elif line == "" and buffer:
                events.append("\n".join(buffer))
                buffer = []

        if buffer:
            events.append("\n".join(buffer))

        parsed_events: List[Dict[str, Any]] = []
        for event in events:
            event = event.strip()
            if not event or event == "[DONE]":
                continue
            try:
                parsed = json.loads(event)
                if isinstance(parsed, dict):
                    parsed_events.append(parsed)
            except json.JSONDecodeError:
                continue

        if not parsed_events:
            return None

        final_event = parsed_events[-1]
        result = final_event.get("Result")
        if not isinstance(result, dict):
            return final_event

        # Use the earliest event with full search results as base.
        for ev in parsed_events:
            ev_result = ev.get("Result")
            if isinstance(ev_result, dict) and ev_result.get("WebResults"):
                result["WebResults"] = ev_result.get("WebResults")
                result["ResultCount"] = ev_result.get("ResultCount", len(ev_result.get("WebResults", [])))
                result["SearchContext"] = ev_result.get("SearchContext", result.get("SearchContext"))
                break

        # Aggregate streamed delta text into a final assistant message.
        content_chunks: List[str] = []
        for ev in parsed_events:
            ev_result = ev.get("Result")
            if not isinstance(ev_result, dict):
                continue
            choices = ev_result.get("Choices")
            if not isinstance(choices, list) or not choices:
                continue
            choice0 = choices[0]
            if not isinstance(choice0, dict):
                continue
            delta = choice0.get("Delta")
            if isinstance(delta, dict):
                piece = delta.get("Content")
                if isinstance(piece, str) and piece:
                    content_chunks.append(piece)

        if content_chunks:
            combined_content = "".join(content_chunks)
            choices = result.get("Choices")
            if not isinstance(choices, list) or not choices or not isinstance(choices[0], dict):
                choices = [{"Index": 0, "FinishReason": "stop", "Delta": {"Role": "assistant", "Content": ""}, "Message": None}]
                result["Choices"] = choices
            choice0 = choices[0]
            choice0["Message"] = {
                "Role": "assistant",
                "Content": combined_content
            }

        return final_event


def _split_csv(value: Optional[str]) -> Optional[List[str]]:
    if not value:
        return None
    items = [x.strip() for x in value.split(",") if x.strip()]
    return items or None


def _normalize_legacy_argv(argv: List[str]) -> Tuple[List[str], bool]:
    """
    兼容旧格式: python script.py <api_key> <search_type> <query> [options]
    """
    if len(argv) >= 4 and argv[1] not in ("web", "summary", "-h", "--help"):
        if argv[2] in ("web", "summary"):
            rewritten = [argv[0], argv[2], argv[3], "--api-key", argv[1], *argv[4:]]
            return rewritten, True
    return argv, False


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="火山引擎融合信息搜索 API 客户端（Web / Web Summary）"
    )
    parser.add_argument("--api-key", help="VOLCENGINE_API_KEY，未传时自动从环境变量/.env读取")
    subparsers = parser.add_subparsers(dest="search_type")
    subparsers.required = True

    web_parser = subparsers.add_parser("web", help="Web 搜索")
    web_parser.add_argument("query", help="搜索关键词")
    web_parser.add_argument("--count", type=int, default=10, help="返回条数，web 最大 50")
    web_parser.add_argument("--need-content", action="store_true", help="仅返回有正文的结果")
    web_parser.add_argument("--need-url", action="store_true", help="仅返回有原文链接的结果")
    web_parser.add_argument("--need-summary", action="store_true", help="返回精准摘要")
    web_parser.add_argument("--time-range", help="OneDay/OneWeek/OneMonth/OneYear 或 YYYY-MM-DD..YYYY-MM-DD")
    web_parser.add_argument("--sites", help="站点白名单，逗号分隔，如 github.com,mp.qq.com")
    web_parser.add_argument("--block-hosts", help="站点黑名单，逗号分隔")
    web_parser.add_argument("--auth-info-level", type=int, default=0, choices=[0, 1], help="权威度过滤：0/1")
    web_parser.add_argument("--query-rewrite", action="store_true", help="开启 Query 改写")
    web_parser.add_argument("--industry", choices=["finance", "game"], help="行业搜索类型")

    summary_parser = subparsers.add_parser("summary", help="Web 搜索总结版")
    summary_parser.add_argument("query", help="搜索关键词")
    summary_parser.add_argument("--count", type=int, default=10, help="返回条数，web_summary 最大 50")
    summary_parser.add_argument("--need-content", action="store_true", help="仅返回有正文的结果")
    summary_parser.add_argument("--need-url", action="store_true", help="仅返回有原文链接的结果")
    summary_parser.add_argument("--time-range", help="OneDay/OneWeek/OneMonth/OneYear 或 YYYY-MM-DD..YYYY-MM-DD")
    summary_parser.add_argument("--sites", help="站点白名单，逗号分隔，如 github.com,mp.qq.com")
    summary_parser.add_argument("--block-hosts", help="站点黑名单，逗号分隔")
    summary_parser.add_argument("--auth-info-level", type=int, default=0, choices=[0, 1], help="权威度过滤：0/1")
    summary_parser.add_argument("--query-rewrite", action="store_true", help="开启 Query 改写")
    summary_parser.add_argument("--industry", choices=["finance", "game"], help="行业搜索类型")

    return parser


def main():
    """命令行入口"""
    argv, used_legacy = _normalize_legacy_argv(sys.argv)
    parser = _build_arg_parser()
    args = parser.parse_args(argv[1:])

    if used_legacy:
        print("Warning: Passing API key as first argument is deprecated. Use --api-key or VOLCENGINE_API_KEY.", file=sys.stderr)

    api_key = args.api_key or load_api_key()

    if not api_key:
        print("Error: API Key not found. Please set VOLCENGINE_API_KEY environment variable or create .env file.", file=sys.stderr)
        sys.exit(1)

    client = VolcengineSearchClient(api_key)

    try:
        if args.search_type == "web":
            result = client.web_search(
                query=args.query,
                count=args.count,
                need_content=args.need_content,
                need_url=args.need_url,
                need_summary=args.need_summary,
                time_range=args.time_range,
                sites=_split_csv(args.sites),
                block_hosts=_split_csv(args.block_hosts),
                auth_info_level=args.auth_info_level,
                query_rewrite=args.query_rewrite,
                industry=args.industry,
            )
        elif args.search_type == "summary":
            result = client.web_search_summary(
                query=args.query,
                count=args.count,
                need_content=args.need_content,
                need_url=args.need_url,
                time_range=args.time_range,
                sites=_split_csv(args.sites),
                block_hosts=_split_csv(args.block_hosts),
                auth_info_level=args.auth_info_level,
                query_rewrite=args.query_rewrite,
                industry=args.industry,
            )
        else:
            print(f"Unknown search type: {args.search_type}", file=sys.stderr)
            sys.exit(1)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(2)

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
