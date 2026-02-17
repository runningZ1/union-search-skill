#!/usr/bin/env python3
"""
火山引擎图片搜索 API 客户端

专门用于图片搜索功能,从 volcengine_search.py 解耦而来
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
        Path(__file__).parent / ".env",  # scripts 目录
        Path(__file__).parent.parent / ".env",  # 技能根目录
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


class VolcengineImageSearchClient:
    """火山引擎图片搜索 API 客户端"""

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

    def image_search(
        self,
        query: str,
        count: int = 5,
        width_min: Optional[int] = None,
        width_max: Optional[int] = None,
        height_min: Optional[int] = None,
        height_max: Optional[int] = None,
        shapes: Optional[List[str]] = None,
        query_rewrite: bool = False
    ) -> Dict[str, Any]:
        """
        执行图片搜索

        Args:
            query: 搜索关键词
            count: 返回结果数量 (最多5条)
            width_min: 最小宽度
            width_max: 最大宽度
            height_min: 最小高度
            height_max: 最大高度
            shapes: 图片形状列表 (横长方形/竖长方形/方形)
            query_rewrite: 是否开启Query改写

        Returns:
            搜索结果字典
        """
        payload = {
            "Query": query,
            "SearchType": "image",
            "Count": min(count, 5),  # 最多5条
            "Filter": {},
            "QueryControl": {
                "QueryRewrite": query_rewrite
            }
        }

        if width_min is not None:
            payload["Filter"]["ImageWidthMin"] = width_min
        if width_max is not None:
            payload["Filter"]["ImageWidthMax"] = width_max
        if height_min is not None:
            payload["Filter"]["ImageHeightMin"] = height_min
        if height_max is not None:
            payload["Filter"]["ImageHeightMax"] = height_max
        if shapes:
            payload["Filter"]["ImageShapes"] = shapes

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
        print("Usage: python volcengine_image_search.py <query> [count]")
        print("\nAPI Key Configuration:")
        print("  1. Set environment variable: VOLCENGINE_API_KEY=your_api_key")
        print("  2. Create .env file with: VOLCENGINE_API_KEY=your_api_key")
        print("\nExample:")
        print('  python volcengine_image_search.py "可爱的猫咪" 5')
        sys.exit(1)

    query = sys.argv[1]
    count = int(sys.argv[2]) if len(sys.argv) > 2 else 5

    # 检查 API Key 是否存在
    if not api_key:
        print("Error: API Key not found. Please set VOLCENGINE_API_KEY environment variable or create .env file.", file=sys.stderr)
        sys.exit(1)

    client = VolcengineImageSearchClient(api_key)
    result = client.image_search(query, count=count)

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
