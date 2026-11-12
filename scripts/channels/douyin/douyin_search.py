import argparse
import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import requests
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), ".env"))

ENDPOINT = "https://api.scavio.dev/api/v1/douyin/search/videos"
# Long captions keep their full text in body; the title is cut to this length.
TITLE_LENGTH = 100


class DouyinSearchClient:
    """Douyin video search through the Scavio API, https://scavio.dev/docs/douyin-search-videos

    Needs SCAVIO_API_KEY. One request per search (the first result page, about
    10 videos), no retries: each request costs 10 Scavio credits.
    """

    ENGINE_NAME = "douyin"
    ENGINE_DISPLAY_NAME = "Douyin"
    REQUIRES_API_KEY = True

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = (api_key or os.environ.get("SCAVIO_API_KEY") or "").strip()
        if not self.api_key:
            raise ValueError("SCAVIO_API_KEY is not set; the douyin channel needs a Scavio API key")
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        })

    def search(self, query: str, max_results: Optional[int] = None, timeout: int = 60) -> List[Dict[str, Any]]:
        if not query.strip():
            raise ValueError("Search keyword must not be empty")

        response = self.session.post(ENDPOINT, json={"keyword": query.strip()}, timeout=timeout)
        if response.status_code == 401:
            raise RuntimeError("Douyin search failed: HTTP 401, Scavio rejected SCAVIO_API_KEY")
        if response.status_code == 402:
            raise RuntimeError("Douyin search failed: HTTP 402, the Scavio account is out of credits")
        if response.status_code != 200:
            raise RuntimeError(f"Douyin search failed: HTTP {response.status_code} {response.text.strip()[:500]}")

        payload = response.json()
        raw_items = (payload.get("data") or {}).get("items")
        if not isinstance(raw_items, list):
            raise RuntimeError(f"Douyin response has no data.items list: {str(payload)[:500]}")

        results = []
        for item in raw_items:
            aweme_id = str(item.get("aweme_id") or "").strip()
            if not aweme_id:
                continue
            # Image posts are shared as /share/note/<id> and open at douyin.com/note/<id>.
            kind = "note" if "/share/note/" in (item.get("share_url") or "") else "video"
            author = item.get("author") or {}
            stats = item.get("statistics") or {}
            nickname = (author.get("nickname") or "").strip()
            desc = " ".join((item.get("desc") or "").split())
            created = item.get("create_time")
            title = desc if len(desc) <= TITLE_LENGTH else desc[:TITLE_LENGTH] + "..."
            counts = (
                f"@{nickname} · {stats.get('digg_count', 0)} likes · {stats.get('comment_count', 0)} comments"
                f" · {stats.get('share_count', 0)} shares · {stats.get('collect_count', 0)} saves"
            )
            results.append({
                "title": title or f"@{nickname}",
                "href": f"https://www.douyin.com/{kind}/{aweme_id}",
                "body": f"{desc} ({counts})" if desc else counts,
                "engine": self.ENGINE_NAME,
                "publish_date": (
                    datetime.fromtimestamp(created, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
                    if isinstance(created, int) and created > 0 else None
                ),
                "thumbnail": (item.get("video") or {}).get("cover") or None,
                "aweme_id": aweme_id,
                "type": kind,
                "author": nickname,
                "author_sec_uid": author.get("sec_uid"),
                "author_follower_count": author.get("follower_count"),
                "like_count": stats.get("digg_count"),
                "comment_count": stats.get("comment_count"),
                "share_count": stats.get("share_count"),
                "collect_count": stats.get("collect_count"),
                "hashtags": [tag.get("name") for tag in item.get("hashtags") or [] if tag.get("name")],
            })
        return results[:max_results] if max_results is not None else results

    def format_results(self, results: List[Dict[str, Any]], query: str) -> str:
        output = [f"{self.ENGINE_DISPLAY_NAME}: {query}", f"{len(results)} results", ""]
        for i, item in enumerate(results, 1):
            output.append(f"[{i}] {item.get('title', '')}")
            output.append(f"    {item.get('href', '')}")
            if item.get("publish_date"):
                output.append(f"    {item['publish_date']}")
            output.append(f"    {item.get('body', '')}")
            output.append("")
        return "\n".join(output)


def search_douyin(
    query: str,
    max_results: Optional[int] = None,
    api_key: Optional[str] = None,
    **kwargs,
) -> List[Dict[str, Any]]:
    client = DouyinSearchClient(api_key=api_key)
    return client.search(query=query, max_results=max_results, timeout=int(kwargs.get("timeout", 60)))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Douyin video search through the Scavio API (needs SCAVIO_API_KEY; 10 credits per search)")
    parser.add_argument("query", help="Search keyword")
    parser.add_argument("-m", "--max-results", type=int, default=None, help="Keep at most this many results; default keeps the whole first page (about 10)")
    parser.add_argument("--api-key", help="Scavio API key (overrides SCAVIO_API_KEY)")
    parser.add_argument("--timeout", type=int, default=60, help="Request timeout in seconds")
    parser.add_argument("--json", action="store_true", help="JSON output")

    args = parser.parse_args()

    client = DouyinSearchClient(api_key=args.api_key)
    results = client.search(query=args.query, max_results=args.max_results, timeout=args.timeout)

    if args.json:
        print(json.dumps({"results": results}, ensure_ascii=False, indent=2))
    else:
        print(client.format_results(results, args.query))
