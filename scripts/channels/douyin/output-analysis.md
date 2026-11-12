# Douyin output analysis

## Capacity and sample

| Per request | Module default | Paging | `limit` |
| --- | --- | --- | --- |
| The first result page, about 10 items | One request | None | Cuts the returned page locally; the request is the same |

Checked 2026-11-12 against the live API.

Real query sample (`douyin_search.py "手冲咖啡教程" --json`, first result, `thumbnail` shortened):

```json
{
  "results": [
    {
      "title": "手冲教程 | 别被专业术语吓住，这才是普通人能学会的手冲！ #手冲咖啡 #手冲咖啡教程 #自制咖啡 #咖啡教程 #手冲咖啡入门",
      "href": "https://www.douyin.com/video/7615192143656783113",
      "body": "手冲教程 | 别被专业术语吓住，这才是普通人能学会的手冲！ #手冲咖啡 #手冲咖啡教程 #自制咖啡 #咖啡教程 #手冲咖啡入门 (@尹师傅（喜欢咖啡版） · 10550 likes · 344 comments · 2833 shares · 7388 saves)",
      "engine": "douyin",
      "publish_date": "2026-03-09T09:54:55Z",
      "thumbnail": "https://p9-sign.douyinpic.com/tos-cn-i-dy/4bfe092fb3e0495b8d...",
      "aweme_id": "7615192143656783113",
      "type": "video",
      "author": "尹师傅（喜欢咖啡版）",
      "author_sec_uid": "MS4wLjABAAAAxuH5ANL_NMDU_tshEmVy0kHbNv9wB2Wqwi2Q6GJVbdEHLfM7uTmuRE4HzEzHH9wT",
      "author_follower_count": 5950,
      "like_count": 10550,
      "comment_count": 344,
      "share_count": 2833,
      "collect_count": 7388,
      "hashtags": ["手冲咖啡", "手冲咖啡教程", "自制咖啡", "咖啡教程", "手冲咖啡入门"]
    }
  ]
}
```

## Request

`POST https://api.scavio.dev/api/v1/douyin/search/videos` with `Authorization: Bearer $SCAVIO_API_KEY` and body `{"keyword": "..."}`. The response carries `data.items`; a non-200 response, or one without a `data.items` list, exits with an error. There are no retries and no other source.

## Fields

The script's `--json` output is `{results: array<object>}`.

| Field | Type and default | Source |
| --- | --- | --- |
| `title` | non-empty string | `desc` with whitespace collapsed, cut to 100 characters; `@<author>` when the caption is empty |
| `href` | non-empty string | `https://www.douyin.com/note/<aweme_id>` when `share_url` is a `/share/note/` link (image post), otherwise `https://www.douyin.com/video/<aweme_id>`; items without `aweme_id` are skipped |
| `body` | string | The full caption followed by the author and counts |
| `engine` | string, always `douyin` | added locally |
| `publish_date` | string or `null` | `create_time` (Unix seconds) as ISO 8601 UTC |
| `thumbnail` | string or `null` | `video.cover` |
| `aweme_id` | string | `aweme_id` |
| `type` | `video` or `note` | from `share_url` |
| `author`, `author_sec_uid`, `author_follower_count` | string, string, integer | `author.nickname`, `author.sec_uid`, `author.follower_count` |
| `like_count`, `comment_count`, `share_count`, `collect_count` | integer | `statistics.digg_count`, `comment_count`, `share_count`, `collect_count` |
| `hashtags` | array of string | `hashtags[].name` |
