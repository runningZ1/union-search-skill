"""
B 站搜索工具包
==============

基于 bilibili-api 的 B 站数据获取工具集，支持视频搜索、用户搜索、
热搜榜、搜索建议以及视频数据和评论获取。

核心模块
--------
- search: 视频/用户/热搜/搜索建议
- get_video_full_data: 视频完整数据（无需登录）
- get_video_comments: 视频评论（需要登录）

工具函数
--------
- clean_title: 清理 HTML 标签
- format_number: 格式化数字（万/亿）
- format_timestamp: 格式化时间戳
- print_header: 打印标题头

使用示例
--------
>>> from bilibili import search
>>> async def main():
...     searcher = search.VideoSearcher()
...     await searcher.search("Python 教程", page_size=10)
...     searcher.print_results()
...     searcher.export()
"""

from . import search
from . import get_video_full_data
from . import get_video_comments
from .utils import clean_title, format_number, format_timestamp, print_header, print_section

__all__ = [
    # 模块
    "search",
    "get_video_full_data",
    "get_video_comments",
    # 工具函数
    "clean_title",
    "format_number",
    "format_timestamp",
    "print_header",
    "print_section",
    # 搜索器类
    "VideoSearcher",
    "UserSearcher",
    "HotSearcher",
    "SuggestSearcher",
    "CommentFetcher",
]

# 搜索器类快捷导入
VideoSearcher = search.VideoSearcher
UserSearcher = search.UserSearcher
HotSearcher = search.HotSearcher
SuggestSearcher = search.SuggestSearcher
CommentFetcher = get_video_comments.CommentFetcher
