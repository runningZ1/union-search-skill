"""
知乎搜索模块

基于 Playwright 的知乎搜索信息获取模块
"""

from .field import SearchType, SearchSort, SearchTimeRange, ContentType
from .exception import (
    ZhihuSearchError,
    ZhihuCookieError,
    ZhihuAuthError,
    ZhihuRateLimitError,
    ZhihuForbiddenError,
    ZhihuNotFoundError,
    ZhihuParseError,
    ZhihuNetworkError,
)
from .core import ZhihuSearchClient, search_zhihu
from .client import ZhihuAPIClient
from .extractor import ZhihuExtractor
from .signature import ZhihuSignature
from .fetcher import ZhihuContentFetcher, enrich_with_full_content

__all__ = [
    # 枚举
    "SearchType",
    "SearchSort",
    "SearchTimeRange",
    "ContentType",
    # 异常
    "ZhihuSearchError",
    "ZhihuCookieError",
    "ZhihuAuthError",
    "ZhihuRateLimitError",
    "ZhihuForbiddenError",
    "ZhihuNotFoundError",
    "ZhihuParseError",
    "ZhihuNetworkError",
    # 核心类和函数
    "ZhihuSearchClient",
    "search_zhihu",
    "ZhihuAPIClient",
    "ZhihuExtractor",
    "ZhihuSignature",
    "ZhihuContentFetcher",
    "enrich_with_full_content",
]

__version__ = "1.0.0"
