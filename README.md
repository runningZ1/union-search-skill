# Union Search Skill

统一搜索技能 - 跨平台搜索解决方案

## 概述

提供跨多个平台的统一搜索能力，包括：

1. **开发者搜索**: GitHub 仓库、代码、Issues/PRs、Reddit 帖子和讨论
2. **社交媒体与网络搜索**: 小红书、抖音、Bilibili、YouTube、Twitter、Google、Tavily
3. **图片搜索与下载**: 17 个图片平台（百度、Bing、Google、Pixabay、Unsplash 等）
4. **RSS 订阅搜索**: 搜索和监控 RSS 订阅内容，支持关键词过滤
5. **播客搜索**: 小宇宙FM播客搜索，支持关键词搜索和AI摘要

## 统一 CLI（推荐）

项目现在提供统一命令行入口，适合智能体按参数快速调用：

```bash
# 查看命令树
python union_search_cli.py --help

# 列出能力与分组
python union_search_cli.py list --pretty

# 健康检查（凭据/依赖）
python union_search_cli.py doctor --env-file .env --pretty

# 多平台聚合搜索
python union_search_cli.py search "AI Agent" --group dev --limit 3 --pretty

# 单平台调用
python union_search_cli.py platform github "machine learning" --limit 5 --pretty

# 单平台直达命令（新增）
python union_search_cli.py google "AI Agent" --limit 5 --pretty
python union_search_cli.py bing "AI Agent" --limit 5 --pretty
python union_search_cli.py bsearch "AI Agent" --limit 5 --pretty

# 图片搜索与下载
python union_search_cli.py image "cats" --platforms pixabay bing --limit 10 --output-dir ./image_downloads --pretty
```

说明：
- 统一输出协议：默认 `json`，可选 `--format markdown|text`
- 全部命令支持 `--output` 输出到文件
- 单平台支持两种方式：`platform <name> ...` 或 `<platform> ...`（如 `google ...`）
- 旧的 `python scripts/<platform>/*.py` 用法仍可继续使用

## 平台可用性公告

以下 3 个平台当前在本项目中暂不可用，正在开发和修复中：

1. **Reddit**
   当前常见失败现象：`403`（请求被拒绝）。
2. **Weibo (微博)**
   当前状态：依赖 `WEIBO_COOKIE` 和 `WEIBO_USER_ID`，且模块仍在完善。
3. **Volcengine (火山引擎)**
   当前常见失败现象：响应解析失败（空响应/非 JSON）。

如需稳定使用，请优先选择 README 中其他可用平台。

## 支持的平台

### 开发者搜索
- **GitHub** - 搜索仓库、代码、Issues/PRs，支持高级筛选
- **Reddit** - 搜索帖子、子版块、用户，获取详细信息和评论

### 社交媒体与网络搜索
- **Xiaohongshu (小红书)** - 搜索笔记，支持筛选和排序
- **Douyin (抖音)** - 搜索视频，支持综合筛选
- **Bilibili** - 搜索视频和内容
- **Twitter** - 搜索推文和时间线
- **YouTube** - 搜索视频、统计数据和评论
- **Google** - 使用 Google Custom Search API 进行网络搜索
- **Tavily** - AI 优化的搜索引擎，支持智能摘要
- **Metaso (秘塔搜索)** - AI 驱动的网络搜索，提供智能摘要
- **Volcengine (火山引擎)** - 字节跳动融合信息搜索，支持 Web 搜索和 AI 摘要
  - **注意**: 图片搜索功能已集成到 union_image_search 模块

### 通用搜索引擎（无需 API 密钥）
- **DuckDuckGo** - 隐私友好的搜索引擎，支持分页和时间过滤
- **Brave** - 隐私保护搜索，支持安全搜索设置
- **Yahoo** - 传统搜索引擎，支持时间过滤
- **Bing** - 微软搜索引擎，支持多语言和地区
- **Wikipedia** - 维基百科搜索，支持多语言和详细摘要
- **Anna's Archive** - 电子书搜索，海量书籍资源

### 图片搜索与下载（18 个平台）
- **搜索引擎**: 百度、Bing、Google、360、搜狗、DuckDuckGo、Yandex、Yahoo
- **图库网站**: Pixabay、Pexels、Unsplash、Foodiesfeed
- **动漫图片**: Danbooru、Gelbooru、Safebooru
- **其他**: 花瓣网、次元小镇、火山引擎 (API-based)

### RSS 订阅搜索
- 支持单个或多个 RSS 订阅源
- 关键词搜索（标题、摘要、内容）
- 多种输出格式

### 播客搜索
- **小宇宙FM** - 搜索播客内容，获取标题、摘要、主播、时长等元数据

## 快速开始

### 1. 安装依赖

```bash
# 基础依赖（所有脚本共用）
pip install requests python-dotenv lxml

# 图片搜索（可选）
pip install pyimagedl

# Bilibili 搜索（可选）
# 依赖本地项目 D:/Programs/bilibili-api
pip install curl_cffi

# Tavily 搜索（可选）
pip install tavily-python

# RSS 搜索（可选）
pip install feedparser
```

### 2. 配置凭证

**GitHub 搜索（推荐方式）：**
```bash
# 一次性配置
python scripts/github_search.py config --token YOUR_GITHUB_TOKEN

# 获取 token: https://github.com/settings/tokens
# 公共搜索无需特殊权限
```

**社交媒体与网络搜索：**
```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件，填入 API 凭证
# - TIKHUB_TOKEN: TikHub API token
# - GOOGLE_API_KEY: Google API key
# - GOOGLE_SEARCH_ENGINE_ID: Google Search Engine ID
# - TAVILY_API_KEY: Tavily API key
# - YOUTUBE_API_KEY: YouTube Data API key
# - METASO_API_KEY: 秘塔搜索 API key
# - VOLCENGINE_API_KEY: 火山引擎 API key
```

### 3. 使用示例

**GitHub 搜索：**
```bash
python scripts/github_search.py repo "machine learning" --language python --stars ">1000"
```

**Google Custom Search 搜索：**
```bash
python scripts/google_search/google_search.py "人工智能" -n 5
```

**Tavily 搜索：**
```bash
python scripts/tavily_search/tavily_search.py "AI 最新进展" --max-results 5
```

**秘塔搜索：**
```bash
python scripts/metaso/metaso_search.py "人工智能发展趋势" --size 10
```

**火山引擎搜索：**
```bash
# Web 搜索
python scripts/volcengine/volcengine_search.py web "北京旅游攻略"

# Web 搜索 + AI 摘要
python scripts/volcengine/volcengine_search.py summary "量子计算"

# 图片搜索 (使用 union_image_search)
python scripts/union_image_search/multi_platform_image_search.py --keyword "风景" --platforms volcengine
```

**小红书搜索：**
```bash
python scripts/tikhub_xhs_search.py --keyword "美食" --limit 10
```

**图片搜索：**
```bash
python scripts/union_image_search/multi_platform_image_search.py --keyword "cute cats" --num 50
```

**通用搜索引擎（无需 API 密钥）：**
```bash
# DuckDuckGo 搜索
python scripts/duckduckgo/duckduckgo_search.py "Python programming"

# Brave 搜索
python scripts/brave/brave_search.py "machine learning"

# Yahoo 搜索
python scripts/yahoo/yahoo_search.py "artificial intelligence"

# Bing 搜索
python scripts/bing/bing_search.py "deep learning"

# Wikipedia 搜索
python scripts/wikipedia/wikipedia_search.py "Albert Einstein"

# Anna's Archive 书籍搜索
python scripts/annasarchive/annasarchive_search.py "Python programming"
```

## 功能特性

### GitHub 搜索
- ✅ 搜索仓库（按语言、星标、主题等筛选）
- ✅ 搜索代码（跨所有公共仓库）
- ✅ 搜索 Issues 和 Pull Requests
- ✅ 速率限制检查
- ✅ 多种输出格式（文本、JSON、Markdown）
- ✅ 配置文件支持
- ✅ 最小依赖（仅需 requests）

### Reddit 搜索
- ✅ 全站搜索和子版块搜索
- ✅ 获取帖子详情和评论
- ✅ 用户活动历史
- ✅ 无需 API 密钥
- ✅ 自动重试和限流保护

### Google Custom Search
- ✅ 网页搜索和图片搜索
- ✅ 语言过滤
- ✅ JSON 和文本输出
- ✅ 干净的终端输出

### Tavily Search
- ✅ AI 优化的搜索引擎
- ✅ 多种搜索深度（basic/advanced/fast）
- ✅ 特定主题搜索（general/news/finance）
- ✅ 可选 AI 生成的答案摘要

### 社交媒体搜索
- 小红书：按时间、内容类型、互动指标筛选
- 抖音：高级筛选（时长、内容类型）
- Bilibili：视频搜索（依赖本地项目 `D:/Programs/bilibili-api`）
- Twitter：推文和时间线搜索
- YouTube：详细视频信息和评论

### 图片搜索
- 17 个平台同时搜索
- 自动元数据保存
- 进度跟踪和摘要报告
- 按平台组织输出

### RSS 订阅搜索
- 单个或多个订阅源支持
- 关键词搜索
- 多种输出格式
- 配置文件支持

### 通用搜索引擎
- DuckDuckGo：隐私友好，无需 API 密钥
- Brave：隐私保护，支持安全搜索
- Yahoo：传统搜索，自动处理 URL 重定向
- Bing：多语言支持，自动解码 URL
- Wikipedia：多语言百科，自动获取摘要
- Anna's Archive：电子书搜索，海量资源

## 使用示例

### GitHub 搜索

```bash
# 搜索仓库
python scripts/github_search.py repo "machine learning" --language python --stars ">1000"
python scripts/github_search.py repo "web framework" --sort stars --limit 10

# 搜索代码
python scripts/github_search.py code "async def" --language python --limit 20
python scripts/github_search.py code "OAuth2" --repo "flask" --extension py

# 搜索 Issues
python scripts/github_search.py issue "bug" --state open --label "help wanted"
python scripts/github_search.py issue "feature" --is-pr --author "username"

# 检查速率限制
python scripts/github_search.py rate-limit
```

### Google Custom Search

```bash
# 基础搜索
python scripts/google_search/google_search.py "Python tutorial" -n 5

# 中文搜索
python scripts/google_search/google_search.py "人工智能" --lang zh-CN -n 10

# 图片搜索
python scripts/google_search/google_search.py "sunset" --image -n 10
```

### Tavily Search

```bash
# 基础搜索
python scripts/tavily_search/tavily_search.py "AI 最新进展" --max-results 5

# 新闻搜索
python scripts/tavily_search/tavily_search.py "科技新闻" --topic news --max-results 10

# 高级搜索（含 AI 答案）
python scripts/tavily_search/tavily_search.py "量子计算" --search-depth advanced --include-answer
```

### Reddit 搜索

```bash
# 全站搜索
python scripts/reddit_search.py search "python tutorial" --limit 10

# 子版块搜索
python scripts/reddit_search.py subreddit-search python "async await" --limit 10

# 获取帖子详情（含评论）
python scripts/reddit_search.py post /r/python/comments/abc123/title/ --include-comments
```

### 小红书搜索

```bash
python scripts/tikhub_xhs_search.py --keyword "美食" --limit 10 --sort-field likes --sort-order desc
```

### Bilibili 搜索

> ⚠️ **注意**：Bilibili 搜索依赖本地项目 `D:/Programs/bilibili-api`，请确保该目录存在。

```bash
# 官方 API 搜索（功能更全）
python scripts/bilibili/search.py video Python教程
python scripts/bilibili/search.py user 老番茄
python scripts/bilibili/search.py hot
```

### YouTube 搜索

```bash
# 基础搜索
python scripts/youtube/youtube_search.py "Python tutorial" --limit 5

# 包含评论
python scripts/youtube/youtube_search.py "AI" --include-comments --max-comments 5

# JSON 输出
python scripts/youtube/youtube_search.py "编程" --json --pretty

### 多平台图片搜索

```bash
# 搜索所有平台 (包括火山引擎)
python scripts/union_image_search/multi_platform_image_search.py --keyword "cute cats" --num 50

# 搜索指定平台
python scripts/union_image_search/multi_platform_image_search.py --keyword "sunset" --platforms baidu google pixabay volcengine --num 30

# 自定义输出目录
python scripts/union_image_search/multi_platform_image_search.py --keyword "flowers" --output ./my_images --num 100
```

### RSS 订阅搜索

```bash
# 搜索单个订阅源
python scripts/rss_search/rss_search.py "AI" --feed http://example.com/feed.xml --limit 10

# 搜索多个订阅源
python scripts/rss_search/rss_search.py "GPT" --feeds rss_feeds.txt --markdown
```

### 小宇宙FM播客搜索

```bash
# 基础搜索
python scripts/xiaoyuzhoufm/xiaoyuzhou_search.py "人工智能"

# 限制结果数量
python scripts/xiaoyuzhoufm/xiaoyuzhou_search.py "创业故事" --size 5

# JSON格式输出
python scripts/xiaoyuzhoufm/xiaoyuzhou_search.py "心理学" --json

# 包含AI摘要
python scripts/xiaoyuzhoufm/xiaoyuzhou_search.py "投资理财" --summary
```

### 通用搜索引擎

```bash
# DuckDuckGo 搜索
python scripts/duckduckgo/duckduckgo_search.py "Python programming" -p 1 -m 10
python scripts/duckduckgo/duckduckgo_search.py "AI research" -t d --json

# Brave 搜索
python scripts/brave/brave_search.py "blockchain" -p 2 -m 15
python scripts/brave/brave_search.py "tech news" -t w -s strict

# Yahoo 搜索
python scripts/yahoo/yahoo_search.py "quantum computing" -p 2 -m 15
python scripts/yahoo/yahoo_search.py "breaking news" -t d --json

# Bing 搜索
python scripts/bing/bing_search.py "neural networks" -p 2 -m 15
python scripts/bing/bing_search.py "local search" -l zh -c cn

# Wikipedia 搜索
python scripts/wikipedia/wikipedia_search.py "Albert Einstein" -m 5
python scripts/wikipedia/wikipedia_search.py "人工智能" -l zh --json

# Anna's Archive 书籍搜索
python scripts/annasarchive/annasarchive_search.py "Python programming" -p 1 -m 10
python scripts/annasarchive/annasarchive_search.py "machine learning" --json
```

## 项目结构

```
union-search-skill/
├── scripts/                    # 所有搜索脚本
│   ├── union_search/           # 联合搜索
│   ├── github/                # GitHub 搜索
│   ├── reddit/                # Reddit 搜索
│   ├── xiaohongshu/           # 小红书搜索
│   ├── douyin/                # 抖音搜索
│   ├── bilibili/              # Bilibili 搜索
│   ├── youtube/               # YouTube 搜索
│   ├── google_search/         # Google 搜索
│   ├── tavily_search/         # Tavily 搜索
│   ├── duckduckgo/            # DuckDuckGo 搜索
│   ├── brave/                 # Brave 搜索
│   ├── yahoo/                 # Yahoo 搜索
│   ├── bing/                  # Bing 搜索
│   ├── wikipedia/             # Wikipedia 搜索
│   ├── annasarchive/          # Anna's Archive 搜索
│   ├── union_image_search/    # 图片搜索
│   ├── rss_search/            # RSS 搜索
│   └── zhihu/                 # 知乎搜索
├── references/                 # 参考文档（全局）
│   ├── api_credentials.md     # API 凭据获取指南
│   ├── rate_limits.md         # 速率限制说明
│   ├── platform_notes.md      # 平台特定说明
│   ├── troubleshooting.md     # 问题排查指南
│   └── google_search_guide.md # Google 搜索技巧
├── responses/                  # API 响应存档
├── .env.example               # 环境变量模板
├── SKILL.md                   # 完整技能文档（中文）
└── README.md                  # 本文件
```

## 配置说明

### 环境变量 (.env)

| 变量名 | 说明 | 获取地址 |
|--------|------|----------|
| `GITHUB_TOKEN` | GitHub API Token | https://github.com/settings/tokens |
| `TIKHUB_TOKEN` | TikHub API Token | https://www.tikhub.io |
| `GOOGLE_API_KEY` | Google API Key | https://console.cloud.google.com/apis/credentials |
| `GOOGLE_SEARCH_ENGINE_ID` | Google Search Engine ID | https://programmablesearchengine.google.com/ |
| `TAVILY_API_KEY` | Tavily API Key | https://tavily.com |
| `YOUTUBE_API_KEY` | YouTube Data API Key | https://console.cloud.google.com/apis/credentials |
| `ZHIHU_COOKIE` | 知乎 Cookie | 知乎网站 |

## 速率限制

### GitHub API
- **已认证**: 30 次搜索/分钟，5000 次核心请求/小时
- **未认证**: 10 次搜索/分钟，60 次核心请求/小时

### YouTube API
- 搜索: 100 单位/请求
- Videos.list: 1 单位/请求
- 每日配额: 10,000 单位（默认）

### 其他平台
请参考各平台 API 文档

## 常见问题

### GitHub 搜索

**Q: 如何获取 GitHub token？**
A: 访问 https://github.com/settings/tokens，点击 "Generate new token (classic)"，公共搜索无需特殊权限。

**Q: Token 存储在哪里？**
A: 配置文件位于 `~/.github-search.json`。

### Google Custom Search

**Q: 如何创建搜索引擎？**
A: 访问 https://programmablesearchengine.google.com/，点击"添加"或"新增搜索引擎"，选择"搜索整个网络"。

### Tavily Search

**Q: 是否有免费额度？**
A: 是的，Tavily 提供免费层级，每月 1000 积分。

## 更新日志

### v4.0.0 (2026-02-01)
- ✨ 新增 DuckDuckGo 搜索模块（无需 API 密钥）
- ✨ 新增 Brave 搜索模块（无需 API 密钥）
- ✨ 新增 Yahoo 搜索模块（无需 API 密钥）
- ✨ 新增 Bing 搜索模块（无需 API 密钥）
- ✨ 新增 Wikipedia 搜索模块（无需 API 密钥）
- ✨ 新增 Anna's Archive 书籍搜索模块（无需 API 密钥）
- 📦 添加 lxml 依赖用于 HTML 解析
- 📝 为所有新模块添加完整文档

### v3.0.0 (2026-02-01)
- ✨ 新增 Reddit 搜索功能
- ✨ 新增 Google Custom Search 模块
- ✨ 新增 Tavily Search 模块
- ✨ 新增 YouTube 搜索功能
- ✨ 新增 RSS 订阅搜索功能
- 📝 更新文档为中文

### v2.0.0 (2026-01-31)
- ✨ 新增 GitHub 搜索功能
- ✨ 独立的 `github_search.py` 脚本
- 📝 更新文档

### v1.0.0
- 初始版本
- 支持小红书、抖音、Bilibili、Twitter、Google 搜索
- 支持 17 个平台的图片搜索

## 许可证

MIT License
