"""
URL to Markdown 模块

将网页 URL 转换为 LLM 友好的 Markdown 内容。

双引擎架构：
- 首选：Jina AI Reader API (快速、稳定、免费)
- 备选：Defuddle (本地运行、无速率限制、需 Node.js)

当 Jina 失败时自动切换到 Defuddle，确保高可用性。

Usage:
    from scripts.url_to_markdown import UrlToMarkdown, fetch_url_as_markdown

    # 简单调用（自动降级）
    result = fetch_url_as_markdown("https://example.com")

    # 高级用法
    client = UrlToMarkdown()
    result = client.fetch(
        url="https://example.com",
        with_images=True,
        timeout=30
    )

    # 指定引擎
    client_jina = UrlToMarkdown(prefer_engine="jina")  # 仅 Jina
    client_defuddle = UrlToMarkdown(prefer_engine="defuddle")  # 仅 Defuddle
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
