# 知乎开放平台搜索

知乎开放平台提供的站内搜索、全网搜索、热榜与直答接口。

## 功能特性

- 站内搜索：知乎问题与文章，带作者、赞同数、评论数
- 全网搜索：覆盖站外内容，最多 20 条
- 热榜：实时榜单，最多 30 条
- 直答：`zhida-fast-1p5`、`zhida-thinking-1p5`、`zhida-agent` 三个模型

## 配置

在项目根目录的 `.env` 文件中添加：

```bash
ZHIHU_ACCESS_SECRET=your_access_secret
# 默认 https://developer.zhihu.com
ZHIHU_OPENAPI_BASE_URL=
```

Access Secret 在 [知乎开放平台](https://developer.zhihu.com) 控制台创建应用后获取。

## 使用示例

```bash
# 站内搜索
python scripts/zhihu_official/zhihu_official_search.py search "大模型 联网搜索" -m 5

# 全网搜索
python scripts/zhihu_official/zhihu_official_search.py global "AI agent 最新进展" -m 10

# 热榜
python scripts/zhihu_official/zhihu_official_search.py hot -m 20

# 直答
python scripts/zhihu_official/zhihu_official_search.py ask "什么是 RAG" --model zhida-fast-1p5

# JSON 输出
python scripts/zhihu_official/zhihu_official_search.py search "大模型" --json
```

## 参数说明

| 子命令 | 参数 | 说明 |
|--------|------|------|
| `search` | `query`、`-m/--max-results` | 站内搜索，最多 10 条 |
| `global` | `query`、`-m/--max-results` | 全网搜索，最多 20 条 |
| `hot` | `-m/--max-results` | 热榜，最多 30 条 |
| `ask` | `question`、`--model` | 直答，默认 `zhida-agent` |

公共参数：`--access-secret`、`--base-url`、`--timeout`、`--json`。

## 输出字段

搜索结果：`title`、`href`、`body`、`engine`、`author_name`、`edit_time`，站内搜索另带 `vote_up_count`、`comment_count`。
热榜结果：`title`、`href`、`body`、`thumbnail_url`，以及 `total`。
直答结果：`answer`、`reasoning_content`、`model`、`id`。

## 接口

| 能力 | 接口 |
|------|------|
| 站内搜索 | `GET /api/v1/content/zhihu_search?Query=&Count=` |
| 全网搜索 | `GET /api/v1/content/global_search?Query=&Count=` |
| 热榜 | `GET /api/v1/content/hot_list?Limit=` |
| 直答 | `POST /v1/chat/completions` |

鉴权使用 `Authorization: Bearer <secret>` 与 `X-Request-Timestamp` 请求头。

## 相关链接

- [知乎开放平台文档](https://developer.zhihu.com/docs)
