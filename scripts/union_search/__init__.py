"""
Union Search - 统一多平台搜索模块

提供跨多个平台的统一搜索接口，支持并发搜索和结果汇总。

Version: 1.0.0
Status: Production Ready
License: MIT
"""

from .union_search import (
    PLATFORM_MODULES,
    PLATFORM_GROUPS,
    search_platform,
    union_search,
    format_markdown,
    format_json,
    list_platforms,
    __version__,
    __author__,
)

__all__ = [
    "PLATFORM_MODULES",
    "PLATFORM_GROUPS",
    "search_platform",
    "union_search",
    "format_markdown",
    "format_json",
    "list_platforms",
    "__version__",
    "__author__",
]
