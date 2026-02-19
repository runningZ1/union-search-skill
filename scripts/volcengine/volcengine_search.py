#!/usr/bin/env python3
"""
火山引擎融合信息搜索 API 客户端

提供 Web 搜索和 Web 搜索总结版功能
"""

import json
import sys
import os
import requests
from typing import Dict, List, Optional, Any
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
    
    def web_search(
        self,
        query: str,
        count: int = 10,
        need_content: bool = False,
        need_url: bool = True,
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
        need_url: bool = True,
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
            return response.json()
        except requests.exceptions.RequestException as e:
            return {
                "error": str(e),
                "status_code": getattr(e.response, 'status_code', None) if hasattr(e, 'response') else None
            }


def main():
    """命令行入口"""
    # 尝试从环境变量或 .env 文件加载 API Key
    api_key = load_api_key()

    # 解析命令行参数
    if len(sys.argv) < 2:
        print("Usage: python volcengine_search.py <search_type> <query> [options]")
        print("       python volcengine_search.py <api_key> <search_type> <query> [options]  (deprecated)")
        print("\nSearch types:")
        print("  web         - Web search")
        print("  summary     - Web search with AI summary")
        print("\nAPI Key Configuration:")
        print("  1. Set environment variable: VOLCENGINE_API_KEY=your_api_key")
        print("  2. Create .env file with: VOLCENGINE_API_KEY=your_api_key")
        print("  3. Pass as first argument (deprecated for security)")
        print("\nExample:")
        print('  python volcengine_search.py web "北京旅游攻略"')
        sys.exit(1)

    # 兼容旧的命令行格式 (api_key 作为第一个参数)
    if len(sys.argv) >= 4 and sys.argv[1] not in ["web", "summary"]:
        # 旧格式: python script.py <api_key> <search_type> <query>
        api_key = sys.argv[1]
        search_type = sys.argv[2]
        query = sys.argv[3]
        print("Warning: Passing API key as command line argument is deprecated. Use environment variable or .env file instead.", file=sys.stderr)
    elif len(sys.argv) >= 3:
        # 新格式: python script.py <search_type> <query>
        search_type = sys.argv[1]
        query = sys.argv[2]
    else:
        print("Error: Invalid arguments", file=sys.stderr)
        sys.exit(1)

    # 检查 API Key 是否存在
    if not api_key:
        print("Error: API Key not found. Please set VOLCENGINE_API_KEY environment variable or create .env file.", file=sys.stderr)
        sys.exit(1)

    client = VolcengineSearchClient(api_key)

    if search_type == "web":
        result = client.web_search(query, count=10, need_summary=True)
    elif search_type == "summary":
        result = client.web_search_summary(query, count=10)
    else:
        print(f"Unknown search type: {search_type}")
        sys.exit(1)

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
