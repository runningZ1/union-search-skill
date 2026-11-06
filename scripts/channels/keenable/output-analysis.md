# Keenable 输出结果分析

## 容量表与结果留样

| 官方单次上限 | 模块默认 | 分页 | `limit` 作用 |
| --- | --- | --- | --- |
| `max_results` 最大 50 | 未传 `-m` 时请求 50 条 | 单次 POST，不分页 | 正数作为 `max_results` 发送（截到 1–50），并在本地再截取一次 |

资料核对日期：2026-11-03，来源 [Keenable Search API](https://docs.keenable.ai/api-reference/search)。

真实查询留样（`keenable_search.py "duckdb" -m 1 --site duckdb.org --json`，无 Key，`body` 已截断）：

```json
{
  "results": [
    {
      "title": "An analytical SQL database management system",
      "href": "http://duckdb.org",
      "body": "# Your universal\ndata wrangling tool\nDatabase anywhere\nDuckDB is an analytical database system that you can deploy anywhere: from edge devices to servers with h…",
      "engine": "keenable",
      "publish_date": null
    }
  ]
}
```

## 请求

- 无 Key：`POST https://api.keenable.ai/v1/search/public`，请求头 `X-Keenable-Title: union-search-skill`
- 有 Key：`POST https://api.keenable.ai/v1/search`，请求头 `X-API-Key`
- 请求体：`query`、`max_results`，可选 `site`、`published_after`、`published_before`

非 200 响应或缺少 `results` 数组时脚本抛错退出，不做重试或切换来源。429 错误保留 `Retry-After` 等待提示；缺少该头时提示冷却 300 秒。

免 Key 搜索限额为每个出口 IP 每小时 1,000 次且每秒最多 10 次，同 IP 共享；单次最多 50 条。官方额度与响应头说明见[模块 README](README.md#免-key-额度与请求速率)和[限流说明](../../../references/rate_limits.md#keenable-search)。

## 字段

脚本 `--json` 输出 `{results:array<object>}`，没有查询回显或总命中数。

| 字段 | 类型与缺省 | 接口映射及含义 |
| --- | --- | --- |
| `title` | 非空 string | 接口 `title`，为空时用 `url` |
| `href` | 非空 string | 接口 `url`；缺少 `url` 的条目被跳过 |
| `body` | string，缺失时 `""` | 接口 `snippet`（页面正文摘录，可能含 Markdown，可达数千字符），为空时用 `description` |
| `engine` | string，固定 `keenable` | 本地补充 |
| `publish_date` | string 或 `null` | 接口 `published_at`，ISO 8601 |
