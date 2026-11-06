# Keenable Search

面向 AI Agent 的网页搜索接口，返回标题、链接、发布时间与较长的正文摘录。默认走免 API Key 的公共端点，配置 `KEENABLE_API_KEY` 后改用带 Key 的正式端点、额度更高。

## 功能特性

- 无需 API Key 即可使用（公共端点按 IP 限流）
- 单次最多 50 条结果
- 可按域名（`site`）与发布时间（`published_after`、`published_before`）过滤，时间支持 `YYYY-MM-DD` 或相对时间 `1d`、`7d`、`1mo`、`1y`
- 结果含 `publish_date`（接口有该信息时）

## 配置

可选，在项目根目录的 `.env` 文件中添加：

```bash
# 不填时调用免 Key 公共端点 /v1/search/public
KEENABLE_API_KEY=
# 默认 https://api.keenable.ai/v1/search
KEENABLE_SEARCH_ENDPOINT=
```

API Key 在 [Keenable 控制台](https://keenable.ai) 创建，接口说明见 [官方文档](https://docs.keenable.ai/api-reference/search)。

## 免 Key 额度与请求速率

按 [官方限流文档](https://docs.keenable.ai/rate-limits)（2026-11-05 核查）：

| 项目 | 免 Key 搜索端点的限制 |
| --- | --- |
| 请求地址 | `POST https://api.keenable.ai/v1/search/public` |
| 认证 | 无需账号/API Key；必须提供应用标识 `X-Keenable-Title: union-search-skill` |
| 小时额度 | 每个出口 IP 每小时 1,000 次搜索请求 |
| 瞬时速率 | 同时受每个出口 IP 每秒最多 10 次请求限制 |
| 共享范围 | 同一 IP 的所有调用方共享；搜索与 fetch 端点分别计数 |
| 单次结果数 | 最多 50 条；统一 CLI 默认与 `--limit 0` 均不自动分页 |
| 费用 | 不消耗 credits |

响应的 `X-RateLimit-Limit`、`X-RateLimit-Remaining`、`X-RateLimit-Reset` 描述服务端限流状态。超限返回 429 和 `Retry-After`；适配器会将等待提示放入错误信息，不自动重试。调用方应停止请求并等待该时长，缺少该头时冷却 300 秒。项目跨命令对同 host 保留至少 2 秒间隔；这是保守操作规则，不是官方限额，也不是适配器内部的全局限流器。

配置 Key 可取消免 Key 的小时上限，但默认仍限制为每组织 10 次/秒，所有组织 Key 共享，并消耗账号 credits。更多说明见[集中限流文档](../../../references/rate_limits.md#keenable-search)。

## 使用示例

```bash
# 基础搜索（无需 Key）
python scripts/channels/keenable/keenable_search.py "AI agent framework" -m 10

# 限定域名与发布时间
python scripts/channels/keenable/keenable_search.py "langchain" --site pypi.org --published-after 1y

# JSON 输出
python scripts/channels/keenable/keenable_search.py "AI agent framework" --json

# 统一入口
python union_search_cli.py platform keenable "AI agent framework" --limit 5
python union_search_cli.py platform keenable "langchain" --param site=pypi.org --param published_after=7d
```

## 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `query` | 搜索关键词（必需） | - |
| `-m, --max-results` | 结果数量上限，超出 1–50 时截到该范围 | 50 |
| `--site` | 只保留该域名的结果 | - |
| `--published-after` | 发布时间下限，`YYYY-MM-DD` 或 `1d`、`7d`、`1mo`、`1y` | - |
| `--published-before` | 发布时间上限，`YYYY-MM-DD` | - |
| `--api-key` | API Key（优先于环境变量，可选） | - |
| `--endpoint` | 接口地址；无 Key 时自动追加 `/public` | https://api.keenable.ai/v1/search |
| `--timeout` | 请求超时秒数 | 30 |
| `--json` | JSON 输出 | 否 |

输出字段见[输出结果分析](output-analysis.md)。
