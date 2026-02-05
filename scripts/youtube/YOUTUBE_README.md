# YouTube 搜索

基于 YouTube Data API v3 的视频搜索工具

## 安装

无需额外依赖，仅使用 Python 标准库。

## 配置

在根目录 `.env` 文件中添加：
```bash
YOUTUBE_API_KEY=your_api_key_here
```

获取 API Key: https://console.cloud.google.com/apis/credentials（需启用 YouTube Data API v3）

## 使用示例

### 基础搜索
```bash
python scripts/youtube/youtube_search.py "Python tutorial" --limit 5
```

### 按播放量排序
```bash
python scripts/youtube/youtube_search.py "AI" --order viewCount --limit 10
```

### 包含评论
```bash
python scripts/youtube/youtube_search.py "Python" --include-comments --max-comments 5
```

### 输出格式
```bash
python scripts/youtube/youtube_search.py "编程" --json --pretty
python scripts/youtube/youtube_search.py "教程" --markdown -o results.md
```

## 主要参数

- `--limit`: 结果数量（1-50，默认 10）
- `--order`: 排序方式（relevance/date/rating/viewCount/title）
- `--region`: 地区代码（如 US, CN）
- `--language`: 语言代码（如 zh-CN, en）
- `--include-comments`: 包含评论
- `--max-comments`: 每个视频的最大评论数（默认 10）
- `--json`, `--markdown`: 输出格式
- `--save-raw`: 保存原始响应

## API 配额

- 每日配额: 10,000 单位
- Search 请求: 100 单位/次
- Videos.list: 1 单位/次
- CommentThreads.list: 1 单位/次
