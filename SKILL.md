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

- 跨多个平台搜索内容（GitHub、Reddit、社交媒体、搜索引擎）
- 按时间范围、互动指标或内容类型过滤结果
- 批量搜索/下载并归档原始响应

## 可用的搜索工具

所有脚本位于 `scripts/` 目录。

| 模块 | 描述 | 文档 |
|------|------|------|
| **GitHub** | 仓库、代码、问题/PR搜索 | [GITHUB_README.md](scripts/github/GITHUB_README.md) |
| **Reddit** | 帖子、子版块、用户搜索 | [REDDIT_README.md](scripts/reddit/REDDIT_README.md) |
| **图片搜索** | 17平台批量图片下载 | [UNION_IMAGE_SEARCH_README.md](scripts/union_image_search/UNION_IMAGE_SEARCH_README.md) |
| **小红书** | 笔记搜索，支持过滤排序 | [XIAOHONGSHU_README.md](scripts/xiaohongshu/XIAOHONGSHU_README.md) |
| **抖音** | 视频搜索，支持过滤选项 | [DOUYIN_README.md](scripts/douyin/DOUYIN_README.md) |
| **Bilibili** | 视频搜索，双API支持 | [BILIBILI_README.md](scripts/bilibili/BILIBILI_README.md) |
| **Twitter** | 帖子和时间线搜索 | [TWITTER_README.md](scripts/twitter/TWITTER_README.md) |
| **Google** | Custom Search API | [GOOGLE_SEARCH_README.md](scripts/google_search/GOOGLE_SEARCH_README.md) |
| **Tavily** | AI驱动搜索引擎 | [TAVILY_SEARCH_README.md](scripts/tavily_search/TAVILY_SEARCH_README.md) |
| **YouTube** | 视频、评论搜索 | [YOUTUBE_README.md](scripts/youtube/YOUTUBE_README.md) |
| **微博** | 用户信息和帖子搜索 | [WEIBO_README.md](scripts/weibo/WEIBO_README.md) |
| **RSS** | 订阅源内容搜索 | [RSS_SEARCH_README.md](scripts/rss_search/RSS_SEARCH_README.md) |
| **Wikipedia** | 百科全书搜索 | [WIKIPEDIA_README.md](scripts/wikipedia/WIKIPEDIA_README.md) |
| **DuckDuckGo** | 隐私搜索引擎 | [DUCKDUCKGO_README.md](scripts/duckduckgo/DUCKDUCKGO_README.md) |
| **Brave** | 隐私搜索引擎 | [BRAVE_README.md](scripts/brave/BRAVE_README.md) |
| **Bing** | 微软搜索引擎 | [BING_README.md](scripts/bing/BING_README.md) |
| **Yahoo** | 雅虎搜索引擎 | [YAHOO_README.md](scripts/yahoo/YAHOO_README.md) |
| **Anna's Archive** | 电子书搜索 | [ANNASARCHIVE_README.md](scripts/annasarchive/ANNASARCHIVE_README.md) |
| **知乎** | 中文问答平台 | [ZHIHU_README.md](scripts/zhihu/ZHIHU_README.md) |

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
