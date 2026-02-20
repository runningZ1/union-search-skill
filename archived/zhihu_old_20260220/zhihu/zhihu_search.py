#!/usr/bin/env python3
"""
知乎搜索模块 - 主入口脚本

命令行工具，用于搜索知乎内容并输出结果
"""
import argparse
import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from loguru import logger

from scripts.zhihu.field import SearchType, SearchSort
from scripts.zhihu.core import ZhihuSearchClient
from scripts.zhihu.exception import ZhihuSearchError


# 配置日志
logger.remove()
logger.add(sys.stderr, level="INFO")


def format_text_output(results: List[Dict[str, Any]], keyword: str) -> str:
    """格式化文本终端输出

    Args:
        results: 搜索结果列表
        keyword: 搜索关键词

    Returns:
        格式化的文本字符串
    """
    lines = []
    lines.append("=" * 80)
    lines.append(f"知乎搜索结果 - 关键词: {keyword}")
    lines.append(f"找到 {len(results)} 条结果")
    lines.append("=" * 80)
    lines.append("")

    for result in results:
        rank = result.get("rank", 0)
        title = result.get("title", "无标题")
        content_type = result.get("type", "unknown")
        author = result.get("author", {}).get("name", "匿名")
        url = result.get("url", "")
        stats = result.get("stats", {})
        votes = stats.get("votes", 0)
        comments = stats.get("comments", 0)
        created = result.get("created_at", "")
        excerpt = result.get("excerpt", "")

        lines.append(f"[{rank}] {title}")
        lines.append(f"    类型: {content_type} | 作者: {author}")
        if votes > 0:
            lines.append(f"    赞同: {votes} | 评论: {comments}")
        if created:
            lines.append(f"    发布于: {created}")
        if excerpt:
            lines.append(f"    摘要: {excerpt}")
        lines.append(f"    链接: {url}")
        lines.append("")

    lines.append("=" * 80)
    return "\n".join(lines)


def format_json_output(results: List[Dict[str, Any]], pretty: bool = True) -> str:
    """格式化 JSON 输出

    Args:
        results: 搜索结果列表
        pretty: 是否格式化输出

    Returns:
        JSON 字符串
    """
    if pretty:
        return json.dumps(results, ensure_ascii=False, indent=2)
    else:
        return json.dumps(results, ensure_ascii=False)


def format_markdown_output(results: List[Dict[str, Any]], keyword: str) -> str:
    """格式化 Markdown 输出

    Args:
        results: 搜索结果列表
        keyword: 搜索关键词

    Returns:
        Markdown 字符串
    """
    lines = []
    lines.append(f"# 知乎搜索结果: {keyword}")
    lines.append("")
    lines.append(f"**搜索时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"**结果数量**: {len(results)}")
    lines.append("")
    lines.append("---")
    lines.append("")

    for result in results:
        rank = result.get("rank", 0)
        title = result.get("title", "无标题")
        content_type = result.get("type", "unknown")
        author = result.get("author", {})
        author_name = author.get("name", "匿名")
        author_url = author.get("url", "")
        url = result.get("url", "")
        stats = result.get("stats", {})
        votes = stats.get("votes", 0)
        comments = stats.get("comments", 0)
        created = result.get("created_at", "")
        excerpt = result.get("excerpt", "")
        content = result.get("full_content", result.get("content", ""))

        # 标题和排名
        lines.append(f"## {rank}. {title}")

        # 元数据
        lines.append("")
        lines.append(f"- **类型**: {content_type}")
        if author_url:
            lines.append(f"- **作者**: [{author_name}]({author_url})")
        else:
            lines.append(f"- **作者**: {author_name}")
        if votes > 0:
            lines.append(f"- **赞同**: {votes} | **评论**: {comments}")
        if created:
            lines.append(f"- **发布时间**: {created}")

        # 摘要
        if excerpt:
            lines.append("")
            lines.append(f"> {excerpt}")

        # 完整内容（如果有）
        if content and content != excerpt:
            lines.append("")
            lines.append("### 详细内容")
            lines.append("")
            # 简单处理：将 HTML 内容转换为纯文本（实际应用中可能需要更复杂的处理）
            # 这里只做简单替换
            import re
            # 移除 HTML 标签
            clean_content = re.sub(r'<[^>]+>', '', content)
            # 限制长度
            if len(clean_content) > 2000:
                clean_content = clean_content[:2000] + "..."
            lines.append(clean_content)

        # 链接
        lines.append("")
        lines.append(f"**链接**: [{url}]({url})")

        # 分隔线
        lines.append("")
        lines.append("---")
        lines.append("")

    return "\n".join(lines)


async def main() -> int:
    """主函数

    Returns:
        退出码（0 表示成功）
    """
    parser = argparse.ArgumentParser(
        description="知乎搜索工具 - 基于 Playwright 的知乎搜索信息获取",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s "Python 异步编程"
  %(prog)s "机器学习" --type article --limit 20
  %(prog)s "深度学习" --sort votes --markdown -o output.md
  %(prog)s "LLM" --full-content --with-comments --limit 5
        """
    )

    # 位置参数
    parser.add_argument("keyword", help="搜索关键词")

    # 搜索参数
    parser.add_argument(
        "--type",
        choices=["content", "article", "people"],
        default="content",
        help="搜索类型 (默认: content)"
    )
    parser.add_argument(
        "--sort",
        choices=["default", "relevance", "time", "votes"],
        default="default",
        help="排序方式 (默认: default)"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="结果数量 (默认: 10)"
    )

    # 内容获取参数
    parser.add_argument(
        "--full-content",
        action="store_true",
        help="获取完整内容（需要额外请求）"
    )
    parser.add_argument(
        "--with-comments",
        action="store_true",
        help="包含评论数据（需要额外请求）"
    )

    # 输出格式参数
    parser.add_argument(
        "--json",
        action="store_true",
        help="JSON 格式输出"
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="格式化 JSON 输出（与 --json 一起使用）"
    )
    parser.add_argument(
        "--markdown",
        action="store_true",
        help="Markdown 格式输出"
    )
    parser.add_argument(
        "-o", "--output",
        help="输出文件路径"
    )

    # 其他参数
    parser.add_argument(
        "--save-raw",
        action="store_true",
        help="保存原始 API 响应"
    )
    parser.add_argument(
        "--no-headless",
        action="store_true",
        help="显示浏览器窗口（调试用）"
    )

    args = parser.parse_args()

    # 加载环境变量
    from scripts.zhihu.core import load_env_file
    load_env_file()

    # 确定搜索类型枚举
    search_type_map = {
        "content": SearchType.CONTENT,
        "article": SearchType.ARTICLE,
        "people": SearchType.PEOPLE,
    }
    search_type = search_type_map[args.type]

    # 确定排序枚举
    sort_map = {
        "default": SearchSort.DEFAULT,
        "relevance": SearchSort.RELEVANCE,
        "time": SearchSort.TIME,
        "votes": SearchSort.VOTES,
    }
    sort_type = sort_map[args.sort]

    headless = not args.no_headless

    try:
        logger.info(f"开始搜索: {args.keyword}")

        async with ZhihuSearchClient(headless=headless) as client:
            results = await client.search(
                keyword=args.keyword,
                search_type=search_type,
                limit=args.limit,
                sort=sort_type,
                full_content=args.full_content,
                include_comments=args.with_comments,
            )

        if not results:
            logger.warning("未找到搜索结果")
            return 0

        # 确定输出格式
        if args.json:
            output = format_json_output(results, pretty=args.pretty)
        elif args.markdown:
            output = format_markdown_output(results, args.keyword)
        else:
            output = format_text_output(results, args.keyword)

        # 输出到文件或终端
        if args.output:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(output)
            logger.info(f"结果已保存到: {args.output}")
        else:
            print(output)

        # 保存原始响应（如果需要）
        if args.save_raw:
            raw_dir = Path(__file__).parent / "responses"
            raw_dir.mkdir(exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            raw_file = raw_dir / f"{args.keyword}_{timestamp}.json"
            with open(raw_file, "w", encoding="utf-8") as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            logger.info(f"原始响应已保存到: {raw_file}")

        return 0

    except ZhihuSearchError as e:
        logger.error(f"搜索失败: {e}")
        return 1
    except KeyboardInterrupt:
        logger.info("用户中断")
        return 130
    except Exception as e:
        logger.exception(f"发生未预期的错误: {e}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
