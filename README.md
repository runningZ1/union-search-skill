# Union Search Skill

> 🚀 统一的多平台搜索解决方案 — 一次调用，触达全网

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

---

## 📖 目录

- [快速开始](#-快速开始)
- [支持的平台](#-支持的平台)
- [统一 CLI 命令](#-统一-cli-命令)
- [使用示例](#-使用示例)
- [搜索日志记录](#-搜索日志记录)
- [配置指南](#-配置指南)
- [项目结构](#-项目结构)
- [故障排查](#-故障排查)
- [贡献指南](#-贡献指南)
- [许可证](#-许可证)

---

## 🎯 特性亮点

- **🌐 全网覆盖** — 支持 30+ 搜索平台，涵盖开发者社区、社交媒体、通用搜索引擎
- **⚡ 统一接口** — 单一 CLI 命令调用所有平台，标准化输出格式
- **🔧 灵活配置** — 支持分组搜索、并发控制、结果过滤、多格式输出
- **📦 开箱即用** — 最小依赖设计，按需启用高级功能
- **🛡️ 生产就绪** — 完整的错误处理、速率限制、健康检查
- **🏆 渠道最多** — 与其他开源项目相比，本项目支持最多的搜索渠道和备用方案
- **🔄 自动降级** — 多渠道冗余设计，主渠道失败自动切换备用方案

---

## 💡 为什么选择这个项目？

| 特性 | Union Search | 其他开源项目 |
|------|--------------|--------------|
| 支持平台数量 | **30+** | 通常 1-5 个 |
| 备用渠道 | **✅ 多平台冗余** | ❌ 单一渠道 |
| 统一 CLI | **✅ 标准化接口** | ❌ 各自为政 |
| 图片搜索 | **✅ 18 个平台** | ❌ 少见 |
| 社交媒体 | **✅ 抖音/小红书/B 站** | ❌ 主要面向海外 |
| 全媒介下载 | 🔄 即将支持 | ⚠️ 功能分散 |

**核心优势**：
- **渠道最多**：一个项目解决所有搜索需求，无需在不同项目间切换
- **容错性强**：某个 API 失效时，自动切换到其他可用渠道
- **持续扩展**：不断添加新的搜索渠道和下载功能

---

## 📋 路线图

### 即将上线

| 功能 | 描述 | 状态 |
|------|------|------|
| **全媒介下载工具** | 支持抖音视频、小红书图文、B 站视频、YouTube 视频等平台的完整内容下载 | 🔄 开发中 |
| **更多搜索渠道** | 添加 Wikipedia 镜像、学术搜索（Google Scholar、Semantic Scholar） | 📝 计划中 |
| **渠道自动切换** | 主渠道失败时无缝切换到备用渠道 | 📝 计划中 |
| **结果缓存** | 减少重复请求，节省 API 配额 | 📝 计划中 |

---

## ⚠️ 安装提示

> 本项目文件较大（约 100MB+），**Claude Code Core Hub 对 Skill/Agent 有 50MB 的大小限制**。因此：
> - ❌ 通过 Core Hub 安装的版本会**缺失部分文件**（大文件会被忽略）
> - ✅ **推荐直接从 GitHub 仓库下载完整版本**：https://github.com/anyangrc/union-search-skill
> - GitHub 仓库包含完整的依赖文件、脚本和文档，是最完整的安装方式

---

## 🚀 快速开始

### 1. 安装依赖

```bash
# 基础依赖（所有搜索功能）
pip install requests python-dotenv lxml

# 图片搜索（可选）
pip install pyimagedl

# Bilibili 搜索（可选）
pip install curl_cffi

# Tavily 搜索（可选）
pip install tavily-python

# RSS 订阅搜索（可选）
pip install feedparser

> ⚠️ **RSS 模块为测试和实验性质**：RSS 源依赖第三方服务（如 Kindle4RSS、wechat2rss 等），可能不是实时有效的，部分源可能返回 0 条内容或解析失败，这是第三方服务的限制，非本工具的问题。
```

### 2. 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件，填入 API 密钥
```

### 3. 运行第一个搜索

```bash
# 统一搜索（开发者相关平台）
python union_search_cli.py search "AI Agent" --group dev --limit 3 --pretty

# 或直接调用单个平台
python union_search_cli.py google "Python tutorial" --limit 5
```

---

## 🌍 支持的平台

### 开发者搜索

| 引擎 | 类型 | 速率限制 | 状态 |
|------|------|----------|------|
| **GitHub** | 仓库/代码/Issues/PRs 搜索 | - | ✅ 稳定 |
| **Reddit** | 帖子/子版块/用户搜索 | - | ✅ 稳定 |
| **Zhihu** | 知乎问答搜索 | - | ✅ 稳定 |

### 社交媒体与视频

| 引擎 | 类型 | 速率限制 | 状态 |
|------|------|----------|------|
| **Xiaohongshu (小红书)** | 笔记搜索 | - | ✅ 稳定 |
| **Douyin (抖音)** | 视频搜索 | - | ✅ 稳定 |
| **Bilibili** | 视频/UP 主搜索 | - | ✅ 稳定 |
| **Twitter / X** | 推文搜索 | - | ✅ 稳定 |
| **YouTube** | 视频/评论搜索 | - | ✅ 稳定 |
| **WeChat (微信)** | 公众号搜索 | - | ✅ 稳定 |
| **Toutiao (今日头条)** | 文章搜索 | - | ✅ 稳定 |
| **Weibo (微博)** | 微博搜索 | - | ⚠️ 需要 Cookie |

### 通用搜索引擎

| 平台 | API 密钥 | 状态 |
|------|---------|------|
| **Google** | 需要 | ✅ 稳定 |
| **Bing** | 需要 | ✅ 稳定 |
| **DuckDuckGo** | 无需 | ✅ 稳定 |
| **Brave** | 无需 | ✅ 稳定 |
| **Yahoo** | 无需 | ✅ 稳定 |
| **Baidu** | 需要 | ✅ 稳定 |
| **Yandex** | 无需 | ✅ 稳定 |
| **百度（无API）** | 无需 | ✅ 稳定 |
| **必应中国（无API）** | 无需 | ✅ 稳定 |
| **必应国际（无API）** | 无需 | ✅ 稳定 |
| **搜狗（无API）** | 无需 | ✅ 稳定 |
| **360（无API）** | 无需 | ✅ 稳定 |
| **Startpage（无API）** | 无需 | ✅ 稳定 |
| **Ecosia（无API）** | 无需 | ✅ 稳定 |
| **Qwant（无API）** | 无需 | ✅ 稳定 |
| **Wolfram Alpha（无API）** | 无需 | ✅ 稳定 |

### AI 驱动搜索

| 平台 | 特性 | 状态 |
|------|------|------|
| **Tavily** | AI 摘要/智能搜索 | ✅ 稳定 |
| **Metaso (秘塔)** | AI 生成答案 | ✅ 稳定 |
| **Volcengine (火山)** | 融合搜索+AI 摘要 | ⚠️ 偶发解析问题 |
| **Jina** | 内容提取 | ✅ 稳定 |

### 网页转Markdown

| 引擎 | 类型 | 速率限制 | 状态 |
|------|------|----------|------|
| **Jina Reader** | URL转Markdown/提取网页内容 | - | ✅ 稳定 |

> 💡 **Jina Reader** 是免费的HTTP API，无需API Key即可使用（每分钟20次请求），可将任意URL转换为LLM友好的Markdown内容。

### 图片搜索（18 个平台）

- **搜索引擎**: 百度、Bing、Google、360、搜狗、DuckDuckGo、Yandex、Yahoo
- **图库网站**: Pixabay、Pexels、Unsplash、Foodiesfeed
- **动漫图片**: Danbooru、Gelbooru、Safebooru
- **其他**: 花瓣网、次元小镇、火山引擎

### 内容订阅

| 类型 | 功能 | 状态 |
|------|------|------|
| **RSS** | 多源聚合/关键词过滤 | ✅ 稳定 |
| **小宇宙 FM** | 播客搜索/AI 摘要 | ✅ 稳定 |

---

## 📊 实测数据

> 基于 2026-03-05 真实搜索测试，关键词: `AI agent`

### 搜索引擎组 (search) 实测

| 平台 | 默认结果数 | 响应时间 | 状态 |
|------|-----------|----------|------|
| metaso | 10 | 1.00s | ✅ |
| baidu | 10 | 1.60s | ✅ |
| yandex | 10 | 2.15s | ✅ |
| bing | 3 | 2.22s | ✅ |
| wikipedia | 10 | 2.34s | ✅ |
| google | 10 | 2.95s | ✅ |
| tavily | 5 | 3.19s | ✅ |
| brave | 10 | 3.20s | ✅ |
| duckduckgo | 6 | 3.58s | ✅ |
| jina | 10 | 3.68s | ✅ |
| yahoo | 7 | 2.62s | ✅ |
| volcengine | 10 | 6.45s | ✅ |

### 汇总统计

| 指标 | 数值 |
|------|------|
| **搜索平台数** | 12 |
| **成功平台** | 12/12 (100%) |
| **总耗时** | 11.14 秒 |
| **总结果数** | 91 条 |
| **平均每平台** | 7.6 条 |
| **最快响应** | metaso (1.00s) |

### 去重后预估

- 搜索引擎结果存在一定重叠（约 20-30%）
- **去重后预估有效结果**: 约 65-70 条
- **信息覆盖度**: 远超单一搜索引擎

### 各平台默认返回数量

| 平台 | 默认值 | 限制原因 |
|------|--------|----------|
| google | 10 | Custom Search API 限制 |
| tavily | 5 | API 默认设置 |
| jina | 10 | API 默认设置 |
| duckduckgo | 6 | 非 API，结果不稳定 |
| brave | 10 | 非 API |
| yahoo | 7 | 非 API |
| yandex | 10 | SerpAPI |
| bing | 3 | SerpAPI 免费限制 |
| wikipedia | 10 | API 默认设置 |
| metaso | 10 | API 默认设置 |
| volcengine | 10 | API 默认设置 |
| baidu | 10 | API 默认设置 |

> 💡 **提示**: 使用 `--limit` 参数可自定义每平台返回数量

---

## 🖥️ 统一 CLI 命令

### 命令总览

```bash
python union_search_cli.py --help
```

| 命令 | 描述 |
|------|------|
| `search` | 多平台聚合搜索 |
| `platform <name>` | 单平台搜索 |
| `image` | 图片搜索与下载 |
| `download` | 基于 yt-dlp 下载视频/音频 |
| `list` | 列出可用平台/分组 |
| `doctor` | 健康检查 |
| `<platform>` | 平台直达命令（如 `google`、`bing`） |

### 全局选项

| 选项 | 简写 | 描述 |
|------|------|------|
| `--format <type>` | - | 输出格式：`json` / `markdown` / `text` |
| `--pretty` | - | 美化 JSON 输出 |
| `--output <file>` | `-o` | 输出到文件 |
| `--env-file <path>` | - | 环境变量文件路径 |

---

## 🔢 返回数量控制

### 预设档位

使用 `--preset` 参数快速设置返回数量：

| 预设 | 数量 | 适用场景 |
|------|------|----------|
| `small` | 5 条 | 快速预览、节省 Token |
| `medium` | 10 条 | 日常搜索（默认） |
| `large` | 20 条 | 深度研究 |
| `max` | 全量 | 数据采集 |

### 自定义数量

| 参数 | 描述 |
|------|------|
| `--limit <N>` | 自定义返回数量（覆盖 preset） |
| `--limit 0` | 全量返回（不限制） |

### 环境变量

```bash
# .env 文件
SEARCH_DEFAULT_LIMIT=10      # 默认返回数量
SEARCH_LIMIT_PRESET=medium   # 预设档位
```

---

## 📚 使用示例

### 多平台聚合搜索

```bash
# 搜索开发者相关内容
python union_search_cli.py search "machine learning" --group dev --limit 5

# 搜索社交媒体内容
python union_search_cli.py search "AI trends" --group social --limit 3

# 指定多个平台
python union_search_cli.py search "Python" --platforms github google tavily --limit 5

# 导出可下载候选（search 结果内含 download_candidates）
python union_search_cli.py search "AI agent" --platforms youtube bilibili --limit 3 -o ./out/search.json --pretty

# 带并发和超时控制
python union_search_cli.py search "Rust" --max-workers 10 --timeout 120

# 使用预设档位（推荐）
python union_search_cli.py search "AI" --preset small    # 快速预览（5 条）
python union_search_cli.py search "AI" --preset medium  # 标准搜索（10 条）
python union_search_cli.py search "AI" --preset large   # 深度研究（20 条）
python union_search_cli.py search "AI" --preset max     # 全量返回
```

### 单平台搜索

```bash
# GitHub 搜索
python union_search_cli.py platform github "awesome python" --limit 10

# 或使用直达命令
python union_search_cli.py github "machine learning" --limit 5
python union_search_cli.py bing "AI news" --limit 10
python union_search_cli.py bsearch "deep learning" --limit 10  # 使用别名
```

### 视频/音频下载（yt-dlp）

```bash
# 直接下载 URL
python union_search_cli.py download "https://www.youtube.com/watch?v=dQw4w9WgXcQ" --output-dir ./downloads

# 限制分辨率并提取音频
python union_search_cli.py download "https://www.bilibili.com/video/BV1xx411c7mD" --max-height 1080
python union_search_cli.py download "https://www.youtube.com/watch?v=dQw4w9WgXcQ" --audio-only --audio-format mp3

# 从搜索结果文件筛选后下载
python union_search_cli.py download --from-file ./out/search.json --platforms youtube bilibili --select 1,2,3 --output-dir ./downloads

# YouTube 403 推荐：使用 cookies 文件
python union_search_cli.py download "https://youtu.be/Zh9IscszDQg" --cookies-file C:/path/cookies.txt --restrict-filenames --continue-download --output-dir ./downloads
```

> 提示：`search` 输出中的 `download_candidates` 字段提供稳定索引，可直接传给 `download --select`。
> 提示：`download` 对 YouTube 会优先尝试 cookies（显式 `--cookies-file` 或环境变量 `YTDLP_COOKIES_FILE`）。

### 图片搜索与下载

```bash
# 搜索并下载图片
python union_search_cli.py image "cute cats" \
  --platforms google bing pixabay \
  --limit 20 \
  --output-dir ./cat_images

# 自定义下载线程数
python union_search_cli.py image "landscape" --threads 10 --limit 50
```

### 列出能力

```bash
# 列出所有平台和分组
python union_search_cli.py list --format markdown

# 只看图片平台
python union_search_cli.py list --type images
```

### 健康检查

```bash
# 检查环境配置
python union_search_cli.py doctor --env-file .env

# 严格模式（警告也返回非零）
python union_search_cli.py doctor --strict
```

### 网页转Markdown

```bash
# 将URL转换为Markdown（命令行直接调用）
python scripts/url_to_markdown/url_to_markdown.py "https://example.com"

# JSON格式输出
python scripts/url_to_markdown/url_to_markdown.py "https://example.com" --json

# 包含图片摘要
python scripts/url_to_markdown/url_to_markdown.py "https://example.com" --with-images

# 绕过缓存（获取最新内容）
python scripts/url_to_markdown/url_to_markdown.py "https://example.com" --no-cache

# Python API调用
python -c "from scripts.url_to_markdown import fetch_url_as_markdown; print(fetch_url_as_markdown('https://example.com'))"
```

> 💡 **速率限制**: Jina Reader API 免费使用，无需API Key，每分钟最多20次请求。如需更高限额，可注册获取免费API Key（500 RPM）。

---

## 📝 搜索日志记录

每次搜索请求的日志和结果会自动保存到 `search_logs/` 目录，文件格式为 JSON，包含完整的请求信息和搜索结果。

### 日志文件格式

```json
{
  "version": "1.0.0",
  "timestamp": "2026-03-05T21:38:28.502062",
  "request": {
    "query": "Python教程",
    "platforms": ["search"],
    "total_results": 24
  },
  "results": [
    {
      "title": "9. Classes — Python 3.14.3 documentation",
      "link": "https://docs.python.org/3/tutorial/classes.html",
      "source": "google",
      "snippet": "Classes provide a means of bundling data and functionality together..."
    }
    // ... 更多结果
  ],
  "statistics": {
    "total_count": 24,
    "platform_counts": {
      "google": 2,
      "tavily": 2,
      "jina": 2,
      // ...
    }
  },
  "metadata": {
    "response_time": 6.5,
    "status": "success"
  }
}
```

### 使用日志模块

```python
from scripts.search_logger import SearchLogger

# 创建日志记录器
logger = SearchLogger()

# 记录搜索结果
logger.log(
    query="Python教程",
    platforms=["search"],
    results=[...],  # 搜索结果列表
    metadata={"response_time": 2.5, "status": "success"}
)
```

### 示例响应文件

项目包含一个示例响应文件，展示完整的日志格式：

- `search_logs/example_python_tutorial_search.json` - Python教程搜索示例

> **注意**: `search_logs/` 目录已被添加到 `.gitignore`，本地日志不会提交到远程仓库。

---

## 🔧 配置指南

### 环境变量参考

| 变量名 | 平台 | 获取地址 | 备注 |
|--------|------|----------|------|
| `GITHUB_TOKEN` | GitHub | [GitHub Settings](https://github.com/settings/tokens) | 公共搜索无需权限 |
| `TIKHUB_TOKEN` | 小红书/抖音/Twitter | [TikHub](https://www.tikhub.io) | 💰 $5 约 5000 次调用 |
| `SERPAPI_KEY` | Google/Bing (SerpAPI) | [SerpAPI](https://serpapi.com) | ⚠️ 免费 250 次/月，需手机号注册 |
| `GOOGLE_API_KEY` | Google | [Google Cloud Console](https://console.cloud.google.com) | 官方 API 替代方案 |
| `GOOGLE_SEARCH_ENGINE_ID` | Google | [Programmable Search Engine](https://programmablesearchengine.google.com) | 需与 API Key 配合使用 |
| `YOUTUBE_API_KEY` | YouTube | [Google Cloud Console](https://console.cloud.google.com) | 10000 单位/天 |
| `TAVILY_API_KEY` | Tavily | [Tavily Dashboard](https://tavily.com) | 免费 1000 积分/月 |
| `METASO_API_KEY` | 秘塔搜索 | [Metaso](https://metaso.cn) | AI 生成答案 |
| `VOLCENGINE_API_KEY` | 火山引擎 | [火山引擎控制台](https://console.volcengine.com) | 字节官方 API |
| `ZHIHU_COOKIE` | 知乎 | 浏览器开发者工具 | 手动获取 |
| `WEIBO_COOKIE` | 微博 | 浏览器开发者工具 | 手动获取 |

> 💡 **API 成本提示**：
> - **SerpAPI** 免费账户每月仅 250 次请求，注册需要手机号验证。适合测试和低频使用。
> - **TikHub** 5 美元充值约可使用 5000 次（取决于具体平台和参数），正常使用足够。
> - 建议优先使用 **无需 API 密钥** 的引擎（DuckDuckGo、Brave、Yahoo 等）作为日常搜索。
> - 生产环境建议配置多个渠道，自动降级切换。

### 平台分组

```bash
# 查看可用分组
python union_search_cli.py list --type groups
```

| 分组 | 包含平台 |
|------|----------|
| `dev` | GitHub, Reddit, Zhihu |
| `social` | 小红书，抖音，Twitter, Weibo, 微信, 今日头条 |
| `video` | Bilibili, YouTube |
| `search` | Google, Bing, DuckDuckGo, Brave, Yahoo |
| `ai` | Tavily, Metaso, Volcengine, Jina |
| `no_api_key` | 百度, 必应中国, 必应国际, 搜狗, 360, 微信, 今日头条, 集思录, Google, Google香港, DuckDuckGo, Startpage, Brave, Yahoo, Ecosia, Qwant, Wolfram Alpha |

---

## 📁 项目结构

```
union-search-skill/
├── union_search_cli.py      # 统一 CLI 入口
├── _meta.json              # Skill 元数据文件
├── scripts/
│   ├── cli/                 # CLI 核心模块
│   │   ├── main.py          # CLI 主程序
│   │   ├── adapters.py      # 平台适配器
│   │   ├── registry.py      # 平台注册表
│   │   └── validators.py    # 参数验证
│   ├── union_search/        # 统一搜索编排器
│   ├── github/              # GitHub 搜索
│   ├── reddit/              # Reddit 搜索
│   ├── xiaohongshu/         # 小红书搜索
│   ├── douyin/              # 抖音搜索
│   ├── bilibili/            # Bilibili 搜索
│   ├── twitter/             # Twitter 搜索
│   ├── youtube/             # YouTube 搜索
│   ├── google_search/       # Google 搜索 (含无API版本)
│   ├── bing/                # Bing 搜索 (含无API版本)
│   ├── baidu/               # 百度搜索 (含无API版本)
│   ├── duckduckgo/          # DuckDuckGo 搜索 (含无API版本)
│   ├── brave/               # Brave 搜索 (含无API版本)
│   ├── yahoo/               # Yahoo 搜索 (含无API版本)
│   ├── sogou/               # 搜狗搜索 (无API版本)
│   ├── so360/               # 360搜索 (无API版本)
│   ├── wechat/              # 微信搜索 (无API版本)
│   ├── toutiao/             # 今日头条搜索 (无API版本)
│   ├── jisilu/              # 集思录搜索 (无API版本)
│   ├── startpage/           # Startpage 搜索 (无API版本)
│   ├── ecosia/              # Ecosia 搜索 (无API版本)
│   ├── qwant/               # Qwant 搜索 (无API版本)
│   ├── wolfram/             # Wolfram Alpha 搜索 (无API版本)
│   ├── wikipedia/           # Wikipedia 搜索
│   ├── tavily_search/       # Tavily 搜索
│   ├── metaso/              # 秘塔搜索
│   ├── volcengine/          # 火山引擎搜索
│   ├── zhihu/               # 知乎搜索
│   ├── union_image_search/  # 图片搜索
│   ├── rss_search/          # RSS 订阅搜索
│   ├── xiaoyuzhoufm/        # 小宇宙 FM 播客
│   ├── url_to_markdown/     # 网页转Markdown
│   ├── jina/                # Jina 搜索
│   └── exa_search/          # Exa 神经搜索
├── references/              # 参考文档
├── responses/               # API 响应存档
├── search_logs/             # 搜索日志（本地记录，不提交到远程）
│   └── example_*.json      # 示例响应文件
├── scripts/
│   └── search_logger.py    # 日志记录模块
├── .env.example             # 环境变量模板
└── README.md                # 项目文档
```

---

## 🐛 故障排查

### 常见问题

#### 1. 平台返回 403 错误

**原因**: API 密钥无效或请求频率过高

**解决方案**:
```bash
# 检查 API 密钥配置
python union_search_cli.py doctor --platforms github google

# 降低并发数
python union_search_cli.py search "query" --max-workers 2
```

#### 2. 图片下载失败

**原因**: 缺少 `pyimagedl` 依赖

**解决方案**:
```bash
pip install pyimagedl
```

#### 3. 火山引擎解析错误

**状态**: 已知问题，修复中

**临时方案**: 使用其他 AI 搜索平台替代
```bash
python union_search_cli.py search "query" --platforms tavily metaso
```

### 获取帮助

- 📖 查看 [参考文档](references/)
- 🔍 搜索 [历史问题](responses/)
- 💬 提交 Issue

---

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

---

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

---

## 🙏 致谢

感谢以下开源项目和 API 服务：

- [requests](https://github.com/psf/requests) - Python HTTP 库
- [lxml](https://lxml.de/) - XML/HTML 解析
- [TikHub](https://www.tikhub.io) - 社交媒体 API
- [Tavily](https://tavily.com) - AI 搜索引擎
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - 视频下载工具

---

<div align="center">

**Made with ❤️ by the Union Search Team**

[⬆ 返回顶部](#union-search-skill)

</div>
