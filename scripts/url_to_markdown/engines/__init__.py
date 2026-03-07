#!/usr/bin/env python3
"""
URL to Markdown 引擎模块

提供 Jina AI 和 Defuddle 两种引擎，优先使用 Jina，失败时自动切换到 Defuddle。
"""

from .jina_engine import JinaEngine
from .defuddle_engine import DefuddleEngine
from typing import Dict, Any, Optional, Tuple

__version__ = "2.0.0"
__author__ = "Claude"

__all__ = ["UrlToMarkdown", "fetch_url_as_markdown", "JinaEngine", "DefuddleEngine"]


class UrlToMarkdown:
    """
    双引擎 URL 转 Markdown 客户端

    优先使用 Jina AI API（快速、无本地依赖），
    当 Jina 失败时自动切换到 Defuddle（本地运行、无速率限制）。
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        timeout: int = 30,
        prefer_engine: str = "auto",
        enable_fallback: bool = True,
    ):
        """
        初始化 UrlToMarkdown 客户端

        Args:
            api_key: Jina API Key (可选，免费版不需要)
            timeout: 请求超时时间 (秒)
            prefer_engine: 首选引擎 ("jina", "defuddle", "auto")
            enable_fallback: 是否启用自动降级
        """
        self.jina = JinaEngine(api_key=api_key, timeout=timeout)
        self.defuddle = DefuddleEngine(timeout=timeout)
        self.prefer_engine = prefer_engine
        self.enable_fallback = enable_fallback
        self.timeout = timeout

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
        request_timeout = timeout or self.timeout
        engine_used = "unknown"
        fallback_used = False

        # 确定首选引擎
        if self.prefer_engine == "defuddle":
            engines = [("defuddle", self.defuddle)]
            if self.enable_fallback:
                engines.append(("jina", self.jina))
        elif self.prefer_engine == "jina":
            engines = [("jina", self.jina)]
            if self.enable_fallback:
                engines.append(("defuddle", self.defuddle))
        else:  # auto - 优先 Jina
            engines = [("jina", self.jina)]
            if self.enable_fallback:
                engines.append(("defuddle", self.defuddle))

        last_error = None

        for engine_name, engine in engines:
            try:
                # Jina 引擎支持更多参数
                if engine_name == "jina":
                    result = self.jina.fetch(
                        url=url,
                        with_images=with_images,
                        with_links=with_links,
                        with_generated_alt=with_generated_alt,
                        target_selector=target_selector,
                        wait_for_selector=wait_for_selector,
                        timeout=request_timeout,
                        no_cache=no_cache,
                        return_json=return_json,
                    )
                else:
                    # Defuddle 引擎参数较少
                    result = self.defuddle.fetch(
                        url=url,
                        markdown=True,
                        json_output=return_json,
                        timeout=request_timeout,
                    )

                # 添加引擎使用信息
                result["_engine_used"] = engine_name
                result["_fallback_used"] = fallback_used
                return result

            except Exception as e:
                last_error = e
                fallback_used = True
                # 继续尝试下一个引擎
                continue

        # 所有引擎都失败
        raise RuntimeError(
            f"All engines failed. Last error from {engine_name}: {last_error}"
        )

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


def fetch_url_as_markdown(
    url: str,
    with_images: bool = False,
    with_links: bool = False,
    timeout: int = 30,
    prefer_engine: str = "auto",
) -> str:
    """
    便捷函数：直接将 URL 转换为 Markdown 字符串

    Args:
        url: 要抓取的 URL
        with_images: 是否包含图片摘要
        with_links: 是否包含链接摘要
        timeout: 请求超时时间
        prefer_engine: 首选引擎 ("jina", "defuddle", "auto")

    Returns:
        Markdown 格式的内容字符串
    """
    client = UrlToMarkdown(timeout=timeout, prefer_engine=prefer_engine)
    result = client.fetch(
        url,
        with_images=with_images,
        with_links=with_links,
    )
    return result.get("content", "")
