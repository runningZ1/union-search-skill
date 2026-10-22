# Querit 搜索

Querit 内容检索接口，返回标题、链接、摘要、页面时间与站点权威度。请求体与官方 Python SDK `querit` 0.1.5 的 `SearchRequest.to_payload()` 一致。

## 功能特性

- 按语言、国家、站点白名单、站点黑名单过滤
- 按时间范围过滤，例如 `d1`
- 结果附带页面时间、页面年龄与站点权威度

## 配置

在项目根目录的 `.env` 文件中添加：

```bash
QUERIT_API_KEY=your_querit_api_key_here
# 默认 https://api.querit.ai
QUERIT_API_BASE_URL=
```

API Key 在 [Querit 平台](https://www.querit.ai) 创建。环境变量填写密钥本身，脚本会补上 `Bearer` 前缀。

## 使用示例

```bash
# 基础搜索
python scripts/channels/querit/querit_search.py "machine learning" -m 10

# 限定语言、站点与时间
python scripts/channels/querit/querit_search.py "machine learning" --language english --include-site arxiv.org --time-range d1

# JSON 输出
python scripts/channels/querit/querit_search.py "machine learning" --json
```

## 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `query` | 搜索关键词（必需） | - |
| `-m, --max-results` | 返回数量 | 10 |
| `--language` | 语言，可重复传入 | - |
| `--country` | 国家，可重复传入 | - |
| `--include-site` | 站点白名单，可重复传入 | - |
| `--exclude-site` | 站点黑名单，可重复传入 | - |
| `--time-range` | 时间范围，如 `d1` | - |
| `--api-key` | API Key（优先于环境变量） | - |
| `--base-url` | 接口根地址 | https://api.querit.ai |
| `--timeout` | 请求超时秒数 | 60 |
| `--json` | JSON 输出 | False |

语言取值：`english`、`japanese`、`korean`、`german`、`french`、`spanish`、`portuguese`。

国家取值：`argentina`、`australia`、`brazil`、`canada`、`colombia`、`france`、`germany`、`india`、`indonesia`、`japan`、`mexico`、`nigeria`、`philippines`、`south korea`、`spain`、`united kingdom`、`united states`。

## 输出字段

`title`、`href`、`body`、`engine`、`page_time`、`page_age`、`language`、`site_auth_level`、`search_id`。

## 限制

- 接口为 `POST https://api.querit.ai/v1/search`
- 401 表示密钥无效，429 表示触发速率限制
- 官方文档未公布具体配额，额度以控制台为准

## 相关链接

- [Python SDK](https://www.querit.ai/zh/docs/sdks/python)
- [querit-python 源码](https://github.com/querit-ai/querit-python)
