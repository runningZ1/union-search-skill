#!/usr/bin/env python3
"""
Google Custom Search - 综合搜索模块

使用 Google Custom Search API 进行网络搜索
"""

import os
import sys
import json
import argparse
import requests
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv

# 加载环境变量 - 从 union-search-skill 根目录
script_dir = os.path.dirname(os.path.abspath(__file__))
skill_root = os.path.dirname(os.path.dirname(script_dir))
load_dotenv(os.path.join(skill_root, '.env'))


class GoogleCustomSearch:
    """Google Custom Search API 客户端"""

    BASE_URL = "https://www.googleapis.com/customsearch/v1"

    def __init__(self, api_key: str = None, search_engine_id: str = None):
        """
        初始化客户端

        Args:
            api_key: Google API Key
            search_engine_id: Google Custom Search Engine ID
        """
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        self.search_engine_id = search_engine_id or os.getenv("GOOGLE_SEARCH_ENGINE_ID")

        if not self.api_key:
            raise ValueError("未找到 GOOGLE_API_KEY，请检查 .env 文件")
        if not self.search_engine_id:
            raise ValueError("未找到 GOOGLE_SEARCH_ENGINE_ID，请检查 .env 文件")

    def search(
        self,
        query: str,
        num: int = 10,
        start: int = 1,
        lr: Optional[str] = None,
        search_type: Optional[str] = None,
        img_size: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        执行搜索

        Args:
            query: 搜索关键词
            num: 返回结果数量 (1-10)
            start: 起始索引
            lr: 语言限制
            search_type: 搜索类型 (image 为图片搜索)
            img_size: 图片尺寸

        Returns:
            搜索结果字典
        """
        params = {
            "key": self.api_key,
            "cx": self.search_engine_id,
            "q": query,
            "num": min(max(num, 1), 10),
            "start": start
        }

        if lr:
            params["lr"] = lr
        if search_type:
            params["searchType"] = search_type
        if img_size and search_type == "image":
            params["imgSize"] = img_size

        response = requests.get(self.BASE_URL, params=params, timeout=10)
        response.raise_for_status()
        return response.json()

    def format_results(self, data: Dict[str, Any], search_type: str = None) -> str:
        """格式化搜索结果"""
        output = []

        search_info = data.get("searchInformation", {})
        total_results = search_info.get("formattedTotalResults", "未知")
        search_time = search_info.get("formattedSearchTime", "未知")

        output.append(f"🔍 搜索: {data.get('queries', {}).get('request', [{}])[0].get('searchTerms', '')}")
        output.append(f"📊 结果: {total_results} 条 | 耗时: {search_time} 秒")
        output.append("")

        for i, item in enumerate(data.get("items", []), 1):
            output.append(f"[{i}] {item.get('title', '')}")
            output.append(f"    🔗 {item.get('link', '')}")
            output.append(f"    📝 {item.get('snippet', '')}")

            if search_type == "image" and "image" in item:
                img = item["image"]
                output.append(f"    📷 尺寸: {img.get('width', 0)}x{img.get('height', 0)}")
                output.append(f"    🖼️ {img.get('thumbnailLink', '')}")

            output.append("")

        return "\n".join(output)


def main():
    parser = argparse.ArgumentParser(description="Google Custom Search")
    parser.add_argument("query", help="搜索关键词")
    parser.add_argument("-n", "--num", type=int, default=10, help="返回结果数量 (1-10)")
    parser.add_argument("--lang", help="语言限制 (如 zh-CN)")
    parser.add_argument("--image", action="store_true", help="图片搜索")
    parser.add_argument("--img-size", help="图片尺寸")
    parser.add_argument("--json", action="store_true", help="JSON 格式输出")
    parser.add_argument("--pretty", action="store_true", help="格式化 JSON")

    args = parser.parse_args()

    try:
        client = GoogleCustomSearch()

        lr = f"lang_{args.lang}" if args.lang else None
        search_type = "image" if args.image else None

        result = client.search(
            query=args.query,
            num=args.num,
            lr=lr,
            search_type=search_type,
            img_size=args.img_size
        )

        if args.json:
            if args.pretty:
                print(json.dumps(result, indent=2, ensure_ascii=False))
            else:
                print(json.dumps(result, ensure_ascii=False))
        else:
            print(client.format_results(result, search_type))

    except Exception as e:
        print(f"错误: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
