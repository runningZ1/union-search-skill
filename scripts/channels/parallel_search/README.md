# Parallel Search

面向 AI Agent 的网页搜索接口，用自然语言目标加关键词短语检索，返回按相关度排序的 Markdown 摘录。

## 功能特性

- 同时提交搜索目标与多条关键词短语
- 四种模式：`turbo`、`fast`、`basic`、`advanced`
- 可按国家、域名白名单、域名黑名单、发布日期过滤
- 结果包含标题、链接、发布日期与摘录

## 配置

在项目根目录的 `.env` 文件中添加：

```bash
PARALLEL_API_KEY=your_parallel_api_key_here
# 默认 https://api.parallel.ai/v1/search
PARALLEL_SEARCH_ENDPOINT=
# 默认 fast，可选 turbo、basic、advanced
PARALLEL_SEARCH_MODE=fast
```

API Key 在 [Parallel Platform](https://platform.parallel.ai) 创建。欧盟节点 `https://eu.parallel.ai` 只接受 `basic` 模式。

## 使用示例

```bash
# 基础搜索
python scripts/channels/parallel_search/parallel_search.py "AI agent" -m 10

# 指定目标与多条关键词
python scripts/channels/parallel_search/parallel_search.py "AI agent" \
  --objective "Find recent product announcements for AI agent frameworks" \
  --search-query "AI agent framework release" \
  --search-query "AI agent benchmark 2026"

# 限定域名与日期
python scripts/channels/parallel_search/parallel_search.py "AI agent" --include-domain github.com --after-date 2026-01-01

# JSON 输出
python scripts/channels/parallel_search/parallel_search.py "AI agent" --json
```

## 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `query` | 搜索关键词（必需），未指定 objective 时同时作为搜索目标 | - |
| `-m, --max-results` | 结果数量上限 | 10 |
| `--objective` | 自然语言搜索目标 | query |
| `--search-query` | 关键词短语，可重复传入 | query |
| `--mode` | `turbo`、`fast`、`basic`、`advanced` | fast |
| `--location` | 两位国家代码，如 `us`、`jp` | - |
| `--include-domain` | 域名白名单，可重复传入；设置后忽略黑名单 | - |
| `--exclude-domain` | 域名黑名单，可重复传入 | - |
| `--after-date` | 发布日期下限，`YYYY-MM-DD` | - |
| `--api-key` | API Key（优先于环境变量） | - |
| `--endpoint` | 接口地址 | https://api.parallel.ai/v1/search |
| `--timeout` | 请求超时秒数 | 30 |
| `--json` | JSON 输出 | False |

## 输出字段

`title`、`href`、`body`、`engine`、`publish_date`、`search_id`、`session_id`、`warnings`。

## 模式

| 模式 | 特点 |
|------|------|
| `turbo` | 延迟最低，p50 约 200 毫秒 |
| `fast` | 约 700 毫秒，本项目默认值 |
| `basic` | 低延迟，适合 2-3 条关键词 |
| `advanced` | 官方默认值，质量最高，约 3 秒 |

## 限制

- 默认 600 次/分钟
- 白名单与黑名单条目合计不超过 200 个
- 参数校验失败返回 HTTP 422

## 相关链接

- [Search API Quickstart](https://docs.parallel.ai/search/search-quickstart)
- [API Reference](https://docs.parallel.ai/api-reference/search/search)
- [Rate Limits](https://docs.parallel.ai/getting-started/rate-limits)
