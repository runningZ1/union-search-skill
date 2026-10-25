# YouTube 输出结果分析

## 容量表与结果留样

| 官方单次上限 | 模块默认 | 分页 | `limit` 作用 |
| --- | --- | --- | --- |
| search.list 每请求最多 50、API 默认 5；commentThreads.list 最多 100、API 默认 20 | 未指定搜索 limit 时主动请求 50；可选评论默认请求每视频 10 个顶层评论线程 | 搜索与评论各只取一页，均不处理 nextPageToken；搜索后另请求视频详情 | 搜索请求 `min(limit,50)` 并在统一层本地截取；统一 `0` 请求默认 50，独立 `0` 发送 maxResults=0 |

真实视频结果见 [搜索结果样例](examples/search-result.json)。文件为统一 CLI 的 `data.results.youtube` 渠道对象，属于 CLI 渠道对象证据层；视频条目已由搜索与详情响应重建，未保存原始 HTTP 响应。3 条样例验证视频字段，评论字段和容量依据下文已有资料与实现，评论未留样。

## 常用参数与返回数量

资料整理日期：2026-10-25。依据 `youtube_search.py` 与官方 Data API 文档；此次未重新执行搜索或评论请求。

| 参数 | 含义 | 默认值或未指定行为 | 范围与实际约束 |
| --- | --- | --- | --- |
| `keyword` / `--keyword` | 视频关键词 | 可用位置参数；命名参数优先 | 搜索固定 `type=video`，不会输出频道或播放列表 |
| `--limit` | 本次搜索请求的视频数量 | `None`，模块主动发送 `maxResults=50` | 发送 `min(limit, 50)`；官方允许 `0..50`，本地没有负数校验；大于 50 仍只请求 50 |
| 统一 `--limit` | 每渠道视频输出上限 | 未指定或 `0` 为 `None`，模块请求 50 | 正整数既控制上述 maxResults，又在详情返回后本地切片；不增加页数 |
| `--order` | 视频排序 | `relevance` | 本地允许 `relevance/date/rating/viewCount/title` |
| `--region` | 按国家可观看性选择视频 | `US` | API 的 `regionCode`，使用 ISO 3166-1 alpha-2 国家代码 |
| `--language` | 搜索相关语言偏好 | 本地字符串 `zh-CN` | 发给 `relevanceLanguage`；官方一般使用 ISO 639-1，中文说明为 `zh-Hans/zh-Hant`；本地不校验，也不自动改写默认值，不保证严格排除其他语言 |
| `--include-comments` | 为每个视频获取热门评论 | `false` | 独立脚本选项；统一编排默认不传入 |
| `--max-comments` | 每个视频的评论线程请求数量 | `10` | 模块发送 `min(N,100)`；官方允许 `1..100`，不自动获取下一页 |
| `--json/--pretty/--markdown` | 展示格式 | 文本，pretty 为 false | JSON、Markdown 开关；两者同时设置时优先 JSON |

**官方 `search.list` 每请求最多 50 条，省略 API 参数时默认 5 条；当前模块明确发送数量，未指定本地 limit 时请求 50 条。** 搜索只请求一页，忽略 `nextPageToken`，随后用视频 ID 获取详情；返回详情可能少于搜索 ID 数量，因此本实现每次最多输出 50 个视频，设置更大 limit 无法突破这一范围。

评论的 `commentThreads.list` 每请求最多 100 个线程，官方默认 20；当前模块默认明确请求 10，且只提取各线程顶层评论，不获取完整回复。视频数与每视频评论数分别计数。官方可用 pageToken 翻页，但本模块的搜索与评论均未实现自动翻页。

统一 `--limit 0` 表示取消统一层数量限制；独立脚本 `--limit 0` 会发送 API `maxResults=0`，两者语义不同。不指定统一 limit 只取消额外切片，仍保留模块的单页 50 上限。检索匹配、地区可用性、视频删除或权限变化、评论关闭及账号额度均会改变实际数量。官方针对特定 channelId 等条件的搜索范围限制不适用于当前仅关键词加 type=video 的请求。

官方来源（资料整理日期：2026-10-25）：[search.list 参数与分页](https://developers.google.com/youtube/v3/docs/search/list)、[commentThreads.list 参数](https://developers.google.com/youtube/v3/docs/commentThreads/list)。

## 输出层次

覆盖统一渠道 `youtube` 和本目录 `youtube_search.py`。查询先调用 Data API `search` 获取 `items[].id.videoId`，随后调用 `videos` 获取 `snippet`、`statistics`、`contentDetails`。模块 JSON 输出为视频对象数组；统一 CLI 将数组保存在 `data.items`（单渠道）或 `data.results.youtube.items`（联合查询）。搜索响应的 `nextPageToken`、`pageInfo` 等不会进入视频数组，不自动遍历分页。

## 视频字段

| 字段 | 类型与来源 | 空值及含义 |
|---|---|---|
| `rank` | integer，本地从 1 编号 | 详情数组次序，不是上游相关性评分 |
| `video_id`、`url` | string，视频 ID 与拼接的观看地址 | `url` 为视频网页地址 |
| `title`、`description` | string，`snippet.title/description` | 缺失为 `""`；description 是视频描述，不是字幕或视频正文 |
| `channel_title`、`channel_id` | string，`snippet.channelTitle/channelId` | 缺失为 `""` |
| `published_at` | string，`snippet.publishedAt` | 通常为带时区的 ISO 时间；缺失为 `""` |
| `thumbnails` | object，`snippet.thumbnails` | 缺失为 `{}`；按 default/medium/high 等规格包含 `url`、`width`、`height`，规格不保证齐全 |
| `tags` | array，`snippet.tags` | 缺失为 `[]`，不表示视频没有主题 |
| `category_id` | string，`snippet.categoryId` | 分类编号，不是分类名称；缺失为 `""` |
| `duration_raw` | string，`contentDetails.duration` | ISO 8601 时长，例如 PT 开头；缺失为 `""` |
| `duration` | string，本地格式化 | 分秒或时分秒显示值；格式化未匹配时保留原值 |
| `definition` | string，`contentDetails.definition` | 清晰度标记；缺失为 `""` |
| `caption` | string，`contentDetails.caption` | 上游字符串标记，不能按非空字符串直接判定字幕存在 |
| `statistics` | object | `view_count`、`like_count`、`comment_count` 均转成 integer，缺失补 0；0 无法区分真实零次与上游未提供 |

独立脚本启用评论选项时，追加 `comments` 数组，元素为 `author`、`author_channel_id`、`text`、`like_count`、`published_at`、`updated_at`；评论失败可能仅出现 `comments_error`。`text` 来自 `textDisplay`，可能含 HTML。统一搜索默认不请求评论，不能把这些条件字段当作默认字段。

## CLI 保留范围

当前 API 联合查询保留上述视频对象，不会将其全部转换为网页的 `title/url/content/published` 结构。`published_at`、`statistics` 应从渠道条目读取；统一信封的 `timestamp` 是调用时间。不存在价格、服装品类或商品库存等结构化字段。

## 验证范围

以 `sustainable apparel textile industry` 实测返回 3 条，确认视频字段、缩略图对象、标签数组和三项计数存在。证据：`.work/output-analysis/api.json` 的 `data.results.youtube.items`。评论结构依据 `get_video_comments()`，本轮未调用评论接口。实现见 `youtube_search.py` 的 `get_video_details()` 与编排器 `_search_youtube()`。
