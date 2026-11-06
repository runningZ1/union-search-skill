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
