#!/usr/bin/env python3
import argparse
import http.client
import json
import os
import re
import sys
from datetime import datetime

DEFAULT_HOST = "api.tikhub.io"
DEFAULT_PATH = "/api/v1/weibo/web_v2/fetch_advanced_search"
DEFAULT_SAVE_SUFFIX = "weibo_search"


def fetch_advanced_search(token, keyword, search_type="hot", include_type="pic",
                         timescope=None, page=1, host=DEFAULT_HOST, path=DEFAULT_PATH, timeout=30):
    """调用微博高级搜索 API (GET 请求)"""
    from urllib.parse import urlencode
    conn = http.client.HTTPSConnection(host, timeout=timeout)

    params = {
        "q": keyword,
        "search_type": search_type,
        "include_type": include_type,
        "page": page
    }
    if timescope:
        params["timescope"] = timescope

    query_string = urlencode(params)
    full_path = f"{path}?{query_string}"

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
    }

    conn.request("GET", full_path, headers=headers)
    res = conn.getresponse()
    raw = res.read()
    conn.close()

    text = raw.decode("utf-8", errors="replace")
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return {"_http_status": res.status, "_http_reason": res.reason, "_raw": text}

    data["_http_status"] = res.status
    return data


def parse_weibo(item, search_keyword):
    """解析单条微博数据 (TikHub API 格式)"""
    if not item:
        return None

    # TikHub API 返回的数据结构
    mid = item.get("weibo_id")
    text = item.get("content", "")
    created_at = item.get("publish_time")
    user = {
        "id": item.get("user_name"),
        "screen_name": item.get("user_nick"),
        "profile_url": item.get("user_avatar"),
    }

    user_info = {
        "user_id": user.get("id"),
        "screen_name": user.get("screen_name"),
        "profile_url": user.get("profile_url"),
    }

    interaction = item.get("interaction", {})
    reposts = interaction.get("repost_count", 0)
    comments = interaction.get("comment_count", 0)
    attitudes = interaction.get("like_count", 0)

    media = item.get("media", {})
    pic_urls = media.get("images", []) or []

    source = item.get("source", "")
    url = item.get("post_url", "")
    if url:
        # 清理 URL
        url = url.replace("//weibo.com/", "/")
        if not url.startswith("http"):
            url = "https://weibo.com" + url

    return {
        "search_keyword": search_keyword,
        "weibo_id": mid,
        "content": text.strip() if text else "",
        "created_at": created_at,
        "user_info": user_info,
        "interaction_data": {
            "reposts_count": reposts,
            "comments_count": comments,
            "attitudes_count": attitudes,
        },
        "images": pic_urls,
        "source": source,
        "url": url,
    }


def filter_results(result, search_keyword):
    """过滤微博 API 响应数据"""
    items = []

    if isinstance(result, dict):
        # TikHub API 返回的数据结构: data.parsed_data.results
        parsed_data = result.get("data", {}).get("parsed_data", {})
        items = parsed_data.get("results", [])

    if not isinstance(items, list):
        items = []

    filtered = []
    for item in items:
        if isinstance(item, dict):
            processed = parse_weibo(item, search_keyword)
            if processed:
                filtered.append(processed)

    return filtered


def load_env_file(path):
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


def _env_int(name, default):
    value = os.getenv(name)
    if value is None or value == "":
        return default
    try:
        return int(value)
    except ValueError:
        return default


def _env_str(name, default):
    value = os.getenv(name)
    return default if value is None else value


def _env_file_from_argv(argv):
    for i, arg in enumerate(argv):
        if arg == "--env-file" and i + 1 < len(argv):
            return argv[i + 1]
        if arg.startswith("--env-file="):
            return arg.split("=", 1)[1]
    return ".env"


def apply_env_defaults(args):
    if args.token is None:
        args.token = _env_str("TIKHUB_TOKEN", "")

    keyword = args.keyword_opt if args.keyword_opt is not None else args.keyword
    if keyword is None:
        keyword = _env_str("TIKHUB_KEYWORD", "Python")
    args.keyword = keyword

    if args.search_type is None:
        args.search_type = _env_str("TIKHUB_SEARCH_TYPE", "hot")
    if args.include_type is None:
        args.include_type = _env_str("TIKHUB_INCLUDE_TYPE", "pic")
    if args.timescope is None:
        args.timescope = _env_str("TIKHUB_TIMESCOPE", None)
    if args.page is None:
        args.page = _env_int("TIKHUB_PAGE", 1)
    if args.host is None:
        args.host = _env_str("TIKHUB_HOST", DEFAULT_HOST)
    if args.path is None:
        args.path = _env_str("TIKHUB_PATH", DEFAULT_PATH)
    if args.timeout is None:
        args.timeout = _env_int("TIKHUB_TIMEOUT", 30)
    if args.limit is None:
        args.limit = _env_int("TIKHUB_LIMIT", 10)
    return args


def parse_args():
    examples = (
        "Examples:\n"
        "  python tikhub_weibo_search.py \"Python教程\" --pretty\n"
        "  python tikhub_weibo_search.py \"热点\" --search-type hot --page 1\n"
        "  python tikhub_weibo_search.py --env-file .env --limit 20\n"
    )
    parser = argparse.ArgumentParser(
        description="TikHub Weibo search API client",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog=examples,
    )
    parser.add_argument("--env-file", default=_env_file_from_argv(sys.argv), help="Env file path")
    parser.add_argument("keyword", nargs="?", help="Search keyword (positional)")
    parser.add_argument("--keyword", dest="keyword_opt", help="Search keyword (overrides positional)")
    parser.add_argument("--token", help="API token")
    parser.add_argument("--search-type", default="hot", help="Search type: hot, normal")
    parser.add_argument("--include-type", default="pic", help="Include type: pic, video")
    parser.add_argument("--timescope", help="Time scope: custom:2025-09-01-0:2025-09-08-23")
    parser.add_argument("--page", type=int, default=1, help="Page number")
    parser.add_argument("--host", help="API host")
    parser.add_argument("--path", help="API path")
    parser.add_argument("--timeout", type=int, help="Timeout seconds")
    parser.add_argument("--limit", type=int, help="Max items to output")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON")
    return parser.parse_args()


def main():
    env_file = _env_file_from_argv(sys.argv)
    load_env_file(env_file)
    args = parse_args()
    args = apply_env_defaults(args)
    if not args.token:
        print("Missing API token. Set --token or TIKHUB_TOKEN.", file=sys.stderr)
        return 2

    result = fetch_advanced_search(
        token=args.token,
        keyword=args.keyword,
        search_type=args.search_type,
        include_type=args.include_type,
        timescope=args.timescope,
        page=args.page,
        host=args.host,
        path=args.path,
        timeout=args.timeout,
    )

    base_dir = os.path.dirname(os.path.abspath(__file__))
    save_dir = os.path.join(base_dir, "responses")
    os.makedirs(save_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # 1. Save Full Response
    full_filename = f"{timestamp}_{DEFAULT_SAVE_SUFFIX}.json"
    full_save_path = os.path.join(save_dir, full_filename)
    with open(full_save_path, "w", encoding="utf-8") as handle:
        json.dump(result, handle, ensure_ascii=False)

    # 2. Extract and Filter Items
    filtered_items = filter_results(result, args.keyword)
    limit = args.limit if args.limit is not None else 10
    if limit >= 0:
        filtered_items = filtered_items[:limit]
    
    # 3. Save Filtered Summary
    filtered_filename = f"{timestamp}_{DEFAULT_SAVE_SUFFIX}_filtered.json"
    filtered_save_path = os.path.join(save_dir, filtered_filename)
    with open(filtered_save_path, "w", encoding="utf-8") as handle:
        json.dump(filtered_items, handle, ensure_ascii=False, indent=2)

    output = {
        "full_response_saved_at": full_save_path,
        "filtered_summary_saved_at": filtered_save_path,
        "items": filtered_items,
    }

    if args.pretty:
        print(json.dumps(output, indent=2, ensure_ascii=False))
    else:
        print(json.dumps(output, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
