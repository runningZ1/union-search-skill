# Ollama Web Search

Ollama 托管的网页搜索接口，返回标题、链接与正文摘要。免费账号即可创建 API Key。

## 功能特性

- 单次返回 1-10 条结果，默认 5 条
- 摘要字段为 `content`，适合直接放入模型上下文
- 同一密钥也可调用 `POST /api/web_fetch` 抓取页面正文

## 配置

在项目根目录的 `.env` 文件中添加：

```bash
OLLAMA_API_KEY=your_ollama_api_key_here
# 默认 https://ollama.com/api/web_search
OLLAMA_WEB_SEARCH_ENDPOINT=
```

API Key 在 [Ollama Keys](https://ollama.com/settings/keys) 创建。

## 使用示例

```bash
# 基础搜索
python scripts/channels/ollama_search/ollama_search.py "what is ollama" -m 5

# JSON 输出
python scripts/channels/ollama_search/ollama_search.py "what is ollama" --json
```

## 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `query` | 搜索关键词（必需） | - |
| `-m, --max-results` | 返回数量，1-10 | 5 |
| `--api-key` | API Key（优先于环境变量） | - |
| `--endpoint` | 接口地址 | https://ollama.com/api/web_search |
| `--timeout` | 请求超时秒数 | 30 |
| `--json` | JSON 输出 | False |

## 输出字段

`title`、`href`、`body`、`engine`。`body` 对应接口返回的 `content`。

## 限制

- 单次最多 10 条
- 官方文档未公布速率限制与价格
- 摘要可能达到数千 token，放入模型上下文时需要足够的上下文长度

## 相关链接

- [Web Search](https://docs.ollama.com/capabilities/web-search)
- [官方 Python 示例](https://github.com/ollama/ollama-python/blob/main/examples/web-search.py)
- [MCP 示例](https://github.com/ollama/ollama-python/blob/main/examples/web-search-mcp.py)
