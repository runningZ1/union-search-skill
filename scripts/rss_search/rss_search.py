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
        "  python rss_search.py \"AI\" --parse-only --parse-folder ./parsed_results\n"
        "  python rss_search.py \"AI\" --parse-folder ./parsed_results --no-fetch\n"
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
    # 新增：解析结果文件夹相关参数
    parser.add_argument("--parse-folder", type=str, default="",
                        help="解析结果保存/读取的文件夹路径（保存解析结果供后续搜索使用）")
    parser.add_argument("--parse-only", action="store_true",
                        help="仅解析并保存RSS结果，不进行搜索")
    parser.add_argument("--no-fetch", action="store_true",
                        help="不重新获取RSS，直接从解析文件夹中搜索（需先用--parse-folder保存过结果）")
    return parser.parse_args()


def load_feeds_from_file(filepath: str) -> List[str]:
    """从文件加载 RSS feed URLs，支持两种格式：
    1. 每行一个URL
    2. 每行 "名称 URL"（空格分隔）
    """
    feeds = []
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                # 跳过空行、注释行
                if not line or line.startswith("#"):
                    continue

                # 提取URL（支持 "名称 URL" 或直接 "URL" 格式）
                parts = line.split()
                url = None
                for part in parts:
                    if part.startswith("http"):
                        url = part
                        break

                if url:
                    feeds.append(url)
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


def _sanitize_filename(name: str) -> str:
    """将字符串转换为安全的文件名"""
    # 替换不安全字符为下划线
    safe = re.sub(r'[<>:"/\\|?*]', '_', name)
    # 限制长度
    return safe[:50] if len(safe) > 50 else safe


def _get_parse_filename(feed_url: str, parsed_time: str = None) -> str:
    """根据feed URL生成解析结果文件名

    格式: {url_hash}_{YYYY-MM-DD_HH-MM-SS}.json
    """
    import hashlib
    url_hash = hashlib.md5(feed_url.encode()).hexdigest()[:8]

    # 如果没有提供时间，使用当前时间
    if not parsed_time:
        parsed_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    return f"{url_hash}_{parsed_time}.json"


def _strip_html(text: str) -> str:
    """去除HTML标签，只保留纯文本"""
    if not text:
        return ""
    # 去除HTML标签
    clean = re.sub(r'<[^>]+>', '', text)
    # 去除多余空白
    clean = re.sub(r'\s+', ' ', clean).strip()
    return clean


def _clean_entry(entry: Any) -> Dict[str, Any]:
    """清洗条目数据，保留所有字段但清洗HTML标签"""
    # 将entry转换为字典（如果是对象）
    if not isinstance(entry, dict):
        # 如果是对象，获取所有属性
        cleaned = {}
        for key in dir(entry):
            if not key.startswith('_'):
                try:
                    value = getattr(entry, key)
                    if not callable(value):
                        cleaned[key] = value
                except:
                    pass
    else:
        cleaned = dict(entry)

    # 清洗 summary 中的HTML标签
    if "summary" in cleaned and cleaned["summary"]:
        cleaned["summary"] = _strip_html(cleaned["summary"])

    # 清洗 content 中的HTML标签（如果存在）
    if "content" in cleaned and cleaned["content"]:
        if isinstance(cleaned["content"], list) and len(cleaned["content"]) > 0:
            content_item = cleaned["content"][0]
            if isinstance(content_item, dict) and "value" in content_item:
                cleaned["content"][0]["value"] = _strip_html(content_item.get("value", ""))
        elif isinstance(cleaned["content"], str):
            cleaned["content"] = _strip_html(cleaned["content"])

    return cleaned


def _clean_feed_data(feed_data: Dict[str, Any]) -> Dict[str, Any]:
    """清洗feed数据，清理entries，保留所有字段"""
    # 复制原始数据
    cleaned = dict(feed_data)

    # 清洗description中的HTML标签
    if "description" in cleaned and cleaned["description"]:
        cleaned["description"] = _strip_html(cleaned["description"])

    # 清洗每个条目
    entries = cleaned.get("entries", [])
    cleaned["entries"] = [_clean_entry(e) for e in entries]

    return cleaned


def save_parsed_feeds(feeds_data: List[Dict[str, Any]], folder: str) -> None:
    """保存解析结果到指定文件夹（合并为一个文件）"""
    if not folder:
        return

    # 创建文件夹
    os.makedirs(folder, exist_ok=True)

    # 获取当前解析时间
    parsed_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"all_feeds_{parsed_time}.json"
    filepath = os.path.join(folder, filename)

    # 清洗并收集所有feed
    all_feeds = []
    for feed_data in feeds_data:
        # 添加解析时间
        feed_data["parsed_at"] = datetime.now().isoformat()
        # 清洗数据
        cleaned_data = _clean_feed_data(feed_data)
        all_feeds.append(cleaned_data)

    # 保存为合并文件
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(all_feeds, f, ensure_ascii=False, indent=2)

    print(f"  已保存: {filepath} ({len(all_feeds)} 个源)", file=sys.stderr)


def load_parsed_feeds(folder: str, latest_only: bool = True) -> List[Dict[str, Any]]:
    """从指定文件夹加载已解析的feed结果

    Args:
        folder: 文件夹路径
        latest_only: 是否只加载最新的解析结果（按文件名中的日期），默认True
    """
    if not folder or not os.path.exists(folder):
        return []

    # 查找最新的合并文件
    json_files = [f for f in os.listdir(folder) if f.startswith("all_feeds_") and f.endswith(".json")]

    if not json_files:
        return []

    # 按日期排序（最新的在前面）
    def extract_date(filename):
        # 格式: all_feeds_{YYYY-MM-DD_HH-MM-SS}.json
        parts = filename.replace('.json', '').split('_')
        if len(parts) >= 3:
            return '_'.join(parts[-2:])  # 如 "2026-03-07_11-33-00"
        return ""

    json_files.sort(key=extract_date, reverse=True)

    # 加载最新的合并文件
    latest_file = json_files[0]
    filepath = os.path.join(folder, latest_file)

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            feeds_data = json.load(f)
            # feeds_data 是一个列表，每个元素是一个feed的数据
            return feeds_data
    except Exception as e:
        print(f"  警告: 读取 {latest_file} 失败: {e}", file=sys.stderr)
        return []


def _extract_content(entry: Any) -> str:
    """提取条目的内容，同时支持对象和字典访问"""
    # 支持字典访问（从JSON加载后）
    if isinstance(entry, dict):
        if "content" in entry and entry["content"]:
            content_list = entry["content"]
            if content_list and len(content_list) > 0:
                return content_list[0].get("value", "") if isinstance(content_list[0], dict) else ""
        return ""
    # 支持对象属性访问（原始feedparser返回）
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


def _get_entry_value(entry: Any, key: str, default: Any = "") -> Any:
    """统一获取entry的值，支持字典和对象访问"""
    if isinstance(entry, dict):
        return entry.get(key, default)
    # 对象属性访问
    return getattr(entry, key, default)


def _format_published_date(entry: Any) -> str:
    """格式化发布时间"""
    published = _get_entry_value(entry, "published", _get_entry_value(entry, "updated", ""))
    published_parsed = _get_entry_value(entry, "published_parsed", _get_entry_value(entry, "updated_parsed", None))

    if published_parsed:
        # 支持字典（JSON加载后）和元组（原始feedparser）两种格式
        if isinstance(published_parsed, (list, tuple)):
            try:
                return datetime(*published_parsed[:6]).strftime("%Y-%m-%d %H:%M:%S")
            except (TypeError, ValueError):
                pass
    return published

    return published


def _matches_query(title: str, summary: str, query: str, case_sensitive: bool) -> bool:
    """检查条目是否匹配查询"""
    if not query:
        return True

    search_text = f"{title} {summary}"
    if case_sensitive:
        return query in search_text
    return query.lower() in search_text.lower()


def search_entries(entries: List[Any], query: str, case_sensitive: bool = False) -> List[Dict[str, Any]]:
    """在 RSS 条目中搜索关键词"""
    results = []

    for entry in entries:
        title = _get_entry_value(entry, "title", "")
        summary = _get_entry_value(entry, "summary", "")

        if not _matches_query(title, summary, query, case_sensitive):
            continue

        # 获取各种字段
        original_link = _get_entry_value(entry, "link", "")
        weixin_link = _get_entry_value(entry, "weixin_link", _extract_weixin_link(summary, original_link))
        published = _get_entry_value(entry, "published", "")
        author = _get_entry_value(entry, "author", "")
        tags = _get_entry_value(entry, "tags", [])

        results.append({
            "title": title,
            "link": original_link,
            "weixin_link": weixin_link,
            "published": published,
            "author": author,
            "summary": summary,
            "tags": tags,
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

    # 确定使用解析文件夹还是直接获取
    use_parse_folder = bool(args.parse_folder)
    parse_folder = args.parse_folder

    all_results = []

    if use_parse_folder:
        # 模式1: 使用解析文件夹
        if args.no_fetch:
            # 只从文件夹读取，不重新获取
            print(f"从解析文件夹加载: {parse_folder}", file=sys.stderr)
            feeds_data = load_parsed_feeds(parse_folder)
            if not feeds_data:
                print("错误: 解析文件夹为空，请先使用 --parse-only 或不加 --no-fetch 获取解析结果", file=sys.stderr)
                return 1

            # 从加载的数据中搜索
            for feed_data in feeds_data:
                if feed_data.get("status") != "success":
                    continue
                results = search_entries(feed_data["entries"], args.query, args.case_sensitive)
                for result in results:
                    result["feed_title"] = feed_data.get("title", "Unknown")
                    result["feed_url"] = feed_data.get("url", "")
                all_results.extend(results)
                print(f"  从 {feed_data.get('title', 'Unknown')} 加载了 {len(feed_data.get('entries', []))} 条", file=sys.stderr)
        else:
            # 获取并保存到文件夹
            print(f"正在获取 {len(feeds)} 个 RSS feed 并保存到 {parse_folder}...", file=sys.stderr)
            feeds_data = []
            for feed_url in feeds:
                print(f"  - 获取: {feed_url}", file=sys.stderr)
                feed_data = fetch_rss_feed(feed_url, timeout=args.timeout)
                feeds_data.append(feed_data)

                if feed_data["status"] == "error":
                    print(f"    错误: {feed_data['error']}", file=sys.stderr)
                else:
                    print(f"    成功: {feed_data['title']} ({len(feed_data['entries'])} 条)", file=sys.stderr)

            # 保存到文件夹
            save_parsed_feeds(feeds_data, parse_folder)

            # 如果只是解析模式，不进行搜索
            if args.parse_only:
                print(f"\n解析完成，已保存到 {parse_folder}", file=sys.stderr)
                return 0

            # 从获取的数据中搜索
            for feed_data in feeds_data:
                if feed_data.get("status") != "success":
                    continue
                results = search_entries(feed_data["entries"], args.query, args.case_sensitive)
                for result in results:
                    result["feed_title"] = feed_data.get("title", "Unknown")
                    result["feed_url"] = feed_data.get("url", "")
                all_results.extend(results)
    else:
        # 模式2: 直接获取（原有行为）
        print(f"正在获取 {len(feeds)} 个 RSS feed...", file=sys.stderr)

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
