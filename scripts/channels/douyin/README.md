# Douyin Search (Scavio API)

Douyin video search through the [Scavio API](https://scavio.dev). Each result is one video or image post with its caption, link, publish time, cover, author and like, comment, share and save counts.

## Features

- Searches Douyin by keyword and returns the first result page (about 10 videos and image posts)
- Links point at douyin.com: `https://www.douyin.com/video/<id>` for videos, `https://www.douyin.com/note/<id>` for image posts
- `publish_date` is ISO 8601 in UTC
- One request per search, no paging and no retries

## Configuration

Required, in the `.env` file at the project root:

```bash
SCAVIO_API_KEY=
```

Create the key at https://scavio.dev. Endpoint reference: https://scavio.dev/docs/douyin-search-videos

## Cost and limits

| Item | Value |
| --- | --- |
| Request | `POST https://api.scavio.dev/api/v1/douyin/search/videos`, body `{"keyword": "..."}` |
| Authentication | `Authorization: Bearer $SCAVIO_API_KEY` |
| Results per request | The first page, about 10; the channel does not page |
| Cost | 10 Scavio credits per search. A credit is about $0.001 to $0.01 depending on the plan, and new accounts get 50 free credits |
| Errors | 401 (key rejected), 402 (out of credits) and any other non-200 response exit with an error; nothing is retried |
| Latency | 5 to 8 seconds in testing |

## Usage

```bash
# Basic search
python scripts/channels/douyin/douyin_search.py "手冲咖啡教程"

# Keep 5 results, JSON output
python scripts/channels/douyin/douyin_search.py "手冲咖啡教程" -m 5 --json

# Unified entry point
python union_search_cli.py platform douyin "手冲咖啡教程" --limit 5
python union_search_cli.py search "手冲咖啡教程" --platforms douyin weibo
```

## Parameters

| Parameter | Meaning | Default |
|------|------|--------|
| `query` | Search keyword (required) | - |
| `-m, --max-results` | Keep at most this many results (cut locally; still one request) | whole first page |
| `--api-key` | Scavio API key, overrides `SCAVIO_API_KEY` | - |
| `--timeout` | Request timeout in seconds | 60 |
| `--json` | JSON output | no |

Output fields are described in [output-analysis.md](output-analysis.md).
