#!/usr/bin/env python3
"""
小宇宙FM播客搜索工具
通过秘塔AI搜索API搜索小宇宙FM的播客内容

配置: 从环境变量或.env文件读取METASO_API_KEY
"""

import http.client
import json
import sys
import os
from pathlib import Path
from typing import Optional, Dict, Any
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


def get_api_key() -> str:
    """从环境变量获取API密钥"""
    api_key = os.getenv("METASO_API_KEY")
    if not api_key:
        raise ValueError(
            "未找到METASO_API_KEY环境变量\n"
            "请在.env文件中设置: METASO_API_KEY=your_key_here"
        )
    return api_key


def search_podcasts(
    query: str,
    size: int = 10,
    include_summary: bool = False,
    concise_snippet: bool = False,
    base_url: str = "metaso.cn",
    timeout: int = 30
) -> Dict[str, Any]:
    """
    搜索小宇宙FM播客

    Args:
        query: 搜索关键词
        size: 返回结果数量
        include_summary: 是否包含AI摘要
        concise_snippet: 是否使用简洁摘要
        base_url: API基础URL
        timeout: 请求超时时间

    Returns:
        搜索结果字典
    """
    api_key = get_api_key()

    # 构建请求体
    payload = {
        "q": query,
        "scope": "podcast",
        "includeSummary": include_summary,
        "size": str(size),
        "conciseSnippet": concise_snippet
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    # 发送请求
    conn = http.client.HTTPSConnection(base_url, timeout=timeout)
    try:
        conn.request("POST", "/api/v1/search", json.dumps(payload), headers)
        res = conn.getresponse()
        data = res.read()

        if res.status != 200:
            raise Exception(f"API请求失败: HTTP {res.status} - {data.decode('utf-8')}")

        return json.loads(data.decode("utf-8"))
    finally:
        conn.close()


def format_result(result: Dict[str, Any]) -> str:
    """格式化单个搜索结果"""
    title = result.get("title", "无标题")
    link = result.get("link", "")
    snippet = result.get("snippet", "无摘要")
    authors = result.get("authors", [])
    date = result.get("date", "")
    duration = result.get("duration", "")
    score = result.get("score", "")

    # 转换时长为可读格式
    if duration:
        try:
            duration_sec = int(duration)
            minutes = duration_sec // 60
            seconds = duration_sec % 60
            duration_str = f"{minutes}分{seconds}秒" if seconds else f"{minutes}分钟"
        except:
            duration_str = duration
    else:
        duration_str = "未知"

    author_str = ", ".join(authors) if authors else "佚名"

    output = f"""
## {title}
- **主播**: {author_str}
- **发布日期**: {date}
- **时长**: {duration_str}
- **相关度**: {score}
- **链接**: {link}

{snippet}
---"""
    return output


def format_results(response: Dict[str, Any], show_credits: bool = True) -> str:
    """格式化所有搜索结果"""
    podcasts = response.get("podcasts", [])
    total = response.get("total", 0)
    credits = response.get("credits", 0)
    search_params = response.get("searchParameters", {})

    output = f"# 搜索结果: \"{search_params.get('q', '')}\"\n"
    output += f"共找到 {total} 个相关播客\n"

    if show_credits:
        output += f"本次搜索消耗积分: {credits}\n"

    output += "\n" + "="*50 + "\n"

    for podcast in podcasts:
        output += format_result(podcast)

    return output


def search_and_format(
    query: str,
    size: int = 10,
    include_summary: bool = False,
    concise_snippet: bool = False,
    output_format: str = "text"
) -> str:
    """
    搜索并格式化输出

    Args:
        query: 搜索关键词
        size: 返回结果数量
        include_summary: 是否包含AI摘要
        concise_snippet: 是否使用简洁摘要
        output_format: 输出格式 (text/json)

    Returns:
        格式化后的搜索结果
    """
    result = search_podcasts(
        query=query,
        size=size,
        include_summary=include_summary,
        concise_snippet=concise_snippet
    )

    if output_format == "json":
        return json.dumps(result, ensure_ascii=False, indent=2)
    else:
        return format_results(result)


def main():
    """命令行入口"""
    import argparse

    parser = argparse.ArgumentParser(
        description="小宇宙FM播客搜索工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python xiaoyuzhou_search.py "人工智能"
  python xiaoyuzhou_search.py "创业故事" --size 5
  python xiaoyuzhou_search.py "心理学" --json > result.json
        """
    )

    parser.add_argument("query", help="搜索关键词")
    parser.add_argument("--size", "-s", type=int, default=10, help="返回结果数量 (默认: 10)")
    parser.add_argument("--json", "-j", action="store_true", help="以JSON格式输出")
    parser.add_argument("--summary", action="store_true", help="包含AI摘要")
    parser.add_argument("--concise", "-c", action="store_true", help="使用简洁摘要")

    args = parser.parse_args()

    try:
        output = search_and_format(
            query=args.query,
            size=args.size,
            include_summary=args.summary,
            concise_snippet=args.concise,
            output_format="json" if args.json else "text"
        )
        print(output)
    except ValueError as e:
        print(f"错误: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"搜索失败: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
