---
name: union-search-skill
description: 当用户需要跨多个平台搜索内容时使用此技能，包括 GitHub（仓库、代码、问题）、Reddit（帖子、子版块、用户）、小红书、抖音、Bilibili、YouTube、Twitter、微博、Google，或从 17 个图片平台（百度、Bing、Google、Pixabay、Unsplash 等）下载图片。提供统一的搜索接口，支持结构化输出格式、结果过滤、排序、自动响应归档和批量图片下载（保留元数据）。
---

# 联合搜索技能

## 目的

提供跨多个平台的统一搜索能力，包含七大主要类别：

1. **开发者与社区搜索**：GitHub 仓库、代码、问题/PR、Reddit 帖子和讨论
2. **社交媒体与网络搜索**：小红书、抖音、Bilibili、YouTube、Twitter、微博、Google
3. **图片搜索与下载**：17 个图片平台，包括百度、Bing、Google、Pixabay、Unsplash、Pexels 等
4. **RSS 订阅搜索**：搜索和监控 RSS 订阅源内容，支持关键词过滤
5. **Reddit 搜索**：搜索 Reddit 帖子、子版块、用户，获取详细帖子信息和评论
6. **微博搜索**：搜索微博用户信息和帖子，支持全面的过滤选项
7. **YouTube 搜索**：搜索 YouTube 视频，获取详细信息、统计数据和评论

所有搜索脚本遵循标准化的输入/输出约定，提供可靠、可读的结果，具有一致的输出格式、结果过滤和自动响应归档功能。

## 何时使用此技能

当用户请求以下操作时使用此技能：
- 搜索 GitHub 仓库、代码片段或问题/拉取请求
- 查找开源项目、库或代码示例
- 发现热门仓库或适合新手的问题
- 搜索 Reddit 帖子、子版块、用户，或获取带评论的帖子详情
- 在 Reddit 上查找讨论、问题或社区内容
- 搜索小红书、抖音、Bilibili、YouTube、Twitter、微博或 Google 上的内容
- 搜索微博用户信息和帖子（用户资料、微博内容、互动指标）
- 搜索 YouTube 视频及详细元数据（观看量、点赞数、评论数、时长、发布日期）
- 从多个图片平台下载图片（百度、Bing、Google 图片、Pixabay、Unsplash 等）
- 搜索和监控 RSS 订阅源，支持关键词过滤
- 按时间范围、互动指标或内容类型过滤搜索结果
- 按星标、点赞、评论、分享或其他指标排序结果
- 跨多个平台批量搜索/下载
- 归档原始 API 响应或图片元数据以供后续分析

## 可用的搜索脚本

所有脚本位于 `scripts/` 目录：

### 0. GitHub 搜索 (`scripts/github_search.py`)
**新功能** - 搜索 GitHub 仓库、代码和问题/拉取请求，支持全面的过滤功能。

**主要特性：**
- 按语言、星标、主题、许可证等搜索仓库
- 在所有公共仓库中搜索代码
- 搜索问题和拉取请求，支持过滤
- 检查 API 速率限制
- 支持配置文件（`~/.github-search.json`）
- 多种输出格式：文本、JSON、Markdown
- 最小依赖（仅需要 `requests`）

**安装：**
```bash
pip install requests
```

**首次设置：**
```bash
# 配置 GitHub token（一次性设置）
python scripts/github_search.py config --token YOUR_GITHUB_TOKEN

# 获取 token：https://github.com/settings/tokens
# 公共搜索无需特殊权限
```

**使用示例：**

```bash
# 仓库搜索
python scripts/github_search.py repo "machine learning" --language python --stars ">1000"
python scripts/github_search.py repo "web framework" --sort stars --limit 10

# 代码搜索
python scripts/github_search.py code "def main" --language python --limit 20
python scripts/github_search.py code "OAuth2" --repo "flask" --extension py

# 问题/PR 搜索
python scripts/github_search.py issue "bug" --state open --label "help wanted"
python scripts/github_search.py issue "feature" --is-pr --author "username"

# 速率限制检查
python scripts/github_search.py rate-limit

# 输出格式
python scripts/github_search.py repo "react" --format json --pretty
python scripts/github_search.py repo "vue" --format markdown -o results.md
```

**仓库搜索过滤器：**
- `--language`: 编程语言（例：python, javascript）
- `--stars`: 星标数量（例：">1000", "100..500"）
- `--forks`: Fork 数量
- `--user`: 用户或组织
- `--topic`: 仓库主题
- `--license`: 许可证类型（例：mit, apache-2.0）
- `--created`: 创建日期（例：">2024-01-01"）
- `--pushed`: 最后推送日期
- `--archived`: 归档状态（true/false）
- `--sort`: 排序方式（stars, forks, help-wanted-issues, updated）
- `--order`: 排序顺序（asc/desc）

**代码搜索过滤器：**
- `--language`: 编程语言
- `--repo`: 仓库（owner/name）
- `--path`: 文件路径
- `--extension`: 文件扩展名

**问题/PR 搜索过滤器：**
- `--state`: open 或 closed
- `--is-pr`: 仅拉取请求
- `--is-issue`: 仅问题
- `--author`: 问题作者
- `--assignee`: 指派人
- `--label`: 标签
- `--milestone`: 里程碑
- `--repo`: 仓库（owner/name）

**配置：**
Token 优先级（从高到低）：
1. `--token` 命令行选项
2. `GITHUB_TOKEN` 环境变量
3. 配置文件（`~/.github-search.json`）

**速率限制：**
- 已认证：30 次搜索/分钟，5000 次核心请求/小时
- 未认证：10 次搜索/分钟，60 次核心请求/小时

### 1. Reddit 搜索 (`scripts/reddit_search.py`)
**新功能** - 搜索 Reddit 帖子、子版块、用户，并获取详细信息。

**主要特性：**
- 跨所有子版块的全站搜索
- 子版块特定搜索
- 帖子详情，可选评论树提取
- 用户活动历史（帖子和评论）
- 按分类获取子版块帖子（hot, top, new, rising）
- 无需 API 密钥（使用公开 JSON 端点）
- 多种输出格式：文本、JSON、Markdown
- 自动重试和速率限制保护
- 最小依赖（仅需要 `requests`）

**安装：**
```bash
pip install requests
```

**使用示例：**

```bash
# 全站搜索
python scripts/reddit_search.py search "python tutorial" --limit 10

# 子版块搜索
python scripts/reddit_search.py subreddit-search python "async await" --limit 10

# 获取帖子详情（不包含评论）
python scripts/reddit_search.py post /r/python/comments/abc123/title/

# 获取帖子详情（包含评论）
python scripts/reddit_search.py post /r/python/comments/abc123/title/ --include-comments

# 获取用户数据
python scripts/reddit_search.py user spez --limit 20

# 获取用户的帖子
python scripts/reddit_search.py user spez --content-type submitted --limit 10

# 获取用户的评论
python scripts/reddit_search.py user spez --content-type comments --limit 10

# 获取子版块热门帖子
python scripts/reddit_search.py subreddit-posts python --category hot --limit 10

# 获取子版块本周最热帖子
python scripts/reddit_search.py subreddit-posts python --category top --time-filter week --limit 20

# 保存原始响应
python scripts/reddit_search.py search "machine learning" --save-raw

# 输出格式
python scripts/reddit_search.py search "AI" --format json --pretty
python scripts/reddit_search.py search "AI" --format markdown -o results.md
```

**命令：**

1. **search** - 全站搜索
   - `query`: 搜索关键词（必需）
   - `--limit`: 结果数量（默认: 10, 最大: 100）
   - `--sort`: 排序方式（relevance, hot, top, new, comments）

2. **subreddit-search** - 子版块搜索
   - `subreddit`: 子版块名称（必需）
   - `query`: 搜索关键词（必需）
   - `--limit`: 结果数量（默认: 10）
   - `--sort`: 排序方式

3. **post** - 获取帖子详情
   - `permalink`: 帖子链接（必需，例: /r/python/comments/abc123/title/）
   - `--include-comments`: 包含评论内容（可选）

4. **user** - 获取用户数据
   - `username`: 用户名（必需）
   - `--limit`: 结果数量（默认: 10）
   - `--content-type`: 内容类型（overview, submitted, comments）

5. **subreddit-posts** - 获取子版块帖子
   - `subreddit`: 子版块名称（必需）
   - `--category`: 分类（hot, top, new, rising）
   - `--limit`: 结果数量（默认: 10）
   - `--time-filter`: 时间过滤（all, day, week, month, year，仅用于 top）

**通用参数：**
- `--format`: 输出格式（text, json, markdown，默认: text）
- `--pretty`: 格式化 JSON 输出
- `-o, --output`: 保存输出到文件
- `--save-raw`: 保存原始响应到 responses/ 目录
- `--verbose`: 详细日志输出

**输出信息：**
默认输出包含：
- 帖子标题
- 作者和子版块
- 评分（score）和点赞率（upvote_ratio）
- 评论数量（num_comments）
- 帖子链接
- 视频/NSFW 标记（如果适用）

使用 `--include-comments` 时会额外获取完整的评论树结构。

**速率限制：**
- 自动随机延迟 1-2 秒防止限流
- 自动重试机制（5次重试，指数退避）
- 无需 API 密钥，使用 Reddit 公开 JSON 端点

### 2. 多平台图片搜索 (`scripts/image_search/multi_platform_image_search.py`)
**新功能** - 同时从 17 个平台搜索和下载图片。

**支持的平台：**
- 搜索引擎：百度、Bing、Google、360、搜狗、DuckDuckGo、Yandex、Yahoo
- 图库网站：Pixabay、Pexels、Unsplash、Foodiesfeed
- 动漫图片：Danbooru、Gelbooru、Safebooru
- 其他：花瓣网（Huaban）、次元小镇（DimTown）

**主要特性：**
- 批量搜索所有 17 个平台或选定平台
- 有序输出：每个平台有自己的子文件夹
- 自动保存元数据（JSON 格式）
- 进度跟踪和摘要报告（JSON + Markdown）
- 完全独立（仅需要 `pip install pyimagedl`）

**安装：**
```bash
pip install pyimagedl
```

**使用：**
```bash
# Search all platforms
python scripts/image_search/multi_platform_image_search.py "cute cats" --num 50

# Search specific platforms only
python scripts/image_search/multi_platform_image_search.py --keyword "sunset" --platforms baidu google pixabay --num 30

# Custom output directory
python scripts/image_search/multi_platform_image_search.py --keyword "flowers" --output ./my_images --num 100

# List all supported platforms
python scripts/image_search/multi_platform_image_search.py --list-platforms

# Quick test
python scripts/image_search/test_image_search.py
```

**输出结构：**
```
image_downloads/
├── baidu_cute_cats_20260130_123456/
│   ├── 00000001.jpg
│   ├── 00000002.png
│   └── metadata.json
├── google_cute_cats_20260130_123457/
│   ├── 00000001.jpg
│   └── metadata.json
├── pixabay_cute_cats_20260130_123458/
│   └── ...
├── search_summary.json
└── search_summary.md
```

**命令行参数：**

| 参数 | 简写 | 描述 | 默认值 |
|-----------|-------|-------------|---------|
| `--keyword` | `-k` | 搜索关键词（必需） | - |
| `--platforms` | `-p` | 指定平台列表 | 所有平台 |
| `--num` | `-n` | 每个平台的图片数量 | 50 |
| `--output` | `-o` | 输出目录 | `image_downloads` |
| `--threads` | `-t` | 下载线程数 | 5 |
| `--no-metadata` | - | 不保存元数据 | False |
| `--delay` | - | 平台间延迟（秒） | 1.0 |
| `--list-platforms` | - | 列出所有平台 | - |

**Python API 使用：**
```python
from multi_platform_image_search import MultiPlatformImageSearcher

# Create searcher
searcher = MultiPlatformImageSearcher(
    output_dir='./my_images',
    num_threads=5,
    save_metadata=True
)

# Search all platforms
results = searcher.search_all_platforms(
    keyword='cute cats',
    num_images=50
)

# Search specific platforms
results = searcher.search_all_platforms(
    keyword='sunset',
    num_images=30,
    platforms=['baidu', 'google', 'pixabay']
)

# Single platform search
result = searcher.search_platform(
    platform='unsplash',
    keyword='nature',
    num_images=100
)
```

**元数据格式：**
每个平台目录包含一个 `metadata.json` 文件，包括：
- 平台名称和搜索关键词
- 时间戳和图片总数
- 图片详情：索引、标识符、URL、文件路径、原始数据（标签、点赞、浏览量等）

**搜索摘要报告：**
- `search_summary.json`: JSON 格式的完整结果
- `search_summary.md`: 包含统计数据、成功/失败表格的可读 Markdown 报告

### 3. 小红书搜索 (`scripts/tikhub_xhs_search.py`)
搜索小红书笔记，支持过滤和排序功能。

**主要特性：**
- 按时间范围、内容类型（图片/视频）过滤
- 按点赞、评论、分享排序
- 提取话题标签（仅 `#` 前缀标签）
- 输出包括：笔记 ID、作者、类型、互动指标、标签、标题、内容

**使用：**
```bash
python scripts/tikhub_xhs_search.py --keyword "关键词" --limit 10 --sort-field likes --sort-order desc
```

### 4. 抖音搜索 (`scripts/tikhub_douyin_search.py`)
搜索抖音视频，支持全面的过滤选项。

**主要特性：**
- 按发布时间、时长、内容类型过滤
- 按互动指标排序
- 支持游标分页

**使用：**
```bash
python scripts/tikhub_douyin_search.py --keyword "关键词" --limit 10
```

### 5. Bilibili 搜索

本技能包提供两种 Bilibili 搜索方式：

#### 5.1 TikHub API 搜索 (`scripts/bilibili/tikhub_bili_search.py`)
基于 TikHub API 的简单搜索工具。

**特点**:
- 使用 TikHub API
- 需要 API Token
- 返回原始 JSON 数据
- 轻量级，无额外依赖

**使用：**
```bash
python scripts/bilibili/tikhub_bili_search.py "原神" --page 1 --page-size 20
```

#### 5.2 Bilibili API 高级搜索 (`scripts/bilibili/bilibili_api_search.py`)
**新功能** - 基于官方 bilibili-api 库的高级搜索工具，功能更强大。

**主要特性：**
- 使用官方 bilibili-api 库，无需 API Token
- 获取详细视频信息（互动数据、UP主信息、标签等）
- 支持多种输出格式（文本、JSON、Markdown）
- 自动按播放量排序
- 支持多种排序方式（综合、播放量、发布时间、弹幕、收藏）
- 完善的错误处理和重试机制

**安装：**
```bash
pip install bilibili-api-python aiohttp
```

**Usage examples:**
```bash
# 基础搜索（默认返回10个结果）
python scripts/bilibili/bilibili_api_search.py "Python教程"

# 指定结果数量
python scripts/bilibili/bilibili_api_search.py "原神" --limit 5

# 按播放量排序
python scripts/bilibili/bilibili_api_search.py "机器学习" --order click --limit 10

# 按发布时间排序
python scripts/bilibili/bilibili_api_search.py "AI" --order pubdate --limit 10

# JSON 格式输出
python scripts/bilibili/bilibili_api_search.py "编程" --json --pretty

# Markdown 格式输出并保存
python scripts/bilibili/bilibili_api_search.py "教程" --markdown -o results.md

# 只获取基础信息（不获取详细数据，更快）
python scripts/bilibili/bilibili_api_search.py "游戏" --no-details --limit 20

# 保存原始响应
python scripts/bilibili/bilibili_api_search.py "音乐" --save-raw

# 测试功能
python scripts/bilibili/test_bilibili_api.py
```

**排序方式:**
- `totalrank` - 综合排序（默认）
- `click` - 按播放量
- `pubdate` - 按发布时间
- `dm` - 按弹幕数
- `stow` - 按收藏数

**输出信息:**

基础信息：
- 标题、BVID、作者、UP主ID
- 时长、发布时间、视频链接

详细信息（默认获取，使用 `--no-details` 可跳过）：
- 互动数据：播放量、弹幕、点赞、投币、收藏、转发、评论
- 视频信息：AV号、分区、版权、简介
- UP主信息：昵称、UID、头像
- 视频标签

**选择建议:**
- 需要简单快速的搜索 → 使用 `tikhub_bili_search.py`
- 需要详细的视频信息和互动数据 → 使用 `bilibili_api_search.py`
- 需要生成报告或分析数据 → 使用 `bilibili_api_search.py`

### 4. Twitter Search (`scripts/tikhub_twitter_search.py`)
Search Twitter posts and timelines.

**Usage:**
```bash
python scripts/tikhub_twitter_search.py --keyword "关键词" --limit 10
```

### 5. Google Custom Search (`scripts/google_search/google_search.py`)
**NEW** - Search web content using Google Custom Search API with advanced features.

**Key features:**
- Web search with configurable result count
- Image search with size filtering
- Language-specific search
- Multiple output formats: text, JSON
- Clean, formatted terminal output

**安装：**
```bash
pip install requests python-dotenv
```

**首次设置：**
1. 在此获取 Google API Key：https://console.cloud.google.com/apis/credentials
2. 在此创建自定义搜索引擎：https://programmablesearchengine.google.com/
3. 将 API 凭据添加到 `.env`：
   ```bash
   GOOGLE_API_KEY=your_api_key
   GOOGLE_SEARCH_ENGINE_ID=your_search_engine_id
   ```

**使用示例：**

```bash
# 基础网络搜索
python scripts/google_search/google_search.py "Python tutorial" -n 5

# 中文搜索
python scripts/google_search/google_search.py "人工智能" --lang zh-CN -n 10

# 图片搜索
python scripts/google_search/google_search.py "sunset" --image -n 10

# 带尺寸过滤的图片搜索
python scripts/google_search/google_search.py "wallpaper" --image --img-size large

# JSON 输出
python scripts/google_search/google_search.py "Claude AI" --json --pretty
```

**参数：**

| 参数 | 描述 | 默认值 |
|-----------|-------------|---------|
| `query` | 搜索关键词（必需） | - |
| `-n, --num` | 结果数量（1-10） | 10 |
| `--lang` | 语言代码（例：zh-CN, en） | - |
| `--image` | 启用图片搜索 | False |
| `--img-size` | 图片尺寸（icon/small/medium/large/xlarge/xxlarge/huge） | - |
| `--json` | JSON 格式输出 | False |
| `--pretty` | 格式化 JSON 输出 | False |

**输出信息：**
- 结果总数
- 搜索时间
- 每个结果的标题、链接和摘要
- 图片搜索：图片尺寸和缩略图链接

### 8. Tavily 搜索 (`scripts/tavily_search/tavily_search.py`)
**新功能** - 为 LLM 应用优化的 AI 驱动搜索引擎。

**主要特性：**
- 带 AI 生成答案的实时网络搜索
- 多种搜索深度：basic、advanced、fast
- 特定主题搜索：general、news、finance
- 可选的 AI 生成答案摘要
- 多种输出格式：文本、JSON

**安装：**
```bash
pip install tavily-python python-dotenv
```

**首次设置：**
1. 在此获取 API key：https://tavily.com（有免费套餐）
2. 添加到 `.env`：
   ```bash
   TAVILY_API_KEY=tvly-your_api_key
   ```

**使用示例：**

```bash
# 基础搜索
python scripts/tavily_search/tavily_search.py "AI latest developments" --max-results 5

# 新闻搜索
python scripts/tavily_search/tavily_search.py "technology news" --topic news --max-results 10

# 带 AI 答案的高级搜索
python scripts/tavily_search/tavily_search.py "quantum computing" --search-depth advanced --include-answer --max-results 5

# 快速搜索
python scripts/tavily_search/tavily_search.py "Python vs JavaScript" --search-depth fast --max-results 3

# JSON 输出
python scripts/tavily_search/tavily_search.py "machine learning" --json --pretty
```

**参数：**

| 参数 | 描述 | 默认值 |
|-----------|-------------|---------|
| `query` | 搜索关键词（必需） | - |
| `--max-results` | 最大结果数 | 5 |
| `--search-depth` | 搜索深度：basic/advanced/fast | basic |
| `--topic` | 主题：general/news/finance | general |
| `--include-answer` | 包含 AI 生成的答案 | False |
| `--json` | JSON 格式输出 | False |
| `--pretty` | 格式化 JSON 输出 | False |

**输出信息：**
- AI 生成的答案摘要（如果启用）
- 搜索结果，包含标题、URL 和内容摘要
- 结果总数

### 9. YouTube 搜索 (`scripts/youtube/youtube_search.py`)
**新功能** - 搜索 YouTube 视频，获取详细信息、统计数据和评论。

**主要特性：**
- 按关键词搜索视频，支持多种排序选项
- 获取详细视频信息（标题、频道、发布日期、时长）
- 检索互动统计数据（观看量、点赞数、评论数）
- 可选评论提取（热门评论）
- 多种输出格式：文本、JSON、Markdown
- 自动响应归档
- 无外部依赖（仅使用标准库）

**安装：**
无需额外依赖 - 仅使用 Python 标准库。

**首次设置：**
在此获取 YouTube Data API key：https://console.cloud.google.com/apis/credentials

**使用示例：**

```bash
# 基础搜索
python scripts/youtube/youtube_search.py "Python tutorial" --limit 5

# 带排序的搜索
python scripts/youtube/youtube_search.py "机器学习" --order viewCount --limit 10

# 包含评论
python scripts/youtube/youtube_search.py "AI" --include-comments --max-comments 5

# JSON 输出
python scripts/youtube/youtube_search.py "编程" --json --pretty

# Markdown 输出
python scripts/youtube/youtube_search.py "教程" --markdown -o results.md

# 保存原始响应
python scripts/youtube/youtube_search.py "Python" --save-raw

# 测试功能
python scripts/youtube/test_youtube_search.py
```

**参数：**

| 参数 | 描述 | 默认值 |
|-----------|-------------|---------|
| `keyword` | 搜索关键词（必需） | - |
| `--api-key` | YouTube Data API key | 从 .env 读取 |
| `--limit` | 最大结果数（1-50） | 10 |
| `--order` | 排序方式：relevance/date/rating/viewCount/title | relevance |
| `--region` | 地区代码（例：US, CN） | US |
| `--language` | 语言代码（例：zh-CN, en） | zh-CN |
| `--include-comments` | 包含评论部分 | False |
| `--max-comments` | 每个视频的最大评论数 | 10 |
| `--json` | JSON 格式输出 | False |
| `--pretty` | 格式化 JSON 输出 | False |
| `--markdown` | Markdown 格式输出 | False |
| `-o, --output` | 保存输出到文件 | - |
| `--save-raw` | 保存原始响应到 responses/ | False |

**输出信息：**

基础信息：
- 视频 ID、标题、频道名称、频道 ID
- 发布日期、时长、视频 URL
- 缩略图（default, medium, high, standard, maxres）

视频详情：
- 分类 ID、清晰度（HD/SD）、字幕可用性
- 视频标签、描述

互动统计：
- 观看量、点赞数、评论数

评论（可选）：
- 作者名称、作者频道 ID
- 评论文本、点赞数
- 发布日期、更新日期

**排序选项：**
- `relevance` - 最相关（默认）
- `date` - 最新优先
- `rating` - 最高评分
- `viewCount` - 最多观看
- `title` - 字母顺序

**配置：**

提供 API key 的三种方式（优先级顺序）：

1. **命令行参数**（最高优先级）
   ```bash
   python scripts/youtube/youtube_search.py "keyword" --api-key YOUR_API_KEY
   ```

2. **环境变量**（`.env` 文件）
   ```bash
   YOUTUBE_API_KEY=YOUR_API_KEY
   ```

3. **直接在脚本中**（出于安全考虑不推荐）

**API 配额：**
- 搜索：每次请求 100 单位
- Videos.list：每次请求 1 单位
- CommentThreads.list：每次请求 1 单位
- 每日配额：10,000 单位（默认）

**重要说明：**
- 所有请求都需要 API key
- 某些视频可能禁用了评论
- 每次搜索请求最多 50 个结果
- 遵守 YouTube API 速率限制

### 10. 微博搜索 (`scripts/weibo/weibo_search.py`)
**新功能** - 搜索微博用户信息和帖子，支持全面的过滤选项。

**主要特性：**
- 集成 weiboSpider 项目，实现可靠的数据提取
- 获取用户资料信息（昵称、性别、地区、粉丝数等）
- 获取用户的微博帖子，包含完整内容和互动指标
- 按原创帖子过滤或包含转发
- 时间范围过滤（since_date, end_date）
- 按发布时间、点赞、转发或评论排序
- 支持一次查询多个用户
- 多种输出格式：文本、JSON
- 自动响应归档

**安装：**
```bash
# 安装 weiboSpider 依赖
cd D:\Programs\weiboSpider
pip install -r requirements.txt
```

**首次设置：**
需要获取微博 cookie 进行认证。参见 [如何获取 cookie](https://github.com/dataabc/weiboSpider/blob/master/docs/cookie.md)。

**使用示例：**

```bash
# 搜索单个用户
python scripts/weibo/weibo_search.py --user-id 1669879400 --cookie "YOUR_COOKIE"

# 带过滤器搜索
python scripts/weibo/weibo_search.py --user-id 1669879400 --filter 1 --limit 20

# 搜索多个用户
python scripts/weibo/weibo_search.py --user-id 1669879400,1223178222 --since-date 2025-01-01

# 使用配置文件
python scripts/weibo/weibo_search.py --config-path D:\Programs\weiboSpider\config.json

# 按互动排序
python scripts/weibo/weibo_search.py --user-id 1669879400 --sort-by up_num --sort-order desc

# JSON 输出
python scripts/weibo/weibo_search.py --user-id 1669879400 --json --pretty

# 保存原始响应
python scripts/weibo/weibo_search.py --user-id 1669879400 --save-raw
```

**参数：**

| 参数 | 描述 | 默认值 |
|-----------|-------------|---------|
| `--user-id` | 微博用户 ID，逗号分隔 | 必需 |
| `--cookie` | 微博认证 cookie | 必需 |
| `--filter` | 0=所有微博，1=仅原创 | 0 |
| `--since-date` | 开始日期（YYYY-MM-DD） | 2025-01-01 |
| `--end-date` | 结束日期（YYYY-MM-DD 或 'now'） | now |
| `--limit` | 每个用户的最大微博数 | 10 |
| `--sort-by` | 排序字段：publish_time/up_num/retweet_num/comment_num | - |
| `--sort-order` | 排序顺序：asc/desc | desc |
| `--config-path` | weiboSpider config.json 路径 | - |
| `--json` | JSON 格式输出 | False |
| `--pretty` | 格式化 JSON 输出 | False |
| `--save-raw` | 保存原始响应到 responses/ | False |

**输出信息：**

用户信息：
- 用户 ID、昵称、性别、地区、生日
- 简介、认证状态
- 微博数、关注数、粉丝数

微博信息：
- 微博 ID、内容、发布时间、发布工具
- 发布地点（如果有）
- 原图 URL、视频 URL
- 互动指标：点赞（up_num）、转发（retweet_num）、评论（comment_num）

**配置：**

提供配置的三种方式（优先级顺序）：

1. **命令行参数**（最高优先级）
   ```bash
   python scripts/weibo/weibo_search.py --user-id 1669879400 --cookie "YOUR_COOKIE"
   ```

2. **环境变量**（`.env` 文件）
   ```bash
   WEIBO_USER_ID=1669879400
   WEIBO_COOKIE=YOUR_COOKIE
   WEIBO_FILTER=0
   WEIBO_SINCE_DATE=2025-01-01
   WEIBO_END_DATE=now
   WEIBO_LIMIT=10
   ```

3. **配置文件**（weiboSpider config.json）
   ```bash
   python scripts/weibo/weibo_search.py --config-path D:\Programs\weiboSpider\config.json
   ```

**重要说明：**
- 认证需要 Cookie（约 3 个月过期）
- 无法爬取自己的微博（用于 cookie 的账号）
- 遵守速率限制以避免被封禁
- 详细的 weiboSpider 文档，参见：https://github.com/dataabc/weiboSpider

### 11. RSS 订阅搜索 (`scripts/rss_search/rss_search.py`)
从 RSS 订阅源搜索和监控内容，支持关键词过滤和多种输出格式。

**主要特性：**
- 支持单个或多个 RSS 订阅源
- 在标题、摘要和内容中搜索关键词
- 多种输出格式：文本、JSON、Markdown
- 结果过滤和限制
- 支持配置文件管理订阅源

**安装：**
```bash
pip install feedparser
```

**使用：**
```bash
# 搜索单个 RSS 订阅源
python scripts/rss_search/rss_search.py "AI" --feed http://example.com/feed.xml --limit 10

# 从配置文件搜索多个订阅源
python scripts/rss_search/rss_search.py "GPT" --feeds rss_feeds.txt --markdown

# 获取最新条目（不使用关键词）
python scripts/rss_search/rss_search.py --feed http://example.com/feed.xml --limit 5

# 保存结果到文件
python scripts/rss_search/rss_search.py "机器学习" --feed http://example.com/feed.xml --json --pretty -o results.json
```

**参数：**
- `query`: 搜索关键词（可选，省略则返回所有条目）
- `--feed`: 单个 RSS 订阅源 URL
- `--feeds`: 包含多个订阅源 URL 的配置文件（每行一个）
- `--limit`: 最大结果数（默认：10）
- `--json`: JSON 格式输出
- `--pretty`: 格式化 JSON 输出
- `--markdown`: Markdown 格式输出
- `--full`: 包含完整内容和详情
- `-o, --output`: 保存输出到文件
- `--timeout`: 请求超时时间（秒，默认：30）
- `--case-sensitive`: 区分大小写搜索

**配置文件格式（`rss_feeds.txt`）：**
```
# AI News
http://feedmaker.kindle4rss.com/feeds/AI_era.weixin.xml

# Tech News
https://example.com/tech/rss.xml

# 以 # 开头的行是注释
```

## 配置

### 环境变量

脚本从技能目录中的 `.env` 文件或平台特定的配置文件读取配置。命令行参数会覆盖配置值。

**设置：**

1. **GitHub 搜索** - 三种配置方法（优先级顺序）：
   ```bash
   # 方法 1：配置文件（推荐）
   python scripts/github_search.py config --token YOUR_GITHUB_TOKEN

   # 方法 2：环境变量
   export GITHUB_TOKEN=YOUR_GITHUB_TOKEN

   # 方法 3：命令行
   python scripts/github_search.py repo "query" --token YOUR_GITHUB_TOKEN
   ```
   - 在此获取 token：https://github.com/settings/tokens
   - 公共搜索无需特殊权限
   - 配置文件位置：`~/.github-search.json`

2. **社交媒体和网络搜索** - `.env` 文件配置：
   - 复制 `.env.example` 到 `.env`
   - 填写 API 凭据：
     - `TIKHUB_TOKEN`: TikHub API token（用于小红书、抖音、Bilibili、Twitter）
     - `GOOGLE_API_KEY`: Google Custom Search API key
     - `GOOGLE_SEARCH_ENGINE_ID`: Google Custom Search Engine ID
     - `TAVILY_API_KEY`: Tavily Search API key
   - 配置默认搜索参数（关键词、限制、排序选项）

3. **图片搜索** - 无需配置：
   - `multi_platform_image_search.py` 开箱即用
   - 仅需要：`pip install pyimagedl`

4. **RSS 订阅搜索** - 无需 API 凭据：
   - `rss_search.py` 使用 `pip install feedparser` 即可独立运行
   - 可选：创建 `rss_feeds.txt` 管理多个订阅源 URL
   - 配置文件格式：每行一个 URL，`#` 表示注释

5. **YouTube 搜索** - 三种配置方法（优先级顺序）：
   ```bash
   # 方法 1：命令行（推荐用于测试）
   python scripts/youtube/youtube_search.py "keyword" --api-key YOUR_API_KEY

   # 方法 2：环境变量（推荐用于生产）
   # 添加到 .env 文件：
   YOUTUBE_API_KEY=YOUR_API_KEY

   # 方法 3：直接在脚本中（不推荐）
   ```
   - 在此获取 API key：https://console.cloud.google.com/apis/credentials
   - 在 Google Cloud 项目中启用 YouTube Data API v3
   - 每日配额：10,000 单位（搜索：100 单位，Videos.list：1 单位）
   - 详细设置说明参见 `scripts/youtube/README.md`

### 通用参数

- `--keyword` / `--query`: 搜索关键词
- `--limit`: 返回的结果数量（默认：10）
- `--sort-field`: 排序字段（点赞、评论、分享等）
- `--sort-order`: 排序顺序（asc/desc）
- `--time-range`: 按时间范围过滤（平台特定）

## 输出格式

### 终端输出
- **格式**：带中文字段名的 Markdown
- **内容**：结构化、人类可读的结果
- **字段**：平台特定的基本信息（ID、作者、互动指标、内容）

### 原始响应归档
- **位置**：`responses/` 目录
- **命名**：时间戳（YYYYMMDD_HHMMSS）+ 平台后缀
- **格式**：来自 API 的原始 JSON 响应
- **目的**：保留完整数据供后续分析，不会使对话上下文混乱

## 执行指南

### 运行脚本前

1. 验证 `.env` 配置存在且包含有效凭据
2. 确保 `responses/` 目录存在（脚本会自动创建）
3. 确认所需的 Python 依赖可用（仅标准库）

### 运行脚本

从技能目录直接执行脚本：

```bash
cd C:\Users\zijie\.claude\skills\union-search-skill
python scripts/tikhub_xhs_search.py --keyword "关键词" --limit 10
```

### 执行后

1. 检查终端输出的格式化结果
2. 在 `responses/` 目录中找到原始响应文件
3. 引用保存的文件路径以访问完整的 API 响应数据

## 最佳实践

### 结果过滤
- 使用 `--limit` 控制输出量（默认：10）
- 应用时间过滤器获取最新内容
- 按互动指标排序以找到热门内容

### 响应管理
- 永远不要将完整的原始 JSON 粘贴到对话中
- 需要完整数据访问时引用 `responses/` 文件
- 使用 grep/jq 从保存的响应中提取特定字段

### 多平台搜索
- 为不同平台依次运行脚本
- 使用保存的响应文件比较跨平台结果
- 聚合来自多个来源的指标

## 错误处理

常见问题和解决方案：
- **缺少凭据**：检查 `.env` 文件配置
- **API 速率限制**：降低请求频率或限制结果数量
- **网络超时**：增加 `.env` 中的 `TIKHUB_TIMEOUT` 值
- **无效参数**：验证参数名称是否符合脚本预期

## 平台特定说明

### 小红书
- 仅提取带 `#` 前缀的话题标签
- 内容类型过滤：0=全部，1=视频，2=图片
- 排序字段：likes, comments, shares, publish_time

### 抖音
- 支持按时长和内容类型的高级过滤
- 通过游标参数分页
- 搜索 ID 和回溯以保持结果一致性

### Google
- 需要设置自定义搜索引擎
- 结果数量受 API 配额限制
- 清晰的输出针对终端显示优化
