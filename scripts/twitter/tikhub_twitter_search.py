#!/usr/bin/env python3
import argparse
import http.client
import json
import os
import sys
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
        args.cursor = _env_str("TIKHUB_TWITTER_CURSOR", "None")
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
        "cursor": args.cursor,
    }

    result = fetch_search_timeline(
        token=args.token,
        params=params,
        host=args.host,
        path=args.path,
        timeout=args.timeout,
    )

    if args.pretty:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
