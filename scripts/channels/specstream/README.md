# SpecStream Search

SpecStream 的 Search API，返回网页结果，每条带来源链接和摘要，页面有发布日期时一并返回。

## 功能特性

- 使用 `speed=fast`：只返回搜索结果与摘要，不生成答案
- 查询中支持 `site:`、`-site:`、引号短语、`filetype:`、`after:`、`before:`
- `--news` 返回新闻结果，按发布时间从新到旧，带发布方与发布时间
- 可指定语言与国家

## 配置

在项目根目录的 `.env` 文件中添加：

```bash
SPECSTREAM_API_KEY=your_specstream_api_key_here
# 默认 https://api.specstream.ai/v1/web-search
SPECSTREAM_SEARCH_ENDPOINT=
```

API Key 在 [SpecStream 工作区](https://specstream.ai/workspace) 的 Agents & API 中创建。用于搜索的 Key 需要 `finds:spend` 权限和大于 0 的消费上限。

## 使用示例

```bash
# 基础搜索
python scripts/channels/specstream/specstream_search.py "AI agent" -m 10

# 限定域名与日期
python scripts/channels/specstream/specstream_search.py "AI agent site:github.com after:2026-01"

# 新闻
python scripts/channels/specstream/specstream_search.py "AI agent" --news

# JSON 输出
python scripts/channels/specstream/specstream_search.py "AI agent" --json
```

## 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `query` | 搜索关键词（必需），最多 2,000 字符 | - |
| `-m, --max-results` | 结果数量上限，1 到 100 | 10 |
| `--news` | 返回新闻结果 | False |
| `--language` | 两位 ISO 639-1 语言代码，如 `zh` | - |
| `--country` | 两位 ISO 3166-1 国家代码，如 `CN` | - |
| `--api-key` | API Key（优先于环境变量） | - |
| `--endpoint` | 接口地址 | https://api.specstream.ai/v1/web-search |
| `--timeout` | 请求超时秒数 | 30 |
| `--json` | JSON 输出 | False |

## 输出字段

`title`、`href`、`body`、`engine`、`publish_date`、`site`。

## 限制

- 10 条以内每次 0.005 美元，每多 10 条加 0.006 美元
- 每分钟调用用完或服务繁忙时返回 HTTP 503 和 `Retry-After`，不计费
- 无效或过期的 Key 返回 HTTP 401（`invalid_token`）

## 相关链接

- [Search API](https://specstream.ai/search-api)
- [OpenAPI](https://api.specstream.ai/openapi.json)
