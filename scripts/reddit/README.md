# Reddit Search (YARS)

完整的 Reddit 搜索工具，基于 [YARS](https://github.com/Strvm/yars) 项目。

## 文件结构

```
reddit/
├── __init__.py          # 包初始化文件
├── yars.py              # 核心爬虫类
├── sessions.py          # 自定义 Session 类
├── agents.py            # User-Agent 列表 (7098个)
├── utils.py             # 工具函数
├── example.py           # 使用示例
├── cli.py               # 命令行接口
└── README.md            # 本文件
```

## 安装依赖

```bash
pip install requests pygments
```

## 使用方法

### 方式 1：命令行接口（推荐）

```bash
# 全站搜索
python scripts/reddit/cli.py search "python tutorial" --limit 10

# 使用代理
python scripts/reddit/cli.py search "python" --proxy "http://127.0.0.1:7890" --limit 5

# 子版块搜索
python scripts/reddit/cli.py subreddit-search python "async await" --limit 10

# 获取帖子详情
python scripts/reddit/cli.py post /r/python/comments/abc123/title/

# 获取用户数据
python scripts/reddit/cli.py user spez --limit 20

# 获取子版块帖子
python scripts/reddit/cli.py subreddit-posts python --category hot --limit 10

# 导出为 JSON
python scripts/reddit/cli.py search "AI" --format json --output results.json

# 导出为 CSV
python scripts/reddit/cli.py search "AI" --format csv --output results.csv
```

### 方式 2：Python API

```python
from reddit.yars import YARS

# 初始化（可选代理）
miner = YARS(proxy="http://127.0.0.1:7890", timeout=10)

# 全站搜索
results = miner.search_reddit("python tutorial", limit=10)

# 子版块搜索
results = miner.search_subreddit("python", "async await", limit=10)

# 获取帖子详情
post = miner.scrape_post_details("/r/python/comments/abc123/title/")

# 获取用户数据
user_data = miner.scrape_user_data("spez", limit=20)

# 获取子版块帖子
posts = miner.fetch_subreddit_posts("python", category="hot", limit=10)
```

### 方式 3：使用示例文件

```bash
# 查看完整示例
python scripts/reddit/example.py
```

## 命令参数

### 通用参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--proxy` | 代理地址 | 无 |
| `--timeout` | 请求超时时间（秒） | 10 |
| `--output` | 输出文件路径 | 无 |
| `--format` | 输出格式（json/csv/display） | display |

### search 命令

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `query` | 搜索关键词（必需） | - |
| `--limit` | 结果数量 | 10 |
| `--sort` | 排序方式（relevance/hot/top/new） | relevance |

### subreddit-search 命令

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `subreddit` | 子版块名称（必需） | - |
| `query` | 搜索关键词（必需） | - |
| `--limit` | 结果数量 | 10 |
| `--sort` | 排序方式 | relevance |

### post 命令

| 参数 | 说明 |
|------|------|
| `permalink` | 帖子链接（必需） |

### user 命令

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `username` | 用户名（必需） | - |
| `--limit` | 结果数量 | 10 |

### subreddit-posts 命令

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `subreddit` | 子版块名称（必需） | - |
| `--category` | 分类（hot/top/new/rising） | hot |
| `--limit` | 结果数量 | 10 |
| `--time-filter` | 时间过滤（all/day/week/month/year） | all |

## 功能特性

- ✅ 无需 API 密钥（使用 Reddit 公开 JSON 端点）
- ✅ 完整的评论树递归提取
- ✅ 自动重试机制（5次重试，指数退避）
- ✅ 随机 User-Agent 轮换（7098个）
- ✅ 代理支持
- ✅ 多种输出格式（display/json/csv）
- ✅ 详细的日志记录

## 输出格式

### display（默认）
彩色 JSON 格式化输出到终端

### json
标准 JSON 格式，可保存到文件

### csv
CSV 表格格式，适合 Excel 打开

## 注意事项

1. **代理配置**：如果遇到 403 Blocked 错误，请使用 `--proxy` 参数
2. **请求频率**：脚本已内置 1-2 秒随机延迟，避免过快请求
3. **结果限制**：单次请求最多 100 条结果
4. **评论提取**：`post` 命令会自动提取完整评论树

## 原项目

本工具基于 [YARS](https://github.com/Strvm/yars) 项目，保留了所有核心功能。

## 许可

MIT License
