# RSS Feed Search

从 RSS 订阅源搜索和监控内容，支持关键词过滤和多种输出格式。

## 功能特性

- ✅ 支持单个或多个 RSS 订阅源
- ✅ 在标题、摘要和内容中搜索关键词
- ✅ 多种输出格式（文本、JSON、Markdown）
- ✅ 结果过滤和限制
- ✅ 支持配置文件管理订阅源
- ✅ 无需 API 密钥
- ✅ **支持解析结果缓存** - 保存解析结果到本地文件夹，支持离线搜索

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

### 解析结果文件夹（新增）

```bash
# 1. 解析并保存RSS结果到文件夹（首次或更新缓存）
python scripts/rss_search/rss_search.py "AI" --feed http://example.com/feed.xml --parse-folder ./parsed_results

# 2. 从保存的解析结果中搜索（无需再次请求RSS源）
python scripts/rss_search/rss_search.py "GPT" --parse-folder ./parsed_results --no-fetch

# 3. 仅解析保存，不搜索
python scripts/rss_search/rss_search.py --feed http://example.com/feed.xml --parse-folder ./parsed_results --parse-only

# 4. 搜索已保存的解析结果
python scripts/rss_search/rss_search.py "机器学习" --parse-folder ./parsed_results --json
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
| `--parse-folder` | 解析结果保存/读取的文件夹路径 | - |
| `--parse-only` | 仅解析并保存RSS结果，不进行搜索 | False |
| `--no-fetch` | 不重新获取RSS，直接从解析文件夹中搜索 | False |

## 解析结果文件夹功能

### 工作流程

1. **首次解析**：使用 `--parse-folder` 参数指定文件夹，脚本会：
   - 获取 RSS feed 内容
   - 解析所有条目
   - 将所有解析结果合并保存为一个 JSON 文件到指定文件夹

2. **后续搜索**：使用 `--no-fetch` 参数从已保存的结果中搜索：
   - 不再请求 RSS 源，速度更快
   - 支持离线搜索
   - 可以保留历史解析记录

### 文件夹结构

```
parsed_results/
└── all_feeds_{YYYY-MM-DD_HH-MM-SS}.json   # 合并的解析结果文件
```

> **注意**：每次解析会生成一个新的合并文件，历史文件会被保留。

### RSS 源有效性说明

⚠️ **重要提示**：
- 本模块为 **测试和实验性质**
- 配置文件中的 RSS 源来自第三方服务（如 Kindle4RSS、wechat2rss、rsshub 等）
- 这些 RSS 源 **可能不是实时有效的**，具体表现包括：
  - 部分源可能返回 0 条内容
  - 部分源可能解析失败
  - 部分源可能在某些时刻无法访问
- 这是第三方 RSS 服务的限制，非本工具的问题
- **如需使用本模块，请自行配置有效的 RSS 信息源**，部分链接可能已失效，需要自行测试和改造

### JSON 文件格式

合并的 JSON 文件是一个数组，每个元素包含：
- `url`: RSS 源 URL
- `title`: 源标题
- `description`: 源描述
- `link`: 源链接
- `entries`: 条目列表
- `status`: 状态（success/error）
- `parsed_at`: 解析时间

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
5. **离线搜索**：使用解析文件夹实现无需网络的搜索

## 注意事项

1. **订阅源可用性**：某些 RSS 源可能需要代理访问
2. **更新频率**：RSS 源的更新频率由源站点决定
3. **内容完整性**：某些 RSS 源只提供摘要，不包含完整内容
4. **解析文件夹**：首次使用需要网络连接获取 RSS，之后可使用 --no-fetch 离线搜索

## 示例订阅源

- 微信公众号（通过 Kindle4RSS）：`http://feedmaker.kindle4rss.com/feeds/`
- 技术博客：通常在网站底部有 RSS 图标
- 新闻网站：查找 `/feed` 或 `/rss` 路径
