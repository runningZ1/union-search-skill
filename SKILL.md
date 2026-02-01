---
name: union-search-skill
description: 当用户需要跨多个平台搜索内容时使用此技能，包括 GitHub（仓库、代码、问题）、Reddit（帖子、子版块、用户）、小红书、抖音、Bilibili、YouTube、Twitter、微博、Google、Tavily，以及通用搜索引擎（DuckDuckGo、Brave、Yahoo、Bing、Wikipedia、Anna's Archive），或从 17 个图片平台（百度、Bing、Google、Pixabay、Unsplash 等）下载图片。提供统一的搜索接口，支持结构化输出格式、结果过滤、排序、自动响应归档和批量图片下载（保留元数据）。
---

# 联合搜索技能

## 目的

提供跨多个平台的统一搜索能力，包含八大主要类别：

1. **开发者与社区搜索**：GitHub 仓库、代码、问题/PR、Reddit 帖子和讨论
2. **社交媒体与网络搜索**：小红书、抖音、Bilibili、YouTube、Twitter、微博、Google、Tavily
3. **通用搜索引擎**（无需 API 密钥）：DuckDuckGo、Brave、Yahoo、Bing、Wikipedia、Anna's Archive
4. **图片搜索与下载**：17 个图片平台，包括百度、Bing、Google、Pixabay、Unsplash、Pexels 等
5. **RSS 订阅搜索**：搜索和监控 RSS 订阅源内容，支持关键词过滤
6. **Reddit 搜索**：搜索 Reddit 帖子、子版块、用户，获取详细帖子信息和评论
7. **微博搜索**：搜索微博用户信息和帖子，支持全面的过滤选项
8. **YouTube 搜索**：搜索 YouTube 视频，获取详细信息、统计数据和评论

所有搜索脚本遵循标准化的输入/输出约定，提供可靠、可读的结果，具有一致的输出格式、结果过滤和自动响应归档功能。

## 何时使用此技能

当用户请求以下操作时使用此技能：
- 搜索 GitHub 仓库、代码片段或问题/拉取请求
- 搜索 Reddit 帖子、子版块、用户，或获取带评论的帖子详情
- 搜索小红书、抖音、Bilibili、YouTube、Twitter、微博、Google、Tavily 上的内容
- 使用通用搜索引擎（DuckDuckGo、Brave、Yahoo、Bing）进行网络搜索
- 搜索 Wikipedia 百科内容或 Anna's Archive 电子书资源
- 从多个图片平台下载图片（百度、Bing、Google 图片、Pixabay、Unsplash 等）
- 搜索和监控 RSS 订阅源，支持关键词过滤
- 按时间范围、互动指标或内容类型过滤搜索结果
- 跨多个平台批量搜索/下载
- 归档原始 API 响应或图片元数据以供后续分析

## 可用的搜索工具

所有脚本位于 `scripts/` 目录。

### 1. GitHub 搜索

搜索 GitHub 仓库、代码和问题/拉取请求，支持全面的过滤功能。

**核心特性：**
- 按语言、星标、主题、许可证等搜索仓库
- 在所有公共仓库中搜索代码
- 搜索问题和拉取请求，支持过滤
- 多种输出格式：文本、JSON、Markdown

**快速开始：**
```bash
# 配置 GitHub token（一次性设置）
python scripts/github/github_search.py config --token YOUR_GITHUB_TOKEN

# 仓库搜索
python scripts/github/github_search.py repo "machine learning" --language python --stars ">1000"

# 代码搜索
python scripts/github/github_search.py code "def main" --language python --limit 20
```

**关键参数：** `--language`, `--stars`, `--forks`, `--user`, `--topic`, `--license`, `--sort`, `--format`

📖 **详细文档：** [scripts/github/README.md](scripts/github/README.md)

---

### 2. Reddit 搜索

搜索 Reddit 帖子、子版块、用户，并获取详细信息。

**核心特性：**
- 跨所有子版块的全站搜索
- 帖子详情，可选评论树提取
- 用户活动历史（帖子和评论）
- 无需 API 密钥（使用公开 JSON 端点）

**快速开始：**
```bash
# 全站搜索
python scripts/reddit/cli.py search "python tutorial" --limit 10

# 获取帖子详情（包含评论）
python scripts/reddit/cli.py post /r/python/comments/abc123/title/ --include-comments
```

**关键参数：** `--limit`, `--sort`, `--proxy`, `--format`, `--output`

📖 **详细文档：** [scripts/reddit/README.md](scripts/reddit/README.md)

---

### 3. 多平台图片搜索

同时从 17 个平台搜索和下载图片。

**支持的平台：** 百度、Bing、Google、360、搜狗、DuckDuckGo、Yandex、Yahoo、Pixabay、Pexels、Unsplash、Foodiesfeed、Danbooru、Gelbooru、Safebooru、花瓣网、次元小镇

**核心特性：**
- 批量搜索所有 17 个平台或选定平台
- 有序输出：每个平台有自己的子文件夹
- 自动保存元数据（JSON 格式）
- 进度跟踪和摘要报告

**快速开始：**
```bash
pip install pyimagedl

# 搜索所有平台
python scripts/image_search/multi_platform_image_search.py "cute cats" --num 50

# 搜索特定平台
python scripts/image_search/multi_platform_image_search.py --keyword "sunset" --platforms baidu google pixabay --num 30
```

**关键参数：** `--keyword`, `--platforms`, `--num`, `--output`, `--threads`

📖 **详细文档：** [scripts/image_search/README.md](scripts/image_search/README.md)

---

### 4. 小红书搜索

搜索小红书笔记，支持过滤和排序功能。

**核心特性：**
- 按时间范围、内容类型（图片/视频）过滤
- 按点赞、评论、分享排序
- 提取话题标签（仅 `#` 前缀标签）

**快速开始：**
```bash
python scripts/xiaohongshu/tikhub_xhs_search.py "美食" --limit 10 --sort-by liked_count --sort-order desc
```

**关键参数：** `--keyword`, `--limit`, `--sort-by`, `--filter-note-type`, `--filter-note-time`

📖 **详细文档：** [scripts/xiaohongshu/README.md](scripts/xiaohongshu/README.md)

---

### 5. 抖音搜索

搜索抖音视频，支持全面的过滤选项。

**核心特性：**
- 按发布时间、时长、内容类型过滤
- 按互动指标排序
- 支持游标分页

**快速开始：**
```bash
python scripts/douyin/tikhub_douyin_search.py "美食" --limit 10
```

**关键参数：** `--keyword`, `--cursor`, `--sort-type`, `--publish-time`, `--filter-duration`

📖 **详细文档：** [scripts/douyin/README.md](scripts/douyin/README.md)

---

### 6. Bilibili 搜索

提供两种 Bilibili 搜索方式：

#### 6.1 TikHub API 搜索（简单快速）
```bash
python scripts/bilibili/tikhub_bili_search.py "原神" --page 1 --page-size 20
```

#### 6.2 Bilibili API 高级搜索（推荐）

**核心特性：**
- 使用官方 bilibili-api 库，无需 API Token
- 获取详细视频信息（互动数据、UP主信息、标签等）
- 支持多种输出格式（文本、JSON、Markdown）
- 支持多种排序方式

**快速开始：**
```bash
pip install bilibili-api-python aiohttp

# 基础搜索
python scripts/bilibili/bilibili_api_search.py "Python教程" --limit 10

# 按播放量排序
python scripts/bilibili/bilibili_api_search.py "机器学习" --order click --limit 10
```

**关键参数：** `--limit`, `--order` (totalrank/click/pubdate/dm/stow), `--json`, `--markdown`

📖 **详细文档：** [scripts/bilibili/README.md](scripts/bilibili/README.md)

---

### 7. Twitter 搜索

搜索 Twitter 帖子和时间线。

**核心特性：**
- 多种搜索类型（Top、Latest、Media、People、Lists）
- 支持游标分页

**快速开始：**
```bash
python scripts/twitter/tikhub_twitter_search.py "Elon Musk" --search-type Top
```

**关键参数：** `--keyword`, `--search-type`, `--cursor`

📖 **详细文档：** [scripts/twitter/README.md](scripts/twitter/README.md)

---

### 8. Google 搜索

使用 Google Custom Search API 进行网络搜索。

**核心特性：**
- 网络搜索和图片搜索
- 语言特定搜索
- 多种输出格式

**快速开始：**
```bash
pip install requests python-dotenv

# 网络搜索
python scripts/google_search/google_search.py "Python tutorial" -n 5

# 图片搜索
python scripts/google_search/google_search.py "sunset" --image -n 10
```

**关键参数：** `-n/--num`, `--lang`, `--image`, `--img-size`, `--json`

📖 **详细文档：** [scripts/google_search/README.md](scripts/google_search/README.md)

---

### 9. Tavily 搜索

为 LLM 应用优化的 AI 驱动搜索引擎。

**核心特性：**
- 带 AI 生成答案的实时网络搜索
- 多种搜索深度：basic、advanced、fast
- 特定主题搜索：general、news、finance

**快速开始：**
```bash
pip install tavily-python python-dotenv

# 基础搜索
python scripts/tavily_search/tavily_search.py "AI latest developments" --max-results 5

# 带 AI 答案的高级搜索
python scripts/tavily_search/tavily_search.py "quantum computing" --search-depth advanced --include-answer
```

**关键参数：** `--max-results`, `--search-depth`, `--topic`, `--include-answer`

📖 **详细文档：** [scripts/tavily_search/README.md](scripts/tavily_search/README.md)

---

### 10. YouTube 搜索

搜索 YouTube 视频，获取详细信息、统计数据和评论。

**核心特性：**
- 按关键词搜索视频，支持多种排序选项
- 获取详细视频信息和互动统计数据
- 可选评论提取（热门评论）
- 无外部依赖（仅使用标准库）

**快速开始：**
```bash
# 基础搜索
python scripts/youtube/youtube_search.py "Python tutorial" --limit 5

# 按播放量排序
python scripts/youtube/youtube_search.py "机器学习" --order viewCount --limit 10

# 包含评论
python scripts/youtube/youtube_search.py "AI" --include-comments --max-comments 5
```

**关键参数：** `--api-key`, `--limit`, `--order`, `--include-comments`, `--region`, `--language`

📖 **详细文档：** [scripts/youtube/README.md](scripts/youtube/README.md)

---

### 11. 微博搜索

搜索微博用户信息和帖子，支持全面的过滤选项。

**核心特性：**
- 获取用户资料信息（昵称、性别、地区、粉丝数等）
- 获取用户的微博帖子，包含完整内容和互动指标
- 按原创帖子过滤或包含转发
- 时间范围过滤和排序

**快速开始：**
```bash
# 搜索单个用户
python scripts/weibo/weibo_search.py --user-id 1669879400 --cookie "YOUR_COOKIE"

# 带过滤器搜索
python scripts/weibo/weibo_search.py --user-id 1669879400 --filter 1 --limit 20
```

**关键参数：** `--user-id`, `--cookie`, `--filter`, `--since-date`, `--limit`, `--sort-by`

📖 **详细文档：** [scripts/weibo/README.md](scripts/weibo/README.md)

---

### 12. RSS 订阅搜索

从 RSS 订阅源搜索和监控内容，支持关键词过滤。

**核心特性：**
- 支持单个或多个 RSS 订阅源
- 在标题、摘要和内容中搜索关键词
- 多种输出格式
- 无需 API 密钥

**快速开始：**
```bash
pip install feedparser

# 搜索单个 RSS 订阅源
python scripts/rss_search/rss_search.py "AI" --feed http://example.com/feed.xml --limit 10

# 从配置文件搜索多个订阅源
python scripts/rss_search/rss_search.py "GPT" --feeds rss_feeds.txt --markdown
```

**关键参数：** `--feed`, `--feeds`, `--limit`, `--json`, `--markdown`, `--full`

📖 **详细文档：** [scripts/rss_search/README.md](scripts/rss_search/README.md)

---

## 配置

### 环境变量

所有工具支持三种配置方式（优先级从高到低）：

1. **命令行参数**：`--token YOUR_TOKEN` 或 `--api-key YOUR_KEY`
2. **环境变量**：在项目根目录的 `.env` 文件中配置
3. **配置文件**：工具特定的配置文件（如 GitHub 的 `~/.github-search.json`）

### 主要 API 凭据

在项目根目录创建 `.env` 文件：

```bash
# GitHub
GITHUB_TOKEN=your_github_token

# TikHub (小红书、抖音、Bilibili、Twitter)
TIKHUB_TOKEN=your_tikhub_token

# Google Custom Search
GOOGLE_API_KEY=your_google_api_key
GOOGLE_SEARCH_ENGINE_ID=your_search_engine_id

# Tavily Search
TAVILY_API_KEY=tvly-your_tavily_api_key

# YouTube
YOUTUBE_API_KEY=your_youtube_api_key

# 微博
WEIBO_COOKIE=your_weibo_cookie
```

### 获取 API 凭据

- **GitHub Token**: https://github.com/settings/tokens
- **TikHub Token**: https://tikhub.io
- **Google API Key**: https://console.cloud.google.com/apis/credentials
- **Tavily API Key**: https://tavily.com
- **YouTube API Key**: https://console.cloud.google.com/apis/credentials
- **微博 Cookie**: 参见 [如何获取 cookie](https://github.com/dataabc/weiboSpider/blob/master/docs/cookie.md)

## 使用指南

### 通用参数

大多数工具支持以下通用参数：

- `--limit` / `-n`: 返回的结果数量
- `--json`: JSON 格式输出
- `--pretty`: 格式化 JSON 输出
- `--markdown`: Markdown 格式输出
- `-o` / `--output`: 保存输出到文件
- `--save-raw`: 保存原始 API 响应到 `responses/` 目录

### 输出格式

**终端输出：**
- 格式：带中文字段名的 Markdown
- 内容：结构化、人类可读的结果

**原始响应归档：**
- 位置：`responses/` 目录
- 命名：时间戳（YYYYMMDD_HHMMSS）+ 平台后缀
- 格式：来自 API 的原始 JSON 响应

### 执行工作流

1. **运行前**：验证 `.env` 配置存在且包含有效凭据
2. **运行**：从技能目录直接执行脚本
3. **运行后**：检查终端输出和 `responses/` 目录中的原始响应文件

### 最佳实践

**结果过滤：**
- 使用 `--limit` 控制输出量
- 应用时间过滤器获取最新内容
- 按互动指标排序以找到热门内容

**响应管理：**
- 永远不要将完整的原始 JSON 粘贴到对话中
- 需要完整数据访问时引用 `responses/` 文件
- 使用 grep/jq 从保存的响应中提取特定字段

**多平台搜索：**
- 为不同平台依次运行脚本
- 使用保存的响应文件比较跨平台结果

## 常见问题

| 问题 | 解决方案 |
|------|----------|
| 缺少凭据 | 检查 `.env` 文件配置 |
| API 速率限制 | 降低请求频率或限制结果数量 |
| 网络超时 | 增加 `.env` 中的超时值或使用代理 |
| 无效参数 | 验证参数名称是否符合脚本预期 |
| 403 Blocked (Reddit) | 使用 `--proxy` 参数 |

## 平台特定说明

- **小红书**：仅提取带 `#` 前缀的话题标签；内容类型过滤：0=全部，1=视频，2=图片
- **抖音**：支持按时长和内容类型的高级过滤；通过游标参数分页
- **微博**：认证需要 Cookie（约 3 个月过期）；无法爬取自己的微博
- **YouTube**：每日配额 10,000 单位；搜索请求 100 单位/次
- **GitHub**：已认证 30 次搜索/分钟；未认证 10 次搜索/分钟
- **图片搜索**：完全独立，无需 API 密钥，仅需 `pip install pyimagedl`
