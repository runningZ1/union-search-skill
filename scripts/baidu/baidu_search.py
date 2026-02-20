#!/usr/bin/env python3
"""
Baidu Qianfan Search - 百度千帆搜索接口

使用百度千帆大模型平台的搜索 API 进行网页搜索。
API 文档: https://cloud.baidu.com/doc/qianfan/s/2mh4su4uy
"""

import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class BaiduSearch:
    """百度千帆搜索客户端"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        初始化搜索客户端
        
        Args:
            api_key: 百度千帆 API Key (bce-v3 格式)。如果为 None，则从环境变量 BAIDU_QIANFAN_API_KEY 加载。
        """
        self.api_key = api_key or os.getenv("BAIDU_QIANFAN_API_KEY")
        if not self.api_key:
            # 尝试加载 .env 文件以获取密钥
            self._load_env_from_file()
            self.api_key = self.api_key or os.getenv("BAIDU_QIANFAN_API_KEY")

        if not self.api_key:
            logger.error("未找到 BAIDU_QIANFAN_API_KEY。请在 .env 文件中设置或通过参数传入。")
            
        self.base_url = "https://qianfan.baidubce.com/v2/ai_search/web_search"
        self.session = requests.Session()

    def _load_env_from_file(self):
        """尝试加载 .env 文件"""
        env_path = Path(__file__).parent.parent.parent / ".env"
        if env_path.exists():
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, value = line.split("=", 1)
                        if key.strip() == "BAIDU_QIANFAN_API_KEY":
                            os.environ["BAIDU_QIANFAN_API_KEY"] = value.strip()
                            break

    def search(self, query: str, limit: int = 10, **kwargs) -> List[Dict[str, Any]]:
        """
        执行搜索
        
        Args:
            query: 搜索关键词
            limit: 返回结果数量 (API 限制 max 为 50)
            **kwargs: 其他 API 参数 (如 search_recency_filter)
            
        Returns:
            搜索结果列表
        """
        if not self.api_key:
            return []

        headers = {
            "X-Appbuilder-Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        # 构造请求体
        # 注意: 百度千帆搜索 API messages 只支持单轮，取最后一项
        payload = {
            "messages": [{"role": "user", "content": query}],
            "search_source": "baidu_search_v2",
            "resource_type_filter": [{"type": "web", "top_k": min(limit, 50)}]
        }
        
        # 合并其他可选参数
        if "search_recency_filter" in kwargs:
            payload["search_recency_filter"] = kwargs["search_recency_filter"]
            
        try:
            response = self.session.post(self.base_url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            return self._format_results(data)
        except Exception as e:
            logger.error(f"百度搜索请求失败: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"错误详情: {e.response.text}")
            return []

    def _format_results(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """格式化 API 返回的结果"""
        formatted_results = []
        references = data.get("references", [])
        
        for ref in references:
            formatted_results.append({
                "title": ref.get("title", ""),
                "url": ref.get("url", ""),
                "description": ref.get("content", ""),
                "date": ref.get("date", ""),
                "type": ref.get("type", "web"),
                "score": ref.get("rerank_score", 0)
            })
            
        return formatted_results

def format_output(results: List[Dict[str, Any]], query: str):
    """打印格式化结果"""
    print(f"\n=== 百度搜索结果: {query} ===\n")
    if not results:
        print("未找到结果或搜索失败。")
        return

    for i, res in enumerate(results, 1):
        print(f"{i}. {res['title']}")
        print(f"   链接: {res['url']}")
        desc = res['description'][:150].replace('\n', ' ') + "..." if res['description'] else "无描述"
        print(f"   描述: {desc}")
        if res.get('date'):
            print(f"   日期: {res['date']}")
        print()

def main():
    parser = argparse.ArgumentParser(description="百度千帆搜索 CLI")
    parser.add_argument("query", help="搜索关键词")
    parser.add_argument("-l", "--limit", type=int, default=10, help="返回结果数量 (默认: 10)")
    parser.add_argument("--json", action="store_true", help="以 JSON 格式输出")
    parser.add_argument("--key", help="手动指定 API Key")
    
    args = parser.parse_args()
    
    # 优先使用命令行传入的 Key，否则从环境变量或配置文件加载
    client = BaiduSearch(api_key=args.key)
    results = client.search(args.query, limit=args.limit)
    
    if args.json:
        print(json.dumps({"results": results, "query": args.query}, ensure_ascii=False, indent=2))
    else:
        format_output(results, args.query)

if __name__ == "__main__":
    main()
