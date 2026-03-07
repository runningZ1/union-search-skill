"""
URL to Markdown 模块

将网页URL转换为LLM友好的Markdown内容。
基于Jina AI Reader API实现。

Usage:
    from scripts.url_to_markdown import UrlToMarkdown, fetch_url_as_markdown

    # 简单调用
    result = fetch_url_as_markdown("https://example.com")

    # 高级用法
    client = UrlToMarkdown()
    result = client.fetch(
        url="https://example.com",
        with_images=True,
        timeout=30
    )
"""

from .url_to_markdown import (
    UrlToMarkdown,
    fetch_url_as_markdown,
    __version__,
    __author__,
)

__all__ = [
    "UrlToMarkdown",
    "fetch_url_as_markdown",
    "__version__",
    "__author__",
]
