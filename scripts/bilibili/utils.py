"""B 站搜索工具 - 公共工具函数"""

import re
from datetime import datetime
from typing import Optional


def clean_title(title: str) -> str:
    """清理 HTML 标签"""
    if not title:
        return "无标题"
    return re.sub(r'<[^>]+>', '', title).strip()


def format_number(num: Optional[int]) -> str:
    """格式化数字"""
    if num is None:
        return "0"
    if num >= 100000000:
        return f"{num / 100000000:.1f}亿"
    elif num >= 10000:
        return f"{num / 10000:.1f}万"
    return str(num)


def format_timestamp(ts: int) -> str:
    """格式化时间戳"""
    if not ts:
        return "未知"
    try:
        return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")
    except:
        return str(ts)


def print_header(title: str, width: int = 70):
    """打印标题头"""
    print(f"\n{'=' * width}\n{title}\n{'=' * width}")


def print_section(title: str, width: int = 70):
    """打印小节标题"""
    print(f"\n{'-' * width}\n{title}\n{'-' * width}")
