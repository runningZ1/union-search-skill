# Kimi 搜索

Kimi（Moonshot）长期支持的独立搜索接口。基础搜索返回标题、链接与摘要，专业搜索返回按相关度排序的正文片段。

## 功能特性

- 基础搜索 `POST /v1/tools/search`，可选附带页面正文
- 专业搜索 `POST /v1/tools/search_pro`，返回带分数的正文片段
- 可限定最多 5 个站点，多个站点按或关系合并
- 可按年、年月或日期设置时间窗口
- 查询按原文发送，不做改写

## 配置

在项目根目录的 `.env` 文件中添加：

```bash
MOONSHOT_API_KEY=your_moonshot_api_key_here
# 默认 https://api.moonshot.cn/v1
MOONSHOT_API_BASE_URL=
# 默认 search，可选 search_pro
KIMI_SEARCH_TIER=search
```

API Key 在 [Kimi 开放平台](https://platform.kimi.com) 创建。

## 使用示例

```bash
# 基础搜索
python scripts/kimi/kimi_search.py "人工智能最新进展" -m 5

# 专业搜索，限定站点与时间
python scripts/kimi/kimi_search.py "人工智能最新进展" --tier search_pro --site arxiv.org --start 2026-01

# 基础搜索附带正文
python scripts/kimi/kimi_search.py "人工智能最新进展" --include-content --timeout 60

# JSON 输出
python scripts/kimi/kimi_search.py "人工智能最新进展" --json
```

## 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `query` | 搜索关键词（必需） | - |
| `-m, --max-results` | 返回数量，1-20 | 5 |
| `--tier` | `search`、`search_pro` | search |
| `--include-content` | 基础搜索附带页面正文 | 关闭 |
| `--site` | 限定站点，可重复传入，最多 5 个 | - |
| `--start` | 时间窗口起点 | - |
| `--end` | 时间窗口终点 | - |
| `--api-key` | API Key（优先于环境变量） | - |
| `--base-url` | 接口根地址 | https://api.moonshot.cn/v1 |
| `--timeout` | 服务端超时秒数，1-60 | 30 |
| `--json` | JSON 输出 | False |

## 输出字段

`title`、`href`、`body`、`engine`、`site_name`、`publish_date`、`tier`。

基础搜索的 `body` 取摘要，开启正文时取页面内容。专业搜索的 `body` 取 `chunks` 中的片段文本。

## 计费

| 接口 | 单价 |
|------|------|
| `/v1/tools/search` | 0.01 元/次 |
| `/v1/tools/search_pro` | 0.015 元/次 |
| `/v1/tools/fetch` | 0.01 元/次 |

费用与模型 token 分开计算。对话补全里的内置 `$web_search` 工具预计 2026 年 10 月 20 日下线，本渠道使用独立接口。

## 相关链接

- [联网搜索指南](https://platform.kimi.com/docs/guide/use-web-search)
- [独立搜索实践](https://platform.kimi.com/docs/guide/best-practices-for-web-search)
- [搜索计费](https://platform.kimi.com/docs/pricing/websearch)
