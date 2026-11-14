# SpecStream Search 输出结果分析

覆盖 `specstream_search.py` 的客户端、`search_specstream`、JSON 脚本及 `union_search.py::_search_specstream`。当前入口发送 `GET /v1/web-search`，默认 `speed=fast`，`--news` 时改为新闻结果。

## 原生路径与完整模块字段

源码读取 `data.sources[]`。客户端返回数组，脚本输出含 results 的对象；这里只说明已读取结构。

| 模块字段 | 类型、上游映射与缺失规则 |
| --- | --- |
| title | string；title 或 url，去除空白 |
| href | string；url 去除空白；空地址条目丢弃 |
| body | string；snippet 去除空白，缺失为空字符串 |
| engine | string；固定 specstream |
| publish_date | 原值或 null；优先 published_at（新闻结果），其次 published |
| site | 原值或 null；上游同名字段，结果所在站点 |

上游的 `cited`、`modified`、`source`、`file_type`、`read_at`、`excerpt`、`meta` 未映射。顶层 `answer`、`rows`、`passages` 在 `speed=fast` 下不生成，模块也不读取；`request_id`、`price_usd`、`next_page` 未保留。

## 保留边界与统一 CLI

HTTP 非 200 会失败，错误信息带响应正文前 500 字符，有 `Retry-After` 时一并附上。响应缺少 `data.sources` 数组也会失败。模块不重试，不切换来源。

adapter 读取 results 并再次限量。单渠道统一输出位于 `data.items[]`，联合搜索位于 `data.results.specstream.items[]`；联合 `data.final_items[]` 添加 `_source_platform`。CLI 外层 ok/errors、渠道 total 为执行信息。

## 容量概览

| 官方每请求上限 | 模块默认 | 分页行为 | `--limit` 作用 |
| --- | --- | --- | --- |
| `num` 1 到 100 | 发送 `num=10` | 接口有 `page` 参数（1 到 10）；模块只请求第一页 | 不指定或 0 时发送 10；正数发送同值（最多 100），并用于模块与 adapter 本地切片 |

## 常用参数与单次容量

核查日期：2026-11-10。官方来源：[OpenAPI](https://api.specstream.ai/openapi.json)。

| 英文参数 | 含义、默认与范围 |
| --- | --- |
| `q` | 查询，1 到 2,000 字符；支持 `site:`、`-site:`、引号短语、`filetype:`、`after:`、`before:` |
| `num` | 结果数量 1 到 100；模块默认 10 |
| `speed` | 模块发送 `fast`：只返回结果与摘要 |
| `news` | `--news` 时发送 `true`，按发布时间从新到旧 |
| `language`、`country` | 两位 ISO 代码，默认不发送 |
| `timeout` | 模块默认 30 秒 |

## 证据范围

2026-11-10 运行 `python union_search_cli.py platform specstream "rust async runtime" --limit 3 --fail-on-platform-error`，`ok: true`，3 条结果，耗时约 2.1 秒；三条的 title、url、摘要均为 string，`published` 均为 null。`--news`、`--language`、`--country` 及超过 10 条的请求未验证。
