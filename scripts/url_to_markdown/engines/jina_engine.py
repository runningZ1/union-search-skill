#!/usr/bin/env python3
"""
Jina AI Reader API 引擎

Jina AI 是首选引擎，快速、稳定，免费版无需 API Key。
"""

import os
import sys
from typing import Optional, Dict, Any, List
from urllib.parse import urlparse
import requests

# Jina Reader API 基础 URL
JINA_READER_BASE_URL = "https://r.jina.ai"


class JinaEngine:
    """
    Jina AI Reader API 客户端

    将网页 URL 转换为 Markdown 格式。
    官方文档：https://jina.ai/reader
    """

    def __init__(self, api_key: Optional[str] = None, timeout: int = 30):
        """
        初始化 JinaEngine

        Args:
            api_key: Jina API Key (可选，免费版不需要)
            timeout: 请求超时时间 (秒)
        """
        self.api_key = api_key or os.getenv("JINA_API_KEY", "")
        self.timeout = timeout
        self.base_url = JINA_READER_BASE_URL

    def _build_headers(self, extra_headers: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        """构建请求头"""
        headers = {
            "Accept": "text/plain, text/markdown",
            "User-Agent": "Union-Search-Skill/2.0",
        }

        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        if extra_headers:
            headers.update(extra_headers)

        return headers

    def _validate_url(self, url: str) -> str:
        """验证并规范化 URL"""
        if not url:
            raise ValueError("URL 不能为空")

        # 如果 URL 没有 scheme，添加 https://
        parsed = urlparse(url)
        if not parsed.scheme:
            url = f"https://{url}"

        # 验证 URL 格式
        parsed = urlparse(url)
        if not parsed.netloc:
            raise ValueError(f"无效的 URL: {url}")

        return url

    def fetch(
        self,
        url: str,
        with_images: bool = False,
        with_links: bool = False,
        with_generated_alt: bool = False,
        target_selector: Optional[str] = None,
        wait_for_selector: Optional[str] = None,
        timeout: Optional[int] = None,
        no_cache: bool = False,
        return_json: bool = False,
    ) -> Dict[str, Any]:
        """
        获取 URL 对应的 Markdown 内容

        Args:
            url: 要抓取的 URL
            with_images: 是否包含图片摘要
            with_links: 是否包含链接摘要
            with_generated_alt: 是否生成图片 alt 文本
            target_selector: CSS 选择器，指定要提取的内容区域
            wait_for_selector: 等待指定元素渲染完成
            timeout: 请求超时时间 (秒)
            no_cache: 是否绕过缓存
            return_json: 是否返回 JSON 格式

        Returns:
            包含 title, content, url 等字段的字典
        """
        url = self._validate_url(url)
        request_timeout = timeout or self.timeout

        # 构建请求头
        extra_headers = {}
        if with_generated_alt:
            extra_headers["X-With-Generated-Alt"] = "true"
        if target_selector:
            extra_headers["X-Target-Selector"] = target_selector
        if wait_for_selector:
            extra_headers["X-Wait-For-Selector"] = wait_for_selector
        if no_cache:
            extra_headers["X-No-Cache"] = "true"

        # 设置 Accept header
        if return_json:
            extra_headers["Accept"] = "application/json"
        else:
            extra_headers["Accept"] = "text/markdown"

        headers = self._build_headers(extra_headers)

        # 发送请求
        response = requests.get(
            f"{self.base_url}/{url}",
            headers=headers,
            timeout=request_timeout,
        )
        response.raise_for_status()

        if return_json:
            data = response.json()
            # Jina API 返回的 JSON 格式
            if isinstance(data, dict) and "data" in data:
                return {
                    "url": data.get("data", {}).get("url", url),
                    "title": data.get("data", {}).get("title", ""),
                    "content": data.get("data", {}).get("content", ""),
                    "description": data.get("data", {}).get("description", ""),
                    "markdown": data.get("data", {}).get("content", ""),
                    "metadata": data.get("data", {}).get("metadata", {}),
                    "usage": data.get("data", {}).get("usage", {}),
                    "warning": data.get("data", {}).get("warning", ""),
                }
            return data

        # 解析响应
        content = response.text

        # 尝试从响应中提取标题
        title = ""
        lines = content.split("\n")
        if lines and lines[0].startswith("# "):
            title = lines[0][2:].strip()
            content = "\n".join(lines[1:]).strip()

        return {
            "url": url,
            "title": title,
            "content": content,
            "markdown": content,
        }

    def fetch_batch(
        self,
        urls: List[str],
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        批量获取多个 URL 的 Markdown 内容

        Args:
            urls: URL 列表
            **kwargs: fetch() 方法的其他参数

        Returns:
            结果列表
        """
        results = []
        for url in urls:
            try:
                result = self.fetch(url, **kwargs)
                results.append(result)
            except Exception as e:
                results.append({
                    "url": url,
                    "error": str(e),
                    "content": None,
                })
        return results
