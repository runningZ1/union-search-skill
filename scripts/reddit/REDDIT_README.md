# Reddit 搜索

完整的 Reddit 搜索工具，基于 YARS 项目

## 安装

```bash
pip install requests pygments
```

## 使用示例

### 全站搜索
```bash
python scripts/reddit/cli.py search "python tutorial" --limit 10
```

### 使用代理
```bash
python scripts/reddit/cli.py search "python" --proxy "http://127.0.0.1:7890" --limit 5
```

### 子版块搜索
```bash
python scripts/reddit/cli.py subreddit-search python "async await" --limit 10
```

### 获取帖子详情
```bash
python scripts/reddit/cli.py post /r/python/comments/abc123/title/
```

### 获取用户数据
```bash
python scripts/reddit/cli.py user spez --limit 20
```

### 导出格式
```bash
python scripts/reddit/cli.py search "AI" --format json --output results.json
python scripts/reddit/cli.py search "AI" --format csv --output results.csv
```

## 主要参数

**通用参数**: `--proxy`, `--timeout`, `--output`, `--format` (json/csv/display)

**search**: `query`, `--limit`, `--sort` (relevance/hot/top/new)

**subreddit-search**: `subreddit`, `query`, `--limit`, `--sort`

**post**: `permalink`（帖子链接）

**user**: `username`, `--limit`

**subreddit-posts**: `subreddit`, `--category` (hot/top/new/rising), `--limit`, `--time-filter`

## 功能特性

- 无需 API 密钥（使用 Reddit 公开 JSON 端点）
- 完整的评论树递归提取
- 自动重试机制（5次重试，指数退避）
- 随机 User-Agent 轮换（7098个）
- 代理支持
- 多种输出格式

## 注意事项

- 如果遇到 403 Blocked 错误，请使用 `--proxy` 参数
- 脚本已内置 1-2 秒随机延迟
- 单次请求最多 100 条结果
