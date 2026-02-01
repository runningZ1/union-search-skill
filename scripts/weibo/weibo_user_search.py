#!/usr/bin/env python3
"""
微博用户搜索脚本
基于 weiboSpider 项目，提供简化的微博用户信息和微博内容搜索功能
"""
import argparse
import http.client
import json
import os
import re
import sys
from datetime import datetime
from urllib.parse import urlencode, quote


DEFAULT_SAVE_SUFFIX = "weibo_user_search"


def load_env_file(path):
    """加载环境变量文件"""
    if not path or not os.path.exists(path):
        return

    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue

            key, value = line.split("=", 1)
            key, value = key.strip(), value.strip()

            if key and key not in os.environ:
                os.environ[key] = value


def get_env_int(name, default):
    """获取整数类型的环境变量"""
    value = os.getenv(name)
    if not value:
        return default

    try:
        return int(value)
    except ValueError:
        return default


def get_env_str(name, default):
    """获取字符串类型的环境变量"""
    value = os.getenv(name)
    return value if value is not None else default


def get_env_file_from_argv(argv):
    """从命令行参数中提取环境变量文件路径"""
    for i, arg in enumerate(argv):
        if arg == "--env-file" and i + 1 < len(argv):
            return argv[i + 1]
        if arg.startswith("--env-file="):
            return arg.split("=", 1)[1]
    return ".env"


def parse_args():
    examples = (
        "Examples:\n"
        "  python weibo_user_search.py --user-id 1669879400\n"
        "  python weibo_user_search.py --user-id 1669879400 --limit 20 --filter 1\n"
        "  python weibo_user_search.py --user-id 1669879400 --since-date 2025-01-01\n"
    )
    parser = argparse.ArgumentParser(
        description="Weibo user search client (based on weiboSpider)",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog=examples,
    )
    parser.add_argument("--env-file", default=get_env_file_from_argv(sys.argv), help="Env file path")
    parser.add_argument("--user-id", help="Weibo user ID (required)")
    parser.add_argument("--cookie", help="Weibo cookie for authentication")
    parser.add_argument("--filter", type=int, choices=[0, 1], help="0=all weibo, 1=original only (default: 0)")
    parser.add_argument("--since-date", help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end-date", help="End date (YYYY-MM-DD or 'now')")
    parser.add_argument("--limit", type=int, help="Max weibo items to fetch (default: 10)")
    parser.add_argument("--sort-by", help="Sort by field: publish_time/up_num/retweet_num/comment_num")
    parser.add_argument("--sort-order", choices=["asc", "desc"], help="Sort order (asc/desc)")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON")
    parser.add_argument("--save-raw", action="store_true", help="Save raw response to responses/ directory")
    return parser.parse_args()


def apply_env_defaults(args):
    """应用环境变量默认值"""
    args.user_id = args.user_id or get_env_str("WEIBO_USER_ID", "")
    args.cookie = args.cookie or get_env_str("WEIBO_COOKIE", "")
    args.filter = args.filter if args.filter is not None else get_env_int("WEIBO_FILTER", 0)
    args.since_date = args.since_date or get_env_str("WEIBO_SINCE_DATE", "2025-01-01")
    args.end_date = args.end_date or get_env_str("WEIBO_END_DATE", "now")
    args.limit = args.limit or get_env_int("WEIBO_LIMIT", 10)
    args.sort_by = args.sort_by or get_env_str("WEIBO_SORT_BY", "")
    args.sort_order = args.sort_order or get_env_str("WEIBO_SORT_ORDER", "desc")
    return args


def fetch_weibo_user_info(user_id, cookie, timeout=30):
    """获取微博用户信息，使用微博移动版API"""
    headers = {
        "Cookie": cookie,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }

    conn = http.client.HTTPSConnection("weibo.cn", timeout=timeout)
    try:
        conn.request("GET", f"/{user_id}/info", headers=headers)
        res = conn.getresponse()
        html = res.read().decode("utf-8", errors="replace")

        return {
            "user_id": user_id,
            "nickname": extract_field(html, r'昵称[：:]\s*(.+?)<'),
            "gender": extract_field(html, r'性别[：:]\s*(.+?)<'),
            "location": extract_field(html, r'地区[：:]\s*(.+?)<'),
            "description": extract_field(html, r'简介[：:]\s*(.+?)<'),
            "_http_status": res.status,
        }
    except Exception as e:
        return {"error": str(e), "user_id": user_id}
    finally:
        conn.close()


def fetch_weibo_list(user_id, cookie, page=1, filter_type=0, timeout=30):
    """获取微博列表，filter_type: 0=全部微博, 1=原创微博"""
    headers = {
        "Cookie": cookie,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }

    url = f"/{user_id}?filter=1&page={page}" if filter_type == 1 else f"/{user_id}?page={page}"

    conn = http.client.HTTPSConnection("weibo.cn", timeout=timeout)
    try:
        conn.request("GET", url, headers=headers)
        res = conn.getresponse()
        html = res.read().decode("utf-8", errors="replace")

        return {
            "weibo_list": parse_weibo_list(html),
            "page": page,
            "_http_status": res.status,
        }
    except Exception as e:
        return {"error": str(e), "user_id": user_id, "page": page}
    finally:
        conn.close()


def extract_field(html, pattern):
    """从HTML中提取字段"""
    match = re.search(pattern, html)
    return match.group(1).strip() if match else ""


def parse_weibo_list(html):
    """解析微博列表（简化版本，实际项目应使用 BeautifulSoup 或 lxml）"""
    weibo_list = []
    weibo_blocks = re.findall(r'<div class="c" id="M_(.+?)">(.*?)</div>', html, re.DOTALL)

    for weibo_id, content_block in weibo_blocks:
        content_match = re.search(r'<span class="ctt">(.*?)</span>', content_block, re.DOTALL)
        content = content_match.group(1) if content_match else ""

        stats_match = re.search(r'赞\[(\d+)\].*?转发\[(\d+)\].*?评论\[(\d+)\]', content_block)
        up_num = int(stats_match.group(1)) if stats_match else 0
        retweet_num = int(stats_match.group(2)) if stats_match else 0
        comment_num = int(stats_match.group(3)) if stats_match else 0

        time_match = re.search(r'<span class="ct">(.*?)&nbsp;来自(.+?)</span>', content_block)
        publish_time = time_match.group(1).strip() if time_match else ""
        publish_tool = time_match.group(2).strip() if time_match else ""

        weibo_list.append({
            "id": weibo_id,
            "content": clean_html(content),
            "publish_time": publish_time,
            "publish_tool": publish_tool,
            "up_num": up_num,
            "retweet_num": retweet_num,
            "comment_num": comment_num,
        })

    return weibo_list


def clean_html(text):
    """清理HTML标签"""
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'&nbsp;', ' ', text)
    text = re.sub(r'&lt;', '<', text)
    text = re.sub(r'&gt;', '>', text)
    text = re.sub(r'&amp;', '&', text)
    return text.strip()


def sort_weibo_list(weibo_list, sort_by, sort_order):
    """排序微博列表"""
    valid_fields = ["publish_time", "up_num", "retweet_num", "comment_num"]
    if not sort_by or sort_by not in valid_fields:
        return weibo_list

    reverse = (sort_order == "desc")
    key_func = lambda x: x.get(sort_by, "" if sort_by == "publish_time" else 0)
    return sorted(weibo_list, key=key_func, reverse=reverse)


def format_output(user_info, weibo_list, limit):
    """格式化输出"""
    lines = [
        "=" * 60,
        "用户信息",
        "=" * 60,
        f"用户ID: {user_info.get('user_id', 'N/A')}",
        f"昵称: {user_info.get('nickname', 'N/A')}",
        f"性别: {user_info.get('gender', 'N/A')}",
        f"地区: {user_info.get('location', 'N/A')}",
        f"简介: {user_info.get('description', 'N/A')}",
        "",
        "=" * 60,
        f"微博列表 (共 {len(weibo_list)} 条)",
        "=" * 60,
    ]

    for i, weibo in enumerate(weibo_list[:limit], 1):
        content = weibo.get('content', 'N/A')
        if len(content) > 200:
            content = content[:200] + "..."

        lines.extend([
            f"\n[{i}] 微博ID: {weibo.get('id', 'N/A')}",
            f"内容: {content}",
            f"发布时间: {weibo.get('publish_time', 'N/A')}",
            f"发布工具: {weibo.get('publish_tool', 'N/A')}",
            f"点赞: {weibo.get('up_num', 0)} | 转发: {weibo.get('retweet_num', 0)} | 评论: {weibo.get('comment_num', 0)}",
            "-" * 60,
        ])

    return "\n".join(lines)


def save_raw_response(data, suffix=DEFAULT_SAVE_SUFFIX):
    """保存原始响应到文件"""
    os.makedirs("responses", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"responses/{timestamp}_{suffix}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return filename


def main():
    args = parse_args()
    load_env_file(args.env_file)
    args = apply_env_defaults(args)

    if not args.user_id:
        print("错误: 必须提供 --user-id 参数", file=sys.stderr)
        sys.exit(1)

    if not args.cookie:
        print("错误: 必须提供 --cookie 参数或在环境变量中设置 WEIBO_COOKIE", file=sys.stderr)
        print("提示: 请参考 https://github.com/dataabc/weiboSpider 获取cookie", file=sys.stderr)
        sys.exit(1)

    print(f"正在获取用户 {args.user_id} 的信息...", file=sys.stderr)
    user_info = fetch_weibo_user_info(args.user_id, args.cookie)

    if "error" in user_info:
        print(f"错误: {user_info['error']}", file=sys.stderr)
        sys.exit(1)

    print(f"正在获取微博列表...", file=sys.stderr)
    all_weibo = []
    page = 1
    max_pages = 10

    while len(all_weibo) < args.limit and page <= max_pages:
        result = fetch_weibo_list(args.user_id, args.cookie, page, args.filter)

        if "error" in result:
            print(f"警告: 第{page}页获取失败: {result['error']}", file=sys.stderr)
            break

        weibo_list = result.get("weibo_list", [])
        if not weibo_list:
            break

        all_weibo.extend(weibo_list)
        page += 1

    if args.sort_by:
        all_weibo = sort_weibo_list(all_weibo, args.sort_by, args.sort_order)

    all_weibo = all_weibo[:args.limit]

    if args.save_raw:
        raw_data = {
            "user_info": user_info,
            "weibo_list": all_weibo,
            "query_params": {
                "user_id": args.user_id,
                "filter": args.filter,
                "limit": args.limit,
                "sort_by": args.sort_by,
                "sort_order": args.sort_order,
            },
            "timestamp": datetime.now().isoformat(),
        }
        filename = save_raw_response(raw_data)
        print(f"原始响应已保存到: {filename}", file=sys.stderr)

    if args.pretty:
        output_data = {
            "user_info": user_info,
            "weibo_list": all_weibo,
        }
        print(json.dumps(output_data, ensure_ascii=False, indent=2))
    else:
        print(format_output(user_info, all_weibo, args.limit))


if __name__ == "__main__":
    main()
