import argparse
import json
import os
from typing import Any, Dict, List, Optional

import requests
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), ".env"))

ENDPOINT = "https://api.scavio.dev/api/v1/weibo/search/advanced"
# Long posts keep their full text in body; the title is cut to this length.
TITLE_LENGTH = 100


def _strip_query(url: str) -> str:
    # Weibo appends refer_flag tracking to post and user links.
    return url.split("?", 1)[0] if url else url


class WeiboSearchClient:
    """Weibo post search through the Scavio API, https://scavio.dev/docs/weibo-search-advanced

    Needs SCAVIO_API_KEY. One request per search (the first result page, about
    20 posts), no retries: each request costs 1 Scavio credit.
    """

    ENGINE_NAME = "weibo"
    ENGINE_DISPLAY_NAME = "Weibo"
    REQUIRES_API_KEY = True

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = (api_key or os.environ.get("SCAVIO_API_KEY") or "").strip()
        if not self.api_key:
            raise ValueError("SCAVIO_API_KEY is not set; the weibo channel needs a Scavio API key")
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        })

    def search(self, query: str, max_results: Optional[int] = None, timeout: int = 60) -> List[Dict[str, Any]]:
        if not query.strip():
            raise ValueError("Search keyword must not be empty")

        response = self.session.post(ENDPOINT, json={"q": query.strip()}, timeout=timeout)
        if response.status_code == 401:
            raise RuntimeError("Weibo search failed: HTTP 401, Scavio rejected SCAVIO_API_KEY")
        if response.status_code == 402:
            raise RuntimeError("Weibo search failed: HTTP 402, the Scavio account is out of credits")
        if response.status_code != 200:
            raise RuntimeError(f"Weibo search failed: HTTP {response.status_code} {response.text.strip()[:500]}")

        payload = response.json()
        raw_items = (payload.get("data") or {}).get("items")
        if not isinstance(raw_items, list):
            raise RuntimeError(f"Weibo response has no data.items list: {str(payload)[:500]}")

        results = []
        for item in raw_items:
            url = _strip_query((item.get("post_url") or "").strip())
            if not url:
                continue
            user = item.get("user") or {}
            name = (user.get("name") or "").strip()
            text = " ".join((item.get("text") or "").split())
            title = text if len(text) <= TITLE_LENGTH else text[:TITLE_LENGTH] + "..."
            images = (item.get("media") or {}).get("images") or []
            results.append({
                "title": title or f"@{name}",
                "href": url,
                "body": text,
                "engine": self.ENGINE_NAME,
                # As Weibo displays it, e.g. "11月11日 17:11" (no year) or "今天 01:30".
                # Popular posts can carry a "转赞人数超过400" badge after the time.
                "publish_date": (item.get("created_at") or "").split("转赞人数")[0].strip() or None,
                "thumbnail": images[0] if images and isinstance(images[0], str) else None,
                "post_id": item.get("id"),
                "author": name,
                "author_url": _strip_query(user.get("url") or "") or None,
                "source": item.get("source"),
                "weibo_type": item.get("weibo_type"),
            })
        return results[:max_results] if max_results is not None else results

    def format_results(self, results: List[Dict[str, Any]], query: str) -> str:
        output = [f"{self.ENGINE_DISPLAY_NAME}: {query}", f"{len(results)} results", ""]
        for i, item in enumerate(results, 1):
            output.append(f"[{i}] @{item.get('author', '')}: {item.get('title', '')}")
            output.append(f"    {item.get('href', '')}")
            if item.get("publish_date"):
                output.append(f"    {item['publish_date']}")
            output.append("")
        return "\n".join(output)


def search_weibo(
    query: str,
    max_results: Optional[int] = None,
    api_key: Optional[str] = None,
    **kwargs,
) -> List[Dict[str, Any]]:
    client = WeiboSearchClient(api_key=api_key)
    return client.search(query=query, max_results=max_results, timeout=int(kwargs.get("timeout", 60)))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Weibo post search through the Scavio API (needs SCAVIO_API_KEY; 1 credit per search)")
    parser.add_argument("query", help="Search keyword")
    parser.add_argument("-m", "--max-results", type=int, default=None, help="Keep at most this many results; default keeps the whole first page (about 20)")
    parser.add_argument("--api-key", help="Scavio API key (overrides SCAVIO_API_KEY)")
    parser.add_argument("--timeout", type=int, default=60, help="Request timeout in seconds")
    parser.add_argument("--json", action="store_true", help="JSON output")

    args = parser.parse_args()

    client = WeiboSearchClient(api_key=args.api_key)
    results = client.search(query=args.query, max_results=args.max_results, timeout=args.timeout)

    if args.json:
        print(json.dumps({"results": results}, ensure_ascii=False, indent=2))
    else:
        print(client.format_results(results, args.query))
