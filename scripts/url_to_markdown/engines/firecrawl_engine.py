#!/usr/bin/env python3
"""
Firecrawl 引擎

Firecrawl 是一个强大的网页爬取和内容提取引擎，支持 Markdown 格式输出。
作为 Jina AI 和 Defuddle 的备选引擎使用。
"""

import os
import sys
import json
import logging
from typing import Optional, Dict, Any, List

# 配置日志
logger = logging.getLogger(__name__)

class FirecrawlEngine:
    """
    Firecrawl API 引擎
    """

    def __init__(self, api_key: Optional[str] = None, timeout: int = 60):
        """
        初始化 FirecrawlEngine

        Args:
            api_key: API 密钥，如未提供则从环境变量 FIRECRAWL_API_KEY 获取
            timeout: 请求超时时间 (秒)
        """
        self.api_key = api_key or os.environ.get("FIRECRAWL_API_KEY")
        self.timeout = timeout
        self.client = None

        if not self.api_key:
            logger.warning("FIRECRAWL_API_KEY not set. Firecrawl engine will be unavailable.")
            return

        try:
            from firecrawl import FirecrawlApp
            self.client = FirecrawlApp(api_key=self.api_key)
        except ImportError:
            logger.warning("firecrawl-py not installed. Run 'pip install firecrawl-py'")

    def fetch(
        self,
        url: str,
        markdown: bool = True,
        json_output: bool = False,
        timeout: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        使用 Firecrawl 提取网页内容

        Args:
            url: 要提取的网页 URL
            markdown: 是否输出 Markdown 格式
            json_output: 是否输出 JSON 格式（包含元数据）
            timeout: 请求超时时间 (秒)

        Returns:
            包含 title, content, url 等字段的字典
        """
        if not self.client:
            raise RuntimeError("Firecrawl client not initialized (check API key and library)")

        try:
            params = {
                "formats": ["markdown"] if markdown else ["html"],
            }
            
            # Scrape the URL
            result = self.client.scrape_url(url, params=params)
            
            if not result or "markdown" not in result:
                 raise RuntimeError("Firecrawl returned no content")

            return {
                "url": url,
                "title": result.get("metadata", {}).get("title", ""),
                "content": result.get("markdown", ""),
                "markdown": result.get("markdown", ""),
                "description": result.get("metadata", {}).get("description", ""),
                "metadata": result.get("metadata", {}),
                "success": True
            }

        except Exception as e:
            raise RuntimeError(f"Firecrawl failed: {e}")

    def fetch_batch(self, urls: List[str], **kwargs) -> List[Dict[str, Any]]:
        """批量获取内容"""
        results = []
        for url in urls:
            try:
                results.append(self.fetch(url, **kwargs))
            except Exception as e:
                results.append({"url": url, "error": str(e), "success": False})
        return results
