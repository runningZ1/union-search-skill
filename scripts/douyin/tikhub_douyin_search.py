#!/usr/bin/env python3
import argparse
import http.client
import json
import os
import re
import sys
from datetime import datetime

DEFAULT_HOST = "api.tikhub.io"
DEFAULT_PATH = "/api/v1/douyin/search/fetch_general_search_v3"
DEFAULT_SAVE_SUFFIX = "douyin_search_v3"


def fetch_general_search_v3(token, payload, host=DEFAULT_HOST, path=DEFAULT_PATH, timeout=30):
    conn = http.client.HTTPSConnection(host, timeout=timeout)
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    body = json.dumps(payload).encode("utf-8")
    conn.request("POST", path, body=body, headers=headers)
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


def build_payload(args):
    return {
        "keyword": args.keyword,
        "cursor": args.cursor,
        "sort_type": args.sort_type,
        "publish_time": args.publish_time,
        "filter_duration": args.filter_duration,
        "content_type": args.content_type,
        "search_id": args.search_id,
        "backtrace": args.backtrace,
    }


def format_timestamp(ts):
    """Convert unix timestamp to human-readable string."""
    if not ts:
        return "N/A"
    try:
        return datetime.fromtimestamp(int(ts)).strftime('%Y-%m-%d %H:%M:%S')
    except (ValueError, TypeError):
        return str(ts)


def extract_tags(aweme):
    """Extract hashtags from aweme object."""
    tags = []
    text_extra = aweme.get("text_extra") or []
    for entry in text_extra:
        if isinstance(entry, dict):
            tag = (
                entry.get("hashtag_name")
                or entry.get("hash_tag_name")
                or entry.get("tag_name")
            )
            if tag:
                tags.append(f"#{tag}")
    
    if not tags:
        desc = aweme.get("desc") or ""
        tags = [f"#{match}" for match in re.findall(r"#([^\s#]+)", desc)]
        
    # Deduplicate while preserving order
    seen = set()
    return [x for x in tags if not (x in seen or seen.add(x))]


def parse_aweme(aweme, search_keyword):
    """Extract required fields from a single aweme (video) object."""
    if not aweme:
        return None
    
    stats = aweme.get("statistics") or {}
    author = aweme.get("author") or {}
    
    return {
        "search_keyword": search_keyword,
        "video_info": {
            "aweme_id": aweme.get("aweme_id"),
            "title": (aweme.get("desc") or "").strip(),
            "tags": extract_tags(aweme),
            "publish_time": format_timestamp(aweme.get("create_time")),
        },
        "interaction_data": {
            "like_count": stats.get("digg_count", 0),
            "comment_count": stats.get("comment_count", 0),
            "share_count": stats.get("share_count", 0),
            "forward_count": stats.get("forward_count", 0),
            "play_count": stats.get("play_count", 0),
            "collect_count": stats.get("collect_count", 0)
        },
        "author_info": {
            "author_id": author.get("uid"),
            "author_sec_id": author.get("sec_uid"),
            "nickname": author.get("nickname")
        },
        "media_info": {
            "play_urls": (aweme.get("video") or {}).get("play_addr", {}).get("url_list", []),
            "cover_urls": (aweme.get("video") or {}).get("cover", {}).get("url_list", []),
            "dynamic_cover_urls": (aweme.get("video") or {}).get("dynamic_cover", {}).get("url_list", [])
        }
    }


def filter_results(result):
    """Filter full API response into structured summary."""
    search_keyword = result.get("params", {}).get("keyword", "N/A")
    items = result.get("data", {}).get("data") if isinstance(result.get("data"), dict) else []
    if not isinstance(items, list):
        items = []

    filtered = []
    for item in items:
        if not isinstance(item, dict):
            continue
        # Direct video info
        if "aweme_info" in item:
            processed = parse_aweme(item["aweme_info"], search_keyword)
            if processed:
                filtered.append(processed)
        # List of videos (e.g. user card)
        if "aweme_list" in item:
            aweme_list = item["aweme_list"]
            if isinstance(aweme_list, list):
                for aweme in aweme_list:
                    processed = parse_aweme(aweme, search_keyword)
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
        keyword = _env_str("TIKHUB_KEYWORD", "cat")
    args.keyword = keyword

    if args.cursor is None:
        args.cursor = _env_int("TIKHUB_CURSOR", 0)
    if args.sort_type is None:
        args.sort_type = _env_str("TIKHUB_SORT_TYPE", "0")
    if args.publish_time is None:
        args.publish_time = _env_str("TIKHUB_PUBLISH_TIME", "0")
    if args.filter_duration is None:
        args.filter_duration = _env_str("TIKHUB_FILTER_DURATION", "0")
    if args.content_type is None:
        args.content_type = _env_str("TIKHUB_CONTENT_TYPE", "0")
    if args.search_id is None:
        args.search_id = _env_str("TIKHUB_SEARCH_ID", "")
    if args.backtrace is None:
        args.backtrace = _env_str("TIKHUB_BACKTRACE", "")
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
        "  python tikhub_douyin_search.py \"猫咪\" --sort-type 2 --publish-time 7\n"
        "  python tikhub_douyin_search.py --keyword cat --cursor 0 --pretty\n"
        "  python tikhub_douyin_search.py --env-file .env --content-type 1\n"
    )
    parser = argparse.ArgumentParser(
        description="TikHub Douyin search V3 API client with production filtering",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog=examples,
    )
    parser.add_argument("--env-file", default=_env_file_from_argv(sys.argv), help="Env file path")
    parser.add_argument("keyword", nargs="?", help="Search keyword (positional)")
    parser.add_argument("--keyword", dest="keyword_opt", help="Search keyword (overrides positional)")
    parser.add_argument("--token", help="API token")
    parser.add_argument("--cursor", type=int, help="Pagination cursor")
    parser.add_argument("--sort-type", help="Sort type: 0,1,2")
    parser.add_argument("--publish-time", help="Publish time: 0,1,7,180")
    parser.add_argument("--filter-duration", help="Duration filter")
    parser.add_argument("--content-type", help="Content type")
    parser.add_argument("--search-id", help="Search ID for pagination")
    parser.add_argument("--backtrace", help="Backtrace for pagination")
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

    payload = build_payload(args)
    result = fetch_general_search_v3(
        token=args.token,
        payload=payload,
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
    filtered_items = filter_results(result)
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
