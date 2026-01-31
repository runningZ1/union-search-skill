#!/usr/bin/env python3
"""
RSS Feed Search Tool
支持从多个 RSS 源搜索和过滤内容
"""
import argparse
import json
import os
import sys
from datetime import datetime
from typing import List, Dict, Any
import feedparser


DEFAULT_RSS_FEEDS = [
    "http://feedmaker.kindle4rss.com/feeds/AI_era.weixin.xml",
]


def load_env_file(path):
    """加载环境变量文件"""
    if not path or not os.path.exists(path):
        return
    with open(path, "r", encoding="utf-8") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip()
            if key and key not in os.environ:
                os.environ[key] = value


def _env_file_from_argv(argv):
    """从命令行参数中提取 env 文件路径"""
    for i, arg in enumerate(argv):
        if arg == "--env-file" and i + 1 < len(argv):
            return argv[i + 1]
        if arg.startswith("--env-file="):
            return arg.split("=", 1)[1]
    return ".env"


def parse_args():
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


def search_entries(entries: List[Any], query: str, case_sensitive: bool = False) -> List[Dict[str, Any]]:
    """在 RSS 条目中搜索关键词"""
    results = []

    for entry in entries:
        # 提取条目信息
        title = entry.get("title", "")
        summary = entry.get("summary", entry.get("description", ""))
        content = ""
        if "content" in entry and entry.content:
            content = entry.content[0].get("value", "")

        # 搜索逻辑
        if not query:
            # 无查询词，返回所有条目
            match = True
        else:
            # 在标题、摘要、内容中搜索
            search_text = f"{title} {summary} {content}"
            if case_sensitive:
                match = query in search_text
            else:
                match = query.lower() in search_text.lower()

        if match:
            # 解析发布时间
            published = entry.get("published", entry.get("updated", ""))
            published_parsed = entry.get("published_parsed", entry.get("updated_parsed", None))
            if published_parsed:
                try:
                    published = datetime(*published_parsed[:6]).strftime("%Y-%m-%d %H:%M:%S")
                except:
                    pass

            results.append({
                "title": title,
                "link": entry.get("link", ""),
                "published": published,
                "author": entry.get("author", ""),
                "summary": summary,
                "content": content,
                "tags": [tag.get("term", "") for tag in entry.get("tags", [])],
            })

    return results


def format_text(results: List[Dict[str, Any]], query: str, full: bool = False) -> str:
    """格式化为纯文本输出"""
    lines = []

    if query:
        lines.append(f"搜索关键词: {query}")
    else:
        lines.append("RSS Feed 内容")
    lines.append(f"找到 {len(results)} 条结果")
    lines.append("")

    for i, item in enumerate(results, 1):
        lines.append(f"[{i}] {item['title']}")
        lines.append(f"  链接: {item['link']}")
        lines.append(f"  发布时间: {item['published']}")

        if item['author']:
            lines.append(f"  作者: {item['author']}")

        if full:
            if item['summary']:
                lines.append(f"  摘要: {item['summary'][:200]}...")
            if item['tags']:
                lines.append(f"  标签: {', '.join(item['tags'])}")
            if item['content'] and item['content'] != item['summary']:
                lines.append(f"  内容: {item['content'][:300]}...")

        lines.append("")

    return "\n".join(lines)


def format_markdown(results: List[Dict[str, Any]], query: str, full: bool = False) -> str:
    """格式化为 Markdown 输出"""
    lines = []

    if query:
        lines.append(f"## 搜索关键词: {query}")
    else:
        lines.append("## RSS Feed 内容")
    lines.append(f"**找到 {len(results)} 条结果**")
    lines.append("")

    for i, item in enumerate(results, 1):
        lines.append(f"### {i}. {item['title']}")
        lines.append(f"- **链接**: [{item['link']}]({item['link']})")
        lines.append(f"- **发布时间**: {item['published']}")

        if item['author']:
            lines.append(f"- **作者**: {item['author']}")

        if full:
            if item['summary']:
                lines.append(f"- **摘要**: {item['summary']}")
            if item['tags']:
                lines.append(f"- **标签**: {', '.join(item['tags'])}")
            if item['content'] and item['content'] != item['summary']:
                lines.append(f"\n**内容**:\n\n{item['content']}\n")

        lines.append("")

    return "\n".join(lines)


def main():
    """主函数"""
    env_file = _env_file_from_argv(sys.argv)
    load_env_file(env_file)
    args = parse_args()

    # 确定要使用的 RSS feeds
    feeds = []
    if args.feed:
        feeds.append(args.feed)
    elif args.feeds:
        feeds = load_feeds_from_file(args.feeds)
    else:
        feeds = DEFAULT_RSS_FEEDS

    if not feeds:
        print("错误: 未指定 RSS feed。使用 --feed 或 --feeds 参数。", file=sys.stderr)
        return 2

    print(f"正在获取 {len(feeds)} 个 RSS feed...", file=sys.stderr)

    # 获取所有 feeds
    all_results = []
    for feed_url in feeds:
        print(f"  - 获取: {feed_url}", file=sys.stderr)
        feed_data = fetch_rss_feed(feed_url, timeout=args.timeout)

        if feed_data["status"] == "error":
            print(f"    错误: {feed_data['error']}", file=sys.stderr)
            continue

        print(f"    成功: {feed_data['title']} ({len(feed_data['entries'])} 条)", file=sys.stderr)

        # 搜索条目
        results = search_entries(feed_data["entries"], args.query, args.case_sensitive)

        # 添加 feed 信息
        for result in results:
            result["feed_title"] = feed_data["title"]
            result["feed_url"] = feed_url

        all_results.extend(results)

    # 限制结果数量
    if args.limit > 0:
        all_results = all_results[:args.limit]

    print(f"\n共找到 {len(all_results)} 条匹配结果\n", file=sys.stderr)

    # 格式化输出
    if args.json:
        output = json.dumps(all_results, indent=2 if args.pretty else None, ensure_ascii=False)
    elif args.markdown:
        output = format_markdown(all_results, args.query, full=args.full)
    else:
        output = format_text(all_results, args.query, full=args.full)

    # 输出结果
    if args.output:
        with open(args.output, "w", encoding="utf-8") as handle:
            handle.write(output)
        print(f"结果已写入: {args.output}", file=sys.stderr)
    else:
        print(output)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
