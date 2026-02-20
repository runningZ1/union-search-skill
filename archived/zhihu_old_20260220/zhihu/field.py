"""
知乎搜索模块 - 枚举定义

定义搜索类型、排序方式等枚举类型
"""
from enum import Enum


class SearchType(Enum):
    """搜索类型枚举"""
    CONTENT = "content"      # 综合搜索（默认），包含问题和回答
    ARTICLE = "article"      # 文章搜索
    PEOPLE = "people"        # 用户搜索


class SearchSort(Enum):
    """排序方式枚举"""
    DEFAULT = "default"      # 默认排序
    RELEVANCE = "relevance"  # 相关性排序
    TIME = "time"            # 时间排序（最新）
    VOTES = "vote"           # 点赞数排序（热门）


class SearchTimeRange(Enum):
    """搜索时间范围枚举"""
    ALL = ""                 # 全部时间
    DAY = "day"              # 一天内
    WEEK = "week"            # 一周内
    MONTH = "month"          # 一月内
    YEAR = "year"            # 一年内


class ContentType(Enum):
    """内容类型枚举"""
    QUESTION = "question"    # 问题
    ANSWER = "answer"        # 回答
    ARTICLE = "article"      # 文章
    COLUMN = "column"        # 专栏
