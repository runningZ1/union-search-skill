#!/usr/bin/env python3
"""
No API Key Search Engine Base Class
所有无需 API Key 的搜索引擎的基类
"""

import os
import sys
from pathlib import Path
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional

import requests
from lxml import html
from dotenv import load_dotenv

# 加载环境变量
script_dir = Path(__file__).parent.parent.parent
load_dotenv(script_dir / '.env')


class BaseNoApiKeySearchEngine(ABC):
    """无需 API Key 搜索引擎基类"""

    # 类变量 - 子类必须覆盖
    ENGINE_NAME: str = ""           # 引擎名称 (如 "baidu")
    ENGINE_DISPLAY_NAME: str = ""   # 显示名称 (如 "百度搜索")
    SEARCH_URL: str = ""            # 搜索 URL 模板
    REQUIRES_PROXY: bool = False    # 是否需要代理

    def __init__(self, proxy: Optional[str] = None):
        """
        初始化搜索引擎客户端

        Args:
            proxy: 代理地址 (可选)
        """
        self.proxy = proxy or os.getenv("NO_API_KEY_PROXY")
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        })
        if self.proxy:
            self.session.proxies = {'http': self.proxy, 'https': self.proxy}

    @abstractmethod
    def build_search_url(self, query: str, **kwargs) -> str:
        """构建搜索 URL"""
        pass

    @abstractmethod
    def parse_results(self, tree: html.HtmlElement) -> List[Dict[str, Any]]:
        """解析 HTML 搜索结果"""
        pass

    def search(
        self,
        query: str,
        max_results: int = 10,
        timeout: int = 15,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        执行搜索

        Args:
            query: 搜索关键词
            max_results: 最大结果数
            timeout: 请求超时时间 (秒)
            **kwargs: 引擎特定参数

        Returns:
            搜索结果列表，每项包含：title, href, body (可能还有其他引擎特定字段)
        """
        search_url = self.build_search_url(query, **kwargs)

        try:
            response = self.session.get(search_url, timeout=timeout)
            response.raise_for_status()

            tree = html.fromstring(response.content)
            results = self.parse_results(tree)

            return results[:max_results]

        except Exception as e:
            raise Exception(f"{self.ENGINE_DISPLAY_NAME} 搜索失败：{str(e)}")

    def format_results(self, results: List[Dict[str, Any]], query: str) -> str:
        """格式化搜索结果用于终端输出"""
        output = []
        output.append(f"🔍 {self.ENGINE_DISPLAY_NAME}: {query}")
        output.append(f"📊 找到 {len(results)} 条结果")
        output.append("")

        for i, item in enumerate(results, 1):
            title = item.get('title', '')
            href = item.get('href', '')
            body = item.get('body', '')

            output.append(f"[{i}] {title}")
            output.append(f"    🔗 {href}")
            if body:
                output.append(f"    📝 {body}")
            output.append("")

        return "\n".join(output)