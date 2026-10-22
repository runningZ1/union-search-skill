# TinyFish 搜索

轻量实时网页搜索接口，面向 AI Agent，返回站点名、标题、摘要与链接。

## 功能特性

- 单次请求返回约 10 条结构化结果
- 支持按国家与语言限定结果
- 摘要直接可读，适合作为上下文
- 每个请求消耗一次调用额度

## 配置

在项目根目录的 `.env` 文件中添加：

```bash
TINYFISH_API_KEY=your_tinyfish_api_key
# 默认 https://api.search.tinyfish.ai
TINYFISH_SEARCH_ENDPOINT=
```

API Key 在 [TinyFish 控制台](https://www.tinyfish.ai) 创建，注册无需信用卡。

## 使用示例

```bash
# 基础搜索
python scripts/channels/tinyfish/tinyfish_search.py "AI agent" -m 10

# 限定地区与语言
python scripts/channels/tinyfish/tinyfish_search.py "大模型" --location CN --language zh

# JSON 输出
python scripts/channels/tinyfish/tinyfish_search.py "AI agent" --json
```

## 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `query` | 搜索关键词（必需） | - |
| `-m, --max-results` | 返回数量，接口单次约 10 条 | 10 |
| `--location` | 两位国家代码，如 `US`、`CN` | 由语言推断 |
| `--language` | 语言代码，如 `en`、`zh` | 由地区推断 |
| `--api-key` | API Key（优先于环境变量） | - |
| `--endpoint` | 接口地址 | https://api.search.tinyfish.ai |
| `--timeout` | 请求超时秒数 | 15 |
| `--json` | JSON 输出 | False |

## 输出字段

`title`、`href`、`body`、`engine`、`site_name`、`position`、`total_results`。

## 限制

- 默认 5 次/分钟，超限返回 429 `RATE_LIMIT_EXCEEDED`
- 响应没有 `Retry-After`，退避从 15 秒起

## 相关链接

- [TinyFish Search](https://www.tinyfish.ai/search)
- [TinyFish 免费搜索与抓取](https://www.tinyfish.ai/free-search-fetch)
