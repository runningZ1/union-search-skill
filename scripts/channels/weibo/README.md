# Weibo Search (Scavio API)

Weibo post search through the [Scavio API](https://scavio.dev). Each result is one post with its text, link, time, first image, author and posting client.

## Features

- Searches Weibo by keyword and returns the first result page (about 20 posts)
- Links point at the post on weibo.com, without the `refer_flag` tracking parameter
- `publish_date` is passed on as Weibo shows it, such as `11月10日 06:51`, `今天 01:30` or `27分钟前`; it has no year and is not converted
- One request per search, no paging and no retries

## Configuration

Required, in the `.env` file at the project root:

```bash
SCAVIO_API_KEY=
```

Create the key at https://scavio.dev. Endpoint reference: https://scavio.dev/docs/weibo-search-advanced

## Cost and limits

| Item | Value |
| --- | --- |
| Request | `POST https://api.scavio.dev/api/v1/weibo/search/advanced`, body `{"q": "..."}` |
| Authentication | `Authorization: Bearer $SCAVIO_API_KEY` |
| Results per request | The first page, about 20; the channel does not page |
| Cost | 1 Scavio credit per search. A credit is about $0.001 to $0.01 depending on the plan, and new accounts get 50 free credits |
| Errors | 401 (key rejected), 402 (out of credits) and any other non-200 response exit with an error; nothing is retried |
| Latency | 2 to 3 seconds in testing |

## Usage

```bash
# Basic search
python scripts/channels/weibo/weibo_search.py "新能源汽车"

# Keep 5 results, JSON output
python scripts/channels/weibo/weibo_search.py "新能源汽车" -m 5 --json

# Unified entry point
python union_search_cli.py platform weibo "新能源汽车" --limit 5
python union_search_cli.py search "新能源汽车" --group social
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
