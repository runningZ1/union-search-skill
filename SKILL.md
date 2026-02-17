---
name: union-search-skill
description: 当用户需要跨多个平台搜索内容时使用此技能，包括 GitHub（仓库、代码、问题）、Reddit（帖子、子版块、用户）、小红书、抖音、Bilibili、YouTube、Twitter、微博、Google、Tavily、秘塔搜索、火山引擎，以及通用搜索引擎（DuckDuckGo、Brave、Yahoo、Bing、Wikipedia、Anna's Archive），或从 18 个图片平台（百度、Bing、Google、Pixabay、Unsplash、火山引擎等）下载图片。提供统一的搜索接口，支持结构化输出格式、结果过滤、排序、自动响应归档和批量图片下载（保留元数据）。
---

# 联合搜索技能

## 目的

提供跨多个平台的统一搜索能力，支持 20+ 个平台的内容搜索和数据获取。所有搜索脚本遵循标准化的输入/输出约定，提供可靠、可读的结果。

## 何时使用此技能

- 跨多个平台搜索内容（GitHub、Reddit、社交媒体、搜索引擎）
- 按时间范围、互动指标或内容类型过滤结果
- 批量搜索/下载并归档原始响应
- 需要无 API 密钥的搜索方案

## 可用的搜索工具

所有脚本位于 `scripts/` 目录，每个模块都有详细的 README 文档。

### 开发者与社区搜索

| 平台 | 描述 | 文档 |
|------|------|------|
| **GitHub** | 仓库、代码、问题/PR搜索 | [GITHUB_README.md](scripts/github/GITHUB_README.md) |
| **Reddit** | 帖子、子版块、用户搜索 | [REDDIT_README.md](scripts/reddit/REDDIT_README.md) |

### 社交媒体与网络搜索

| 平台 | 描述 | 文档 |
|------|------|------|
| **小红书** | 笔记搜索，支持过滤排序 | [XIAOHONGSHU_README.md](scripts/xiaohongshu/XIAOHONGSHU_README.md) |
| **抖音** | 视频搜索，支持过滤选项 | [DOUYIN_README.md](scripts/douyin/DOUYIN_README.md) |
| **Bilibili** | 视频搜索，双API支持 | [BILIBILI_README.md](scripts/bilibili/BILIBILI_README.md) |
| **Twitter** | 帖子和时间线搜索 | [TWITTER_README.md](scripts/twitter/TWITTER_README.md) |
| **YouTube** | 视频、评论搜索 | [YOUTUBE_README.md](scripts/youtube/YOUTUBE_README.md) |
| **微博** | 用户信息和帖子搜索 | [WEIBO_README.md](scripts/weibo/WEIBO_README.md) |
| **知乎** | 中文问答平台 | [ZHIHU_README.md](scripts/zhihu/ZHIHU_README.md) |
| **Google** | Custom Search API | [GOOGLE_SEARCH_README.md](scripts/google_search/GOOGLE_SEARCH_README.md) |
| **Tavily** | AI驱动搜索引擎 | [TAVILY_SEARCH_README.md](scripts/tavily_search/TAVILY_SEARCH_README.md) |
| **秘塔搜索** | AI驱动搜索，智能摘要 | [METASO_README.md](scripts/metaso/METASO_README.md) |
| **火山引擎** | 字节跳动融合信息搜索 | [VOLCENGINE_README.md](scripts/volcengine/VOLCENGINE_README.md) |

**注意**: 火山引擎的图片搜索功能已集成到 union_image_search 模块

### 通用搜索引擎（无需 API 密钥）

| 平台 | 描述 | 文档 |
|------|------|------|
| **DuckDuckGo** | 隐私搜索引擎 | [DUCKDUCKGO_README.md](scripts/duckduckgo/DUCKDUCKGO_README.md) |
| **Brave** | 隐私搜索引擎 | [BRAVE_README.md](scripts/brave/BRAVE_README.md) |
| **Yahoo** | 雅虎搜索引擎 | [YAHOO_README.md](scripts/yahoo/YAHOO_README.md) |
| **Bing** | 微软搜索引擎 | [BING_README.md](scripts/bing/BING_README.md) |
| **Wikipedia** | 百科全书搜索 | [WIKIPEDIA_README.md](scripts/wikipedia/WIKIPEDIA_README.md) |
| **Anna's Archive** | 电子书搜索 | [ANNASARCHIVE_README.md](scripts/annasarchive/ANNASARCHIVE_README.md) |

### 其他搜索工具

| 工具 | 描述 | 文档 |
|------|------|------|
| **联合搜索** | 统一多平台搜索接口 | [UNION_SEARCH_README.md](scripts/union_search/UNION_SEARCH_README.md) |
| **图片搜索** | 18平台批量图片下载 (含火山引擎) | [UNION_IMAGE_SEARCH_README.md](scripts/union_image_search/UNION_IMAGE_SEARCH_README.md) |
| **RSS** | 订阅源内容搜索 | [RSS_SEARCH_README.md](scripts/rss_search/RSS_SEARCH_README.md) |

## 快速开始

### 1. 配置凭据

在项目根目录创建 `.env` 文件（参考 `.env.example`）：

```bash
# 复制模板
cp .env.example .env

# 编辑配置
# 填入必要的 API 凭据
```

**详细配置指南**: 参考 [API 凭据获取指南](references/api_credentials.md)

### 2. 执行搜索

所有脚本支持类似的命令行参数：

```bash
# 联合搜索（推荐）- 同时搜索多个平台
python scripts/union_search/union_search.py "machine learning" --group dev --limit 3

# GitHub 搜索
python scripts/github/github_search.py repo "machine learning" --language python --stars ">1000"

# 小红书搜索
python scripts/xiaohongshu/tikhub_xhs_search.py --keyword "美食" --limit 10

# 图片搜索（无需 API）
python scripts/union_image_search/multi_platform_image_search.py --keyword "cats" --num 50

# DuckDuckGo 搜索（无需 API）
python scripts/duckduckgo/duckduckgo_search.py "Python programming"
```

### 3. 查看结果

- **终端输出**: 格式化的 Markdown 表格
- **原始响应**: 保存在 `responses/` 目录（使用 `--save-raw` 参数）

## 使用工作流

### 标准搜索流程

1. **运行前**: 验证 `.env` 配置存在且包含有效凭据
2. **运行**: 从技能目录直接执行脚本
3. **运行后**: 检查终端输出和 `responses/` 目录中的原始响应文件

### 通用参数

大多数工具支持以下参数：

- `--limit` / `-n`: 返回的结果数量
- `--json`: JSON 格式输出
- `--pretty`: 格式化 JSON 输出
- `--markdown`: Markdown 格式输出
- `-o` / `--output`: 保存输出到文件
- `--save-raw`: 保存原始 API 响应到 `responses/` 目录

### 最佳实践

**结果过滤**:
- 使用 `--limit` 控制输出量
- 应用时间过滤器获取最新内容
- 按互动指标排序以找到热门内容

**响应管理**:
- 永远不要将完整的原始 JSON 粘贴到对话中
- 需要完整数据访问时引用 `responses/` 文件
- 使用 grep/jq 从保存的响应中提取特定字段

**多平台搜索**:
- 为不同平台依次运行脚本
- 使用保存的响应文件比较跨平台结果

## 参考文档

详细的配置、限制和问题排查信息，请参考 `references/` 目录：

- **[API 凭据获取指南](references/api_credentials.md)** - 如何获取各平台的 API 凭据
- **[速率限制说明](references/rate_limits.md)** - 各平台的速率限制和配额信息
- **[平台特定说明](references/platform_notes.md)** - 各平台的特殊说明和注意事项
- **[问题排查指南](references/troubleshooting.md)** - 常见问题的诊断和解决方案
- **[Google 搜索技巧](references/google_search_guide.md)** - Google 搜索高级指令速查

## 常见问题速查

| 问题 | 解决方案 | 详细文档 |
|------|----------|----------|
| 缺少凭据 | 检查 `.env` 文件配置 | [API 凭据](references/api_credentials.md) |
| API 速率限制 | 降低请求频率或限制结果数量 | [速率限制](references/rate_limits.md) |
| 网络超时 | 增加超时值或使用代理 | [问题排查](references/troubleshooting.md) |
| 无效参数 | 查看模块 README 或使用 `--help` | 各模块 README |
| 403 Blocked | 使用代理或降低请求频率 | [问题排查](references/troubleshooting.md) |
| 平台特定问题 | 查看平台说明 | [平台说明](references/platform_notes.md) |

## 项目结构

```
union-search-skill/
├── scripts/                    # 所有搜索脚本
│   ├── union_search/           # 联合搜索（新增）
│   ├── github/                # GitHub 搜索
│   ├── reddit/                # Reddit 搜索
│   ├── xiaohongshu/           # 小红书搜索
│   ├── douyin/                # 抖音搜索
│   ├── bilibili/              # Bilibili 搜索
│   ├── youtube/               # YouTube 搜索
│   ├── weibo/                 # 微博搜索
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
├── references/                 # 参考文档
│   ├── api_credentials.md     # API 凭据获取指南
│   ├── rate_limits.md         # 速率限制说明
│   ├── platform_notes.md      # 平台特定说明
│   ├── troubleshooting.md     # 问题排查指南
│   └── google_search_guide.md # Google 搜索技巧
├── responses/                  # API 响应存档
├── .env.example               # 环境变量模板
├── SKILL.md                   # 本文件
└── README.md                  # 项目说明
```

## 配置优先级

所有工具支持三种配置方式（优先级从高到低）：

1. **命令行参数**: `--token YOUR_TOKEN` 或 `--api-key YOUR_KEY`
2. **环境变量**: 在项目根目录的 `.env` 文件中配置
3. **配置文件**: 工具特定的配置文件（如 GitHub 的 `~/.github-search.json`）

## 获取帮助

- **模块文档**: 每个模块都有详细的 README（`scripts/*/README.md`）
- **参考文档**: 查看 `references/` 目录中的详细指南
- **命令行帮助**: 使用 `--help` 参数查看脚本用法
- **项目 README**: 查看 `README.md` 了解项目概览
