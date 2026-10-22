# AnySearch 实时搜索

统一实时搜索服务，支持通用网页搜索与垂直领域检索，提供 REST 接口，无需部署 MCP 服务。

## 功能特性

- 通用网页搜索，返回标题、链接、摘要与正文
- 垂直领域检索：金融、学术、代码、文档、数据、图片、视频、音频
- 支持限定域名、区域（中国/国际）与时间范围
- 匿名可用，配置 API Key 提高限额

## 配置

在项目根目录的 `.env` 文件中添加：

```bash
# 可选，留空时匿名访问
ANYSEARCH_API_KEY=your_anysearch_api_key
# 默认 https://api.anysearch.com/v1/search
ANYSEARCH_ENDPOINT=
```

API Key 在 [AnySearch 控制台](https://anysearch.com/console/api-keys) 创建。

## 使用示例

```bash
# 基础搜索
python scripts/channels/anysearch/anysearch_search.py "claude code" -m 5

# 垂直领域检索
python scripts/channels/anysearch/anysearch_search.py "AAPL" --domains finance --tags finance.us_stock

# 指定内容类型与地区
python scripts/channels/anysearch/anysearch_search.py "大模型" --content-types news --zone cn

# 最近一周
python scripts/channels/anysearch/anysearch_search.py "AI agent" --freshness week

# JSON 输出
python scripts/channels/anysearch/anysearch_search.py "claude code" --json
```

## 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `query` | 搜索关键词（必需） | - |
| `-m, --max-results` | 结果数量 | 10 |
| `--domains` | 限定领域或域名，如 `finance`、`academic` | - |
| `--tags` | 子领域标签，如 `finance.us_stock` | - |
| `--content-types` | `web`、`news`、`code`、`doc`、`academic`、`data`、`image`、`video`、`audio` | - |
| `--zone` | `cn` 中国、`intl` 国际 | 服务端默认 |
| `--freshness` | `day`、`week`、`month`、`year` | - |
| `--api-key` | API Key（优先于环境变量） | 匿名 |
| `--endpoint` | 接口地址 | https://api.anysearch.com/v1/search |
| `--timeout` | 请求超时秒数 | 30 |
| `--json` | JSON 输出 | False |

垂直领域检索前先调用官方 CLI 的 `list_domains` 获取可用 `sub_domain` 与 `query_format`：

```bash
python ../anysearch-skill/scripts/anysearch_cli.py list_domains --domain finance
```

## 输出字段

`title`、`href`、`body`、`engine`、`content`、`score`、`quality_score`、`source`、`published_at`、`total_results`、`search_time_ms`。

## 相关链接

- [AnySearch 官网](https://anysearch.com)
- [API Key 管理](https://anysearch.com/console/api-keys)
