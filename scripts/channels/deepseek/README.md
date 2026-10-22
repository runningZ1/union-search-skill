# DeepSeek 联网搜索

DeepSeek 官方搜索接口 `POST /v1/tools/search`，返回自研搜索引擎的网页结果，带相关度与权威度评分。

## 功能特性

- 官方搜索接口，结果带相关度 `rerank_score` 与权威度 `authority`
- 可选返回网页正文（`need_content`）
- 支持 `site:`、`-site:` 与引号精确匹配
- 每条结果带摘要 `snippet` 与模型可读的长摘要 `summary`

## 配置

在项目根目录的 `.env` 文件中添加：

```bash
DEEPSEEK_API_KEY=sk-your_api_key
# 默认 https://api.deepseek.com
DEEPSEEK_API_URL=
```

API Key 在 [DeepSeek 开放平台](https://platform.deepseek.com/) 创建。

## 使用示例

```bash
# 基础搜索
python scripts/channels/deepseek/deepseek_search.py "AI agent" -m 10

# 返回网页正文
python scripts/channels/deepseek/deepseek_search.py "大模型推理" -m 5 --need-content

# 带原始问题提升排序
python scripts/channels/deepseek/deepseek_search.py "V4 发布" --ori-question "DeepSeek V4 什么时候发布"

# JSON 输出
python scripts/channels/deepseek/deepseek_search.py "AI agent" --json
```

## 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `query` | 搜索关键词（必需，最多 128 字符） | - |
| `-m, --max-results` | 结果数量（1-50） | 10 |
| `--ori-question` | 原始用户问题，帮助排序 | - |
| `--localization` | 本地化结果所用 IP 地址 | - |
| `--need-content` | 返回网页正文 | False |
| `--api-key` | API Key（优先于环境变量） | - |
| `--api-url` | 接口地址 | https://api.deepseek.com |
| `--timeout` | 请求超时秒数 | 30 |
| `--json` | JSON 输出 | False |

## 输出字段

每条结果包含 `title`、`href`、`body`、`engine`、`summary`、`content`、`site_name`、`site_icon`、`date`、`authority`、`rerank_score`。

`rerank_score` 达到 1.5 视为高质量结果，`authority` 达到 3 视为高权威来源。

## 计费

按成功请求计费，5 元/1000 次；账号级限速约 100 QPS。

## 相关链接

- [DeepSeek 搜索 API 参考](https://api-docs.deepseek.com/zh-cn/api/search/)
- [DeepSeek 搜索与抓取指南](https://api-docs.deepseek.com/zh-cn/guides/search/)
