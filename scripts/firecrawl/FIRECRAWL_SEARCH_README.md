# Firecrawl Search

Firecrawl v2 搜索接口，返回网页、新闻、图片结果，可按需抓取网页正文。

## 功能特性

- 网页、新闻、图片三类结果
- 支持限定或排除域名
- 支持时间范围过滤（`tbs`）
- 可选抓取正文（Markdown、HTML、links）
- 支持自建 Firecrawl 服务

## 配置

在项目根目录的 `.env` 文件中添加：

```bash
FIRECRAWL_API_KEY=fc-your_api_key
# 自建服务时填写，默认 https://api.firecrawl.dev
FIRECRAWL_API_URL=
```

API Key 在 [Firecrawl 控制台](https://www.firecrawl.dev/app) 创建。

## 使用示例

```bash
# 基础搜索
python scripts/firecrawl/firecrawl_search.py "AI agent" -m 10

# 同时抓取正文
python scripts/firecrawl/firecrawl_search.py "AI agent" -m 5 --scrape

# 搜索新闻并限制时间
python scripts/firecrawl/firecrawl_search.py "大模型" --sources news --tbs qdr:w

# 限定域名
python scripts/firecrawl/firecrawl_search.py "Claude" --include-domains anthropic.com

# JSON 输出
python scripts/firecrawl/firecrawl_search.py "AI agent" --json
```

## 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `query` | 搜索关键词（必需） | - |
| `-m, --max-results` | 每个来源的结果数 | 10 |
| `--sources` | `web`、`news`、`images` | web |
| `--categories` | `research`、`pdf`、`developer`、`gov` | - |
| `--include-domains` | 限定域名 | - |
| `--exclude-domains` | 排除域名 | - |
| `--tbs` | 时间过滤，如 `qdr:d`、`qdr:w`、`sbd:1` | - |
| `--location` | 地理定位，如 `Germany` | - |
| `--country` | 国家代码，如 `CN`、`US` | - |
| `--scrape` | 抓取正文 | False |
| `--formats` | 抓取格式 | markdown |
| `--api-key` | API Key（优先于环境变量） | - |
| `--api-url` | 接口地址 | https://api.firecrawl.dev |
| `--json` | JSON 输出 | False |

## 输出字段

每条结果包含 `title`、`href`、`body`、`engine`、`source_type`、`position`；抓取正文时增加 `markdown`、`metadata`；新闻结果增加 `date`、`image`。

## 计费

搜索按结果数量计费，每 10 条结果消耗 2 credits，抓取正文另计 1 credit/页。

## 相关链接

- [Firecrawl 搜索文档](https://docs.firecrawl.dev/features/search)
- [Firecrawl API 参考](https://docs.firecrawl.dev/api-reference/endpoint/search)
