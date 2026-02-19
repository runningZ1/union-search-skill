#!/usr/bin/env python3
import argparse
import http.client
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import urlencode

DEFAULT_HOST = "api.tikhub.io"
DEFAULT_PATH = "/api/v1/twitter/web/fetch_search_timeline"


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


def parse_args():
    examples = (
        "Examples:\n"
        "  python tikhub_twitter_search.py \"Elon Musk\" --search-type Top\n"
        "  python tikhub_twitter_search.py --keyword OpenAI --search-type Latest\n"
        "  python tikhub_twitter_search.py --cursor \"<cursor>\" --search-type Top\n"
    )
    parser = argparse.ArgumentParser(
        description="TikHub Twitter web search timeline client",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog=examples,
    )
    parser.add_argument("--env-file", default=_env_file_from_argv(sys.argv), help="Env file path")
    parser.add_argument("keyword", nargs="?", help="Search keyword (positional)")
    parser.add_argument("--keyword", dest="keyword_opt", help="Search keyword (overrides positional)")
    parser.add_argument("--token", help="API token")
    parser.add_argument("--search-type", help="Search type: Top/Latest/Media/People/Lists")
    parser.add_argument("--cursor", help="Cursor for paging (from previous response)")
    parser.add_argument("--host", help="API host")
    parser.add_argument("--path", help="API path")
    parser.add_argument("--timeout", type=int, help="Timeout seconds")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON")
    parser.add_argument("--save", action="store_true", help="Save response to file")
    parser.add_argument("--output-dir", default="scripts/twitter/responses", help="Output directory for saved files")
    parser.add_argument("--filter", action="store_true", help="Also save filtered/core response")
    return parser.parse_args()


def apply_env_defaults(args):
    if args.token is None:
        args.token = _env_str("TIKHUB_TOKEN", "")

    keyword = args.keyword_opt if args.keyword_opt is not None else args.keyword
    if keyword is None:
        keyword = _env_str("TIKHUB_TWITTER_KEYWORD", "")
    args.keyword = keyword

    if args.search_type is None:
        args.search_type = _env_str("TIKHUB_TWITTER_SEARCH_TYPE", "Top")
    if args.cursor is None:
        args.cursor = _env_str("TIKHUB_TWITTER_CURSOR", None)
    if args.host is None:
        args.host = _env_str("TIKHUB_HOST", DEFAULT_HOST)
    if args.path is None:
        args.path = _env_str("TIKHUB_TWITTER_PATH", DEFAULT_PATH)
    if args.timeout is None:
        args.timeout = int(_env_str("TIKHUB_TIMEOUT", "30"))
    return args


def fetch_search_timeline(token, params, host=DEFAULT_HOST, path=DEFAULT_PATH, timeout=30):
    query = urlencode(params, doseq=True)
    full_path = f"{path}?{query}" if query else path
    conn = http.client.HTTPSConnection(host, timeout=timeout)
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


def extract_core_tweet(tweet: dict) -> dict:
    """提取单条推文的核心信息"""
    screen_name = tweet.get("screen_name", "")
    tweet_id = tweet.get("tweet_id", "")

    core_tweet = {
        "tweet_id": tweet_id,
        "url": f"https://x.com/{screen_name}/status/{tweet_id}",
        "type": tweet.get("type"),
        "text": tweet.get("text"),
        "lang": tweet.get("lang"),
        "created_at": tweet.get("created_at"),
        "author": {
            "screen_name": screen_name,
            "name": tweet.get("user_info", {}).get("name"),
            "verified": tweet.get("user_info", {}).get("verified", False),
            "followers_count": tweet.get("user_info", {}).get("followers_count"),
            "description": tweet.get("user_info", {}).get("description"),
        },
        "metrics": {
            "favorites": tweet.get("favorites", 0),
            "retweets": tweet.get("retweets", 0),
            "replies": tweet.get("replies", 0),
            "quotes": tweet.get("quotes", 0),
            "bookmarks": tweet.get("bookmarks", 0),
            "views": tweet.get("views", "0"),
        },
        "media": {},
        "entities": {},
        "conversation_id": tweet.get("conversation_id"),
    }

    # 提取媒体信息
    media = tweet.get("media", {})
    if media:
        for media_type, items in media.items():
            if items and isinstance(items, list):
                core_tweet["media"][media_type] = []
                for item in items:
                    media_info = {
                        "media_url_https": item.get("media_url_https"),
                        "id": item.get("id") or item.get("id_str"),
                        "type": item.get("type", media_type),
                    }
                    if "original_info" in item:
                        media_info["width"] = item["original_info"].get("width")
                        media_info["height"] = item["original_info"].get("height")
                    core_tweet["media"][media_type].append(media_info)

    # 提取实体信息
    entities = tweet.get("entities", {})
    if entities:
        if entities.get("hashtags"):
            core_tweet["entities"]["hashtags"] = [tag.get("text") for tag in entities["hashtags"]]
        if entities.get("urls"):
            core_tweet["entities"]["urls"] = [
                {"display_url": url.get("display_url"), "expanded_url": url.get("expanded_url")}
                for url in entities["urls"]
            ]
        if entities.get("user_mentions"):
            core_tweet["entities"]["user_mentions"] = [
                {"screen_name": m.get("screen_name"), "name": m.get("name")}
                for m in entities["user_mentions"]
            ]

    return core_tweet


def extract_core_response(full_response: dict) -> dict:
    """提取完整响应的核心信息"""
    if full_response.get("code") != 200:
        return {
            "success": False,
            "error": full_response.get("detail", full_response.get("message")),
        }

    core_response = {
        "success": True,
        "metadata": {
            "keyword": full_response.get("params", {}).get("keyword"),
            "search_type": full_response.get("params", {}).get("search_type"),
            "request_id": full_response.get("request_id"),
            "search_time": full_response.get("time"),
            "cache_url": full_response.get("cache_url"),
        },
        "stats": {
            "total_tweets": len(full_response.get("data", {}).get("timeline", [])),
        },
        "tweets": [],
    }

    timeline = full_response.get("data", {}).get("timeline", [])
    for tweet in timeline:
        if tweet.get("type") == "tweet":
            core_response["tweets"].append(extract_core_tweet(tweet))

    return core_response


def save_responses(result: dict, args) -> None:
    """保存完整响应和筛选后的响应"""
    if not args.save:
        return

    # 创建输出目录
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # 生成文件名
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    keyword = result.get("params", {}).get("keyword", "unknown").replace("/", "_").replace("\\", "_")
    search_type = result.get("params", {}).get("search_type", "Top")

    base_name = f"twitter_search_{keyword}_{search_type}_{timestamp}"

    # 保存完整响应
    full_file = output_dir / f"{base_name}_full.json"
    with open(full_file, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print(f"✅ 完整响应已保存: {full_file}", file=sys.stderr)

    # 保存筛选后的响应
    if args.filter:
        core_data = extract_core_response(result)
        core_file = output_dir / f"{base_name}_core.json"
        with open(core_file, "w", encoding="utf-8") as f:
            json.dump(core_data, f, indent=2, ensure_ascii=False)
        print(f"✅ 筛选响应已保存: {core_file}", file=sys.stderr)
        print(f"   推文数量: {core_data.get('stats', {}).get('total_tweets', 0)}", file=sys.stderr)


def main():
    env_file = _env_file_from_argv(sys.argv)
    load_env_file(env_file)
    args = apply_env_defaults(parse_args())

    if not args.token:
        print("Missing API token. Set --token or TIKHUB_TOKEN.", file=sys.stderr)
        return 2
    if not args.keyword:
        print("Missing keyword. Provide positional keyword or --keyword.", file=sys.stderr)
        return 2

    params = {
        "keyword": args.keyword,
        "search_type": args.search_type,
    }
    if args.cursor:
        params["cursor"] = args.cursor

    result = fetch_search_timeline(
        token=args.token,
        params=params,
        host=args.host,
        path=args.path,
        timeout=args.timeout,
    )

    # 保存响应文件
    save_responses(result, args)

    if args.pretty:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
