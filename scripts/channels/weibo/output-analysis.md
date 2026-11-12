# Weibo output analysis

## Capacity and sample

| Per request | Module default | Paging | `limit` |
| --- | --- | --- | --- |
| The first result page, about 20 posts | One request | None | Cuts the returned page locally; the request is the same |

Checked 2026-11-12 against the live API.

Real query sample (`weibo_search.py "新能源汽车" --json`, one result):

```json
{
  "results": [
    {
      "title": "中国自己的V8发动机期待领克和路特斯上搭载，并尽快上车#汽场全开##大v聊车##新能源汽车﻿﻿#​",
      "href": "https://weibo.com/1898907123/RqSYQkuFU",
      "body": "中国自己的V8发动机期待领克和路特斯上搭载，并尽快上车#汽场全开##大v聊车##新能源汽车﻿﻿#​",
      "engine": "weibo",
      "publish_date": "11月11日 14:45",
      "thumbnail": "https://wx3.sinaimg.cn/large/712f05f3gy1iixm1u8i56j20u02ak4a4.jpg",
      "post_id": "5364078764884478",
      "author": "痛快舒畅",
      "author_url": "https://weibo.com/1898907123",
      "source": "vivo X Fold5",
      "weibo_type": "original"
    }
  ]
}
```

## Request

`POST https://api.scavio.dev/api/v1/weibo/search/advanced` with `Authorization: Bearer $SCAVIO_API_KEY` and body `{"q": "..."}`. The response carries `data.items`; a non-200 response, or one without a `data.items` list, exits with an error. There are no retries and no other source.

## Fields

The script's `--json` output is `{results: array<object>}`.

| Field | Type and default | Source |
| --- | --- | --- |
| `title` | non-empty string | `text` with whitespace collapsed, cut to 100 characters; `@<author>` when the text is empty |
| `href` | non-empty string | `post_url` without its query string (`refer_flag`); items without `post_url` are skipped |
| `body` | string | The full `text`, whitespace collapsed |
| `engine` | string, always `weibo` | added locally |
| `publish_date` | string or `null` | `created_at` as Weibo displays it (`11月10日 06:51`, `今天 01:30`, `27分钟前`), with a trailing `转赞人数超过N` badge removed. No year; not converted to ISO 8601 |
| `thumbnail` | string or `null` | The first entry of `media.images` |
| `post_id` | string | `id` |
| `author`, `author_url` | string, string or `null` | `user.name`, `user.url` without its query string |
| `source` | string or `null` | The posting client, such as a phone model |
| `weibo_type` | string | `weibo_type`, such as `original` |

This search does not return repost, comment or like counts.
