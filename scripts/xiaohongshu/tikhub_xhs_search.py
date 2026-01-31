#!/usr/bin/env python3
import argparse
import http.client
import json
import os
import re
import sys
from urllib.parse import urlencode
from datetime import datetime

DEFAULT_HOST = "api.tikhub.io"
DEFAULT_PATH = "/api/v1/xiaohongshu/app/search_notes"
DEFAULT_SAVE_SUFFIX = "xhs_search_notes"


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


def parse_args():
    examples = (
        "Examples:\n"
        "  python tikhub_xhs_search.py \"美食\"\n"
        "  python tikhub_xhs_search.py --keyword 美食 --page 2 --sort-type general\n"
        "  python tikhub_xhs_search.py --filter-note-type 不限 --filter-note-time 不限\n"
    )
    parser = argparse.ArgumentParser(
        description="TikHub Xiaohongshu search notes client",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog=examples,
    )
    parser.add_argument("--env-file", default=_env_file_from_argv(sys.argv), help="Env file path")
    parser.add_argument("keyword", nargs="?", help="Search keyword (positional)")
    parser.add_argument("--keyword", dest="keyword_opt", help="Search keyword (overrides positional)")
    parser.add_argument("--token", help="API token")
    parser.add_argument("--page", type=int, help="Page number")
    parser.add_argument("--search-id", help="Search ID from XHS API")
    parser.add_argument("--session-id", help="Session ID from XHS API")
    parser.add_argument("--sort-type", help="Sort type, e.g. general")
    parser.add_argument("--filter-note-type", help="Filter note type, e.g. 不限")
    parser.add_argument("--filter-note-time", help="Filter note time, e.g. 不限/一天内/一周内/半年内")
    parser.add_argument("--host", help="API host")
    parser.add_argument("--path", help="API path")
    parser.add_argument("--timeout", type=int, help="Timeout seconds")
    parser.add_argument("--limit", type=int, help="Max items to output (default: all)")
    parser.add_argument("--sort-by", help="Sort by stats field: liked_count/collected_count/comments_count")
    parser.add_argument("--sort-order", choices=["asc", "desc"], help="Sort order (asc/desc)")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON")
    return parser.parse_args()


def apply_env_defaults(args):
    if args.token is None:
        args.token = _env_str("TIKHUB_TOKEN", "")

    keyword = args.keyword_opt if args.keyword_opt is not None else args.keyword
    if keyword is None:
        keyword = _env_str("TIKHUB_XHS_KEYWORD", "")
    args.keyword = keyword

    if args.page is None:
        args.page = _env_int("TIKHUB_XHS_PAGE", 1)
    if args.search_id is None:
        args.search_id = _env_str("TIKHUB_XHS_SEARCH_ID", "")
    if args.session_id is None:
        args.session_id = _env_str("TIKHUB_XHS_SESSION_ID", "")
    if args.sort_type is None:
        args.sort_type = _env_str("TIKHUB_XHS_SORT_TYPE", "general")
    if args.filter_note_type is None:
        args.filter_note_type = _env_str("TIKHUB_XHS_FILTER_NOTE_TYPE", "不限")
    if args.filter_note_time is None:
        args.filter_note_time = _env_str("TIKHUB_XHS_FILTER_NOTE_TIME", "不限")
    if args.host is None:
        args.host = _env_str("TIKHUB_HOST", DEFAULT_HOST)
    if args.path is None:
        args.path = _env_str("TIKHUB_XHS_PATH", DEFAULT_PATH)
    if args.timeout is None:
        args.timeout = _env_int("TIKHUB_TIMEOUT", 30)
    if args.limit is None:
        args.limit = _env_int("TIKHUB_XHS_LIMIT", -1)
    if args.sort_by is None:
        args.sort_by = _env_str("TIKHUB_XHS_SORT_BY", "")
    if args.sort_order is None:
        args.sort_order = _env_str("TIKHUB_XHS_SORT_ORDER", "desc")
    return args


def fetch_search_notes(token, params, host=DEFAULT_HOST, path=DEFAULT_PATH, timeout=30):
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


def _dedupe_keep_order(values):
    seen = set()
    output = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        output.append(value)
    return output


def extract_tags_from_text(text):
    if not text:
        return []
    matches = re.findall(r"#([^#\\s]+)", text)
    return _dedupe_keep_order([f"#{match}" for match in matches])


def infer_note_type(note):
    raw_type = note.get("type")
    if isinstance(raw_type, str):
        lowered = raw_type.lower()
        if "video" in lowered:
            return "video"
        if lowered in ("normal", "image", "note"):
            return "image"
    images = note.get("images_list") or []
    if isinstance(images, list) and images:
        return "image"
    if note.get("has_music"):
        return "video"
    return "unknown"


def _coerce_int(value):
    if value is None:
        return 0
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, (int, float)):
        return int(value)
    try:
        return int(str(value))
    except ValueError:
        return 0


def sort_items(items, sort_by, sort_order):
    if not sort_by:
        return items
    reverse = sort_order != "asc"
    return sorted(
        items,
        key=lambda item: _coerce_int((item.get("stats") or {}).get(sort_by)),
        reverse=reverse,
    )


def extract_items(result):
    items = []
    data = result.get("data") if isinstance(result, dict) else None
    if isinstance(data, dict):
        inner = data.get("data")
        if isinstance(inner, dict) and isinstance(inner.get("items"), list):
            items = inner.get("items", [])
        elif isinstance(data.get("items"), list):
            items = data.get("items", [])

    output = []
    for entry in items:
        if not isinstance(entry, dict):
            continue
        note = entry.get("note")
        if not isinstance(note, dict):
            continue
        stats = {
            "liked_count": note.get("liked_count"),
            "collected_count": note.get("collected_count"),
            "comments_count": note.get("comments_count"),
        }
        title = (note.get("title") or "").strip()
        desc = (note.get("desc") or "").strip()
        tags = _dedupe_keep_order(extract_tags_from_text(title) + extract_tags_from_text(desc))
        user = note.get("user") or {}
        output.append(
            {
                "note_id": note.get("id"),
                "title": title,
                "tags": tags,
                "desc": desc,
                "note_type": infer_note_type(note),
                "raw_type": note.get("type"),
                "stats": stats,
                "author": {
                    "user_id": user.get("userid"),
                    "red_id": user.get("red_id"),
                    "nickname": user.get("nickname"),
                },
            }
        )
    return output


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
        "page": args.page,
        "search_id": args.search_id,
        "session_id": args.session_id,
        "sort_type": args.sort_type,
        "filter_note_type": args.filter_note_type,
        "filter_note_time": args.filter_note_time,
    }

    result = fetch_search_notes(
        token=args.token,
        params=params,
        host=args.host,
        path=args.path,
        timeout=args.timeout,
    )

    base_dir = os.path.dirname(os.path.abspath(__file__))
    save_dir = os.path.join(base_dir, "responses")
    os.makedirs(save_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}_{DEFAULT_SAVE_SUFFIX}.json"
    save_path = os.path.join(save_dir, filename)
    with open(save_path, "w", encoding="utf-8") as handle:
        json.dump(result, handle, ensure_ascii=False)

    items = extract_items(result)
    items = sort_items(items, args.sort_by, args.sort_order)
    if args.limit is not None and args.limit >= 0:
        items = items[: args.limit]
    output = {
        "saved_to": save_path,
        "items": items,
    }

    if args.pretty:
        print(json.dumps(output, indent=2, ensure_ascii=False))
    else:
        print(json.dumps(output, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
