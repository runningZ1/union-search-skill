#!/usr/bin/env python3
"""
RSS Feed Search Tool
支持从多个 RSS 源搜索和过滤内容
"""
import argparse
import json
import os
import re
import sys
from datetime import datetime
from typing import List, Dict, Any
import feedparser


DEFAULT_RSS_FEEDS = [
    "http://feedmaker.kindle4rss.com/feeds/AI_era.weixin.xml",
]


def load_env_file(path: str) -> None:
    """加载环境变量文件"""
    if not path or not os.path.exists(path):
        return

    with open(path, "r", encoding="utf-8") as f:
        for raw_line in f:
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue

            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip()

            if key and key not in os.environ:
                os.environ[key] = value


def _env_file_from_argv(argv: List[str]) -> str:
    """从命令行参数中提取 env 文件路径"""
    for i, arg in enumerate(argv):
        if arg == "--env-file" and i + 1 < len(argv):
            return argv[i + 1]
        if arg.startswith("--env-file="):
            return arg.split("=", 1)[1]
    return ".env"


def parse_args() -> argparse.Namespace:
    """解析命令行参数"""
    examples = (
        "使用示例:\n"
        "  python rss_search.py \"AI\" --feed http://example.com/feed.xml\n"
        "  python rss_search.py \"机器学习\" --limit 5 --json\n"
        "  python rss_search.py \"GPT\" --markdown --full\n"
        "  python rss_search.py \"技术\" --feeds feeds.txt -o results.json\n"
    )
    parser = argparse.ArgumentParser(
        description="RSS Feed 搜索工具 - 从 RSS 源中搜索和过滤内容",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog=examples,
    )
    parser.add_argument("--env-file", default=_env_file_from_argv(sys.argv), help="环境变量文件路径")
    parser.add_argument("query", nargs="?", default="", help="搜索关键词（可选，留空则返回所有条目）")
    parser.add_argument("--feed", help="单个 RSS feed URL")
    parser.add_argument("--feeds", help="包含多个 RSS feed URL 的文件（每行一个）")
    parser.add_argument("-l", "--limit", type=int, default=10, help="返回结果数量限制（默认: 10）")
    parser.add_argument("--json", action="store_true", help="输出 JSON 格式")
    parser.add_argument("--pretty", action="store_true", help="美化 JSON 输出")
    parser.add_argument("--markdown", action="store_true", help="输出 Markdown 格式")
    parser.add_argument("--full", action="store_true", help="包含完整内容和详细信息")
    parser.add_argument("-o", "--output", help="输出到文件")
    parser.add_argument("--timeout", type=int, default=30, help="请求超时时间（秒，默认: 30）")
    parser.add_argument("--case-sensitive", action="store_true", help="区分大小写搜索")
    return parser.parse_args()


def load_feeds_from_file(filepath: str) -> List[str]:
    """从文件加载 RSS feed URLs"""
    feeds = []
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    feeds.append(line)
    except Exception as e:
        print(f"读取 feeds 文件失败: {e}", file=sys.stderr)
    return feeds


def fetch_rss_feed(url: str, timeout: int = 30) -> Dict[str, Any]:
    """获取并解析 RSS feed"""
    try:
        # 设置 User-Agent 避免被某些网站拒绝
        feedparser.USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        feed = feedparser.parse(url)

        if feed.bozo:
            # bozo=1 表示解析有问题，但可能仍有部分数据
            print(f"警告: RSS feed 解析有问题 ({url}): {feed.get('bozo_exception', 'Unknown error')}", file=sys.stderr)

        return {
            "url": url,
            "title": feed.feed.get("title", "Unknown"),
            "description": feed.feed.get("description", ""),
            "link": feed.feed.get("link", ""),
            "entries": feed.entries,
            "status": "success"
        }
    except Exception as e:
        return {
            "url": url,
            "status": "error",
            "error": str(e),
            "entries": []
        }


def _extract_content(entry: Any) -> str:
    """提取条目的内容"""
    if "content" in entry and entry.content:
        return entry.content[0].get("value", "")
    return ""


def _extract_weixin_link(summary: str, default_link: str) -> str:
    """从摘要中提取微信公众号原文链接

    优先级：
    1. 如果 default_link 是 mp.weixin.qq.com 开头，直接使用
    2. 否则从 summary 中查找 mp.weixin.qq.com 链接
    """
    # 默认链接已经是微信链接，直接使用
    if 'mp.weixin.qq.com' in default_link:
        # 将 http 转换为 https
        return default_link.replace('http://', 'https://')

    # 从摘要中查找微信链接
    urls = re.findall(r'https?://[^\s<>\"\'\)]+', summary)
    for url in urls:
        if 'mp.weixin.qq.com' in url:
            return url.replace('http://', 'https://')

    # 没有找到微信链接，返回原始链接
    return default_link


def _format_published_date(entry: Any) -> str:
    """格式化发布时间"""
    published = entry.get("published", entry.get("updated", ""))
    published_parsed = entry.get("published_parsed", entry.get("updated_parsed", None))

    if published_parsed:
        try:
            return datetime(*published_parsed[:6]).strftime("%Y-%m-%d %H:%M:%S")
        except (TypeError, ValueError):
            pass

    return published


def _matches_query(title: str, summary: str, content: str, query: str, case_sensitive: bool) -> bool:
    """检查条目是否匹配查询"""
    if not query:
        return True

    search_text = f"{title} {summary} {content}"
    if case_sensitive:
        return query in search_text
    return query.lower() in search_text.lower()


def search_entries(entries: List[Any], query: str, case_sensitive: bool = False) -> List[Dict[str, Any]]:
    """在 RSS 条目中搜索关键词"""
    results = []

    for entry in entries:
        title = entry.get("title", "")
        summary = entry.get("summary", entry.get("description", ""))
        content = _extract_content(entry)

        if not _matches_query(title, summary, content, query, case_sensitive):
            continue

        # 提取微信公众号原文链接
        original_link = entry.get("link", "")
        weixin_link = _extract_weixin_link(summary, original_link)

        results.append({
            "title": title,
            "link": original_link,  # 原始RSS链接
            "weixin_link": weixin_link,  # 微信公众号原文链接（用于weixin-spider下载）
            "published": _format_published_date(entry),
            "author": entry.get("author", ""),
            "summary": summary,
            "content": content,
            "tags": [tag.get("term", "") for tag in entry.get("tags", [])],
        })

    return results


def _format_header(query: str, result_count: int) -> List[str]:
    """格式化输出头部"""
    header = "搜索关键词: " + query if query else "RSS Feed 内容"
    return [header, f"找到 {result_count} 条结果", ""]


def _add_full_details(lines: List[str], item: Dict[str, Any]) -> None:
    """添加完整详情到输出行"""
    if item['summary']:
        lines.append(f"  摘要: {item['summary'][:200]}...")
    if item['tags']:
        lines.append(f"  标签: {', '.join(item['tags'])}")
    if item['content'] and item['content'] != item['summary']:
        lines.append(f"  内容: {item['content'][:300]}...")


def format_text(results: List[Dict[str, Any]], query: str, full: bool = False) -> str:
    """格式化为纯文本输出"""
    lines = _format_header(query, len(results))

    for i, item in enumerate(results, 1):
        lines.append(f"[{i}] {item['title']}")
        lines.append(f"  链接: {item['link']}")
        lines.append(f"  发布时间: {item['published']}")

        if item['author']:
            lines.append(f"  作者: {item['author']}")

        if full:
            _add_full_details(lines, item)

        lines.append("")

    return "\n".join(lines)


def _add_markdown_full_details(lines: List[str], item: Dict[str, Any]) -> None:
    """添加完整详情到 Markdown 输出行"""
    if item['summary']:
        lines.append(f"- **摘要**: {item['summary']}")
    if item['tags']:
        lines.append(f"- **标签**: {', '.join(item['tags'])}")
    if item['content'] and item['content'] != item['summary']:
        lines.append(f"\n**内容**:\n\n{item['content']}\n")


def format_markdown(results: List[Dict[str, Any]], query: str, full: bool = False) -> str:
    """格式化为 Markdown 输出"""
    header = f"## 搜索关键词: {query}" if query else "## RSS Feed 内容"
    lines = [header, f"**找到 {len(results)} 条结果**", ""]

    for i, item in enumerate(results, 1):
        lines.append(f"### {i}. {item['title']}")
        lines.append(f"- **链接**: [{item['link']}]({item['link']})")
        lines.append(f"- **发布时间**: {item['published']}")

        if item['author']:
            lines.append(f"- **作者**: {item['author']}")

        if full:
            _add_markdown_full_details(lines, item)

        lines.append("")

    return "\n".join(lines)


def _determine_feeds(args: argparse.Namespace) -> List[str]:
    """确定要使用的 RSS feeds"""
    if args.feed:
        return [args.feed]
    if args.feeds:
        return load_feeds_from_file(args.feeds)
    return DEFAULT_RSS_FEEDS


def _fetch_and_search_feed(feed_url: str, query: str, case_sensitive: bool, timeout: int) -> List[Dict[str, Any]]:
    """获取并搜索单个 RSS feed"""
    print(f"  - 获取: {feed_url}", file=sys.stderr)
    feed_data = fetch_rss_feed(feed_url, timeout=timeout)

    if feed_data["status"] == "error":
        print(f"    错误: {feed_data['error']}", file=sys.stderr)
        return []

    print(f"    成功: {feed_data['title']} ({len(feed_data['entries'])} 条)", file=sys.stderr)

    results = search_entries(feed_data["entries"], query, case_sensitive)

    for result in results:
        result["feed_title"] = feed_data["title"]
        result["feed_url"] = feed_url

    return results


def _format_output(results: List[Dict[str, Any]], args: argparse.Namespace) -> str:
    """根据参数格式化输出"""
    if args.json:
        return json.dumps(results, indent=2 if args.pretty else None, ensure_ascii=False)
    if args.markdown:
        return format_markdown(results, args.query, full=args.full)
    return format_text(results, args.query, full=args.full)


def _write_output(output: str, output_path: str = None) -> None:
    """输出结果到文件或标准输出"""
    if output_path:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(output)
        print(f"结果已写入: {output_path}", file=sys.stderr)
    else:
        print(output)


def main() -> int:
    """主函数"""
    env_file = _env_file_from_argv(sys.argv)
    load_env_file(env_file)
    args = parse_args()

    feeds = _determine_feeds(args)
    if not feeds:
        print("错误: 未指定 RSS feed。使用 --feed 或 --feeds 参数。", file=sys.stderr)
        return 2

    print(f"正在获取 {len(feeds)} 个 RSS feed...", file=sys.stderr)

    all_results = []
    for feed_url in feeds:
        results = _fetch_and_search_feed(feed_url, args.query, args.case_sensitive, args.timeout)
        all_results.extend(results)

    if args.limit > 0:
        all_results = all_results[:args.limit]

    print(f"\n共找到 {len(all_results)} 条匹配结果\n", file=sys.stderr)

    output = _format_output(all_results, args)
    _write_output(output, args.output)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
