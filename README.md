# Union Search Skill

统一搜索技能 - 跨平台搜索解决方案

## 概述

提供跨多个平台的统一搜索能力，包括：

1. **开发者搜索**: GitHub 仓库、代码、Issues/PRs
2. **社交媒体与网络搜索**: 小红书、抖音、Bilibili、Twitter、Google
3. **图片搜索与下载**: 17 个图片平台（百度、Bing、Google、Pixabay、Unsplash 等）

## 支持的平台

### 开发者搜索 (NEW)
- **GitHub** - 搜索仓库、代码、Issues/PRs，支持高级筛选

### 社交媒体与网络搜索
- **Xiaohongshu (小红书)** - 搜索笔记，支持筛选和排序
- **Douyin (抖音)** - 搜索视频，支持综合筛选
- **Bilibili** - 搜索视频和内容
- **Twitter** - 搜索推文和时间线
- **Google** - 使用自定义搜索 API 进行网络搜索

### 图片搜索与下载（17 个平台）
- **搜索引擎**: 百度、Bing、Google、360、搜狗、DuckDuckGo、Yandex、Yahoo
- **图库网站**: Pixabay、Pexels、Unsplash、Foodiesfeed
- **动漫图片**: Danbooru、Gelbooru、Safebooru
- **其他**: 花瓣网、次元小镇

## 快速开始

### 1. 安装依赖

```bash
# 基础依赖（所有脚本共用）
pip install requests

# 图片搜索（可选）
pip install pyimagedl
```

### 2. 配置凭证

**GitHub 搜索（推荐方式）：**
```bash
# 一次性配置
python scripts/github_search.py config --token YOUR_GITHUB_TOKEN

# 获取 token: https://github.com/settings/tokens
# 公共搜索无需特殊权限
```

**社交媒体搜索：**
```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件，填入 API 凭证
# - TIKHUB_TOKEN: TikHub API token
# - GOOGLE_API_KEY: Google API key
# - GOOGLE_SEARCH_ENGINE_ID: Google Search Engine ID
```

### 3. 使用示例

**GitHub 搜索：**
```bash
python scripts/github_search.py repo "machine learning" --language python --stars ">1000"
```

**小红书搜索：**
```bash
python scripts/tikhub_xhs_search.py --keyword "美食" --limit 10
```

**图片搜索：**
```bash
python scripts/multi_platform_image_search.py --keyword "cute cats" --num 50
```

## 功能特性

### GitHub 搜索 (NEW)
- ✅ 搜索仓库（按语言、星标、主题等筛选）
- ✅ 搜索代码（跨所有公共仓库）
- ✅ 搜索 Issues 和 Pull Requests
- ✅ 速率限制检查
- ✅ 多种输出格式（文本、JSON、Markdown）
- ✅ 配置文件支持
- ✅ 最小依赖（仅需 requests）

### 社交媒体搜索
- 小红书：按时间、内容类型、互动指标筛选
- 抖音：高级筛选（时长、内容类型）
- Bilibili：视频搜索
- Twitter：推文和时间线搜索
- Google：自定义搜索引擎

### 图片搜索
- 17 个平台同时搜索
- 自动元数据保存
- 进度跟踪和摘要报告
- 按平台组织输出

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

# 输出格式
python scripts/github_search.py repo "react" --format json --pretty
python scripts/github_search.py repo "vue" --format markdown -o results.md
```

### 小红书搜索

```bash
python scripts/tikhub_xhs_search.py --keyword "美食" --limit 10 --sort-field likes --sort-order desc
```

### 抖音搜索

```bash
python scripts/tikhub_douyin_search.py --keyword "旅游" --limit 10
```

### Google 搜索

```bash
python scripts/official_google_search.py --query "AI agent" --num 10
```

### 多平台图片搜索

```bash
# 搜索所有平台
python scripts/multi_platform_image_search.py --keyword "cute cats" --num 50

# 搜索指定平台
python scripts/multi_platform_image_search.py --keyword "sunset" --platforms baidu google pixabay --num 30

# 自定义输出目录
python scripts/multi_platform_image_search.py --keyword "flowers" --output ./my_images --num 100
```

## 项目结构

```
union-search-skill/
├── scripts/
│   ├── github_search.py              # GitHub 搜索（独立脚本）
│   ├── multi_platform_image_search.py # 多平台图片搜索
│   ├── tikhub_xhs_search.py          # 小红书搜索
│   ├── tikhub_douyin_search.py       # 抖音搜索
│   ├── tikhub_bili_search.py         # Bilibili 搜索
│   ├── tikhub_twitter_search.py      # Twitter 搜索
│   └── official_google_search.py     # Google 搜索
├── responses/                         # API 响应存档
├── .env.example                       # 环境变量模板
├── SKILL.md                          # 完整技能文档
└── README.md                         # 本文件
```

## 配置优先级

### GitHub Token
1. `--token` 命令行选项（最高优先级）
2. `GITHUB_TOKEN` 环境变量
3. 配置文件 `~/.github-search.json`

### 其他平台
1. 命令行参数（最高优先级）
2. `.env` 文件配置

## 速率限制

### GitHub API
- **已认证**: 30 次搜索/分钟，5000 次核心请求/小时
- **未认证**: 10 次搜索/分钟，60 次核心请求/小时

### 其他平台
请参考各平台 API 文档

## 常见问题

### GitHub 搜索

**Q: 如何获取 GitHub token？**
A: 访问 https://github.com/settings/tokens，点击 "Generate new token (classic)"，公共搜索无需特殊权限。

**Q: Token 存储在哪里？**
A: 配置文件位于 `~/.github-search.json`，权限设置为 0600（仅所有者可读写）。

**Q: 如何检查速率限制？**
A: 运行 `python scripts/github_search.py rate-limit`

### 社交媒体搜索

**Q: 缺少凭证错误？**
A: 检查 `.env` 文件配置

**Q: API 速率限制？**
A: 减少请求频率或限制结果数量

**Q: 网络超时？**
A: 增加 `.env` 中的 `TIKHUB_TIMEOUT` 值

## 迁移说明

### 从 github-search-skill 迁移

原 `github-search-skill` 技能已集成到此技能中：

- ✅ 所有核心功能已迁移
- ✅ 独立脚本，无需安装包
- ✅ 与现有脚本风格一致
- ✅ 可以安全删除原技能

**迁移步骤：**
1. 使用新脚本：`python scripts/github_search.py`
2. 重新配置 token（如果需要）
3. 删除原技能目录（可选）

## 更新日志

### v2.0.0 (2026-01-31)
- ✨ 新增 GitHub 搜索功能
- ✨ 独立的 `github_search.py` 脚本
- 📝 更新文档，添加 GitHub 搜索说明
- 🔧 优化配置管理

### v1.0.0
- 初始版本
- 支持小红书、抖音、Bilibili、Twitter、Google 搜索
- 支持 17 个平台的图片搜索

## 许可证

MIT License


### Social Media & Web Search
- **Unified interface** - Consistent command-line arguments across platforms
- **Structured output** - Markdown-formatted, human-readable results
- **Response archiving** - Automatic saving of raw API responses
- **Flexible filtering** - Time range, content type, engagement metrics
- **Sorting options** - Sort by likes, comments, shares, publish time
- **Result limiting** - Control output volume with `--limit` parameter

### Image Search & Download
- **Multi-platform batch search** - Search 17 platforms simultaneously or selectively
- **Organized storage** - Each platform gets its own timestamped subfolder
- **Metadata preservation** - Save complete image metadata in JSON format
- **Progress tracking** - Real-time progress display and summary reports
- **Fully standalone** - Only requires `pip install pyimagedl`
- **Flexible configuration** - Command-line and Python API support

## Directory Structure

```
union-search-skill/
├── SKILL.md              # Skill instructions for Claude
├── README.md             # This file
├── .env.example          # Configuration template
├── .env                  # Your credentials (not tracked)
├── scripts/              # Search scripts
│   ├── tikhub_xhs_search.py
│   ├── tikhub_douyin_search.py
│   ├── tikhub_bili_search.py
│   ├── tikhub_twitter_search.py
│   └── official_google_search.py
└── responses/            # Archived API responses
```

## Usage Examples

### Social Media Search

#### Xiaohongshu Search
```bash
python scripts/tikhub_xhs_search.py --keyword "旅游" --limit 10 --sort-field likes
```

#### Douyin Search
```bash
python scripts/tikhub_douyin_search.py --keyword "美食" --limit 10
```

#### Google Search
```bash
python scripts/official_google_search.py --query "python tutorial" --num 10
```

### Image Search & Download

#### Search All Platforms
```bash
python scripts/multi_platform_image_search.py --keyword "cute cats" --num 50
```

#### Search Specific Platforms
```bash
python scripts/multi_platform_image_search.py --keyword "sunset" --platforms baidu google pixabay --num 30
```

#### List All Supported Platforms
```bash
python scripts/multi_platform_image_search.py --list-platforms
```

For detailed usage, see the Multi-Platform Image Search section in [SKILL.md](SKILL.md)

## Output

- **Terminal**: Formatted Markdown with essential information
- **Files**: Raw JSON responses saved to `responses/` directory

## Requirements

### Social Media & Web Search
- Python 3.6+
- Standard library only (no external dependencies)
- Valid API credentials (TikHub, Google Custom Search)

### Image Search & Download
- Python 3.6+
- `pyimagedl` package: `pip install pyimagedl`
- Internet connection (some platforms may require proxy)

## License

This skill is provided as-is for use with Claude Code.
