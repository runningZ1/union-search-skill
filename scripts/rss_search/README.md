# RSS Feed Search

从 RSS 订阅源搜索和监控内容，支持关键词过滤和多种输出格式。

## 功能特性

- ✅ 支持单个或多个 RSS 订阅源
- ✅ 在标题、摘要和内容中搜索关键词
- ✅ 多种输出格式（文本、JSON、Markdown）
- ✅ 结果过滤和限制
- ✅ 支持配置文件管理订阅源
- ✅ 无需 API 密钥

## 安装

```bash
pip install feedparser
```

## 使用示例

### 基础搜索

```bash
# 搜索单个 RSS 订阅源
python scripts/rss_search/rss_search.py "AI" --feed http://example.com/feed.xml --limit 10

# 获取最新条目（不使用关键词）
python scripts/rss_search/rss_search.py --feed http://example.com/feed.xml --limit 5
```

### 多订阅源搜索

```bash
# 从配置文件搜索多个订阅源
python scripts/rss_search/rss_search.py "GPT" --feeds rss_feeds.txt --markdown

# 保存结果到文件
python scripts/rss_search/rss_search.py "机器学习" --feed http://example.com/feed.xml --json --pretty -o results.json
```

## 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `query` | 搜索关键词（可选） | - |
| `--feed` | 单个 RSS 订阅源 URL | - |
| `--feeds` | 包含多个订阅源的配置文件 | - |
| `--limit` | 最大结果数 | 10 |
| `--json` | JSON 格式输出 | False |
| `--pretty` | 格式化 JSON 输出 | False |
| `--markdown` | Markdown 格式输出 | False |
| `--full` | 包含完整内容和详情 | False |
| `-o, --output` | 保存输出到文件 | - |
| `--timeout` | 请求超时时间（秒） | 30 |
| `--case-sensitive` | 区分大小写搜索 | False |

## 配置文件格式

创建 `rss_feeds.txt` 文件管理多个订阅源：

```
# AI News
http://feedmaker.kindle4rss.com/feeds/AI_era.weixin.xml

# Tech News
https://example.com/tech/rss.xml

# 以 # 开头的行是注释
```

## 输出信息

- 条目标题和链接
- 发布日期
- 摘要或内容预览
- 来源订阅源信息

## 使用场景

1. **内容监控**：定期检查多个 RSS 源的新内容
2. **关键词追踪**：搜索特定主题的文章
3. **内容聚合**：从多个来源收集相关内容
4. **自动化工作流**：结合 cron 定时任务监控更新

## 注意事项

1. **订阅源可用性**：某些 RSS 源可能需要代理访问
2. **更新频率**：RSS 源的更新频率由源站点决定
3. **内容完整性**：某些 RSS 源只提供摘要，不包含完整内容

## 示例订阅源

- 微信公众号（通过 Kindle4RSS）：`http://feedmaker.kindle4rss.com/feeds/`
- 技术博客：通常在网站底部有 RSS 图标
- 新闻网站：查找 `/feed` 或 `/rss` 路径
