---
name: union-search-skill
description: This skill should be used when users need to search content across multiple platforms including GitHub (repositories, code, issues), Reddit (posts, subreddits, users), Xiaohongshu (小红书), Douyin (抖音), Bilibili, Twitter, Google, or download images from 17 image platforms (Baidu, Bing, Google, Pixabay, Unsplash, etc.). It provides unified search interfaces with structured output formatting, result filtering, sorting, automatic response archiving, and batch image downloading with metadata preservation.
---

# Union Search Skill

## Purpose

Provide unified search capabilities across multiple platforms with five main categories:

1. **Developer & Community Search**: GitHub repositories, code, issues/PRs, Reddit posts and discussions
2. **Social Media & Web Search**: Xiaohongshu, Douyin, Bilibili, Twitter, Google
3. **Image Search & Download**: 17 image platforms including Baidu, Bing, Google, Pixabay, Unsplash, Pexels, and more
4. **RSS Feed Search**: Search and monitor content from RSS feeds with keyword filtering
5. **Reddit Search**: Search Reddit posts, subreddits, users, and retrieve detailed post information with comments

All search scripts follow standardized input/output conventions for reliable, readable results with consistent output formatting, result filtering, and automatic response archiving.

## When to Use This Skill

Use this skill when users request:
- Searching GitHub repositories, code snippets, or issues/pull requests
- Finding open source projects, libraries, or code examples
- Discovering trending repositories or good first issues
- Searching Reddit posts, subreddits, users, or retrieving post details with comments
- Finding discussions, questions, or community content on Reddit
- Searching content on Xiaohongshu (小红书), Douyin (抖音), Bilibili, Twitter, or Google
- Downloading images from multiple image platforms (Baidu, Bing, Google Images, Pixabay, Unsplash, etc.)
- Searching and monitoring RSS feeds with keyword filtering
- Filtering search results by time range, engagement metrics, or content type
- Sorting results by stars, likes, comments, shares, or other metrics
- Batch searching/downloading across multiple platforms
- Archiving raw API responses or image metadata for later analysis

## Available Search Scripts

All scripts are located in the `scripts/` directory:

### 0. GitHub Search (`scripts/github_search.py`)
**NEW** - Search GitHub repositories, code, and issues/pull requests with comprehensive filtering.

**Key features:**
- Search repositories by language, stars, topics, license, etc.
- Search code across all public repositories
- Search issues and pull requests with filters
- Check API rate limits
- Configuration file support (`~/.github-search.json`)
- Multiple output formats: text, JSON, Markdown
- Minimal dependencies (only requires `requests`)

**Installation:**
```bash
pip install requests
```

**First-time setup:**
```bash
# Configure GitHub token (one-time setup)
python scripts/github_search.py config --token YOUR_GITHUB_TOKEN

# Get token at: https://github.com/settings/tokens
# No special scopes needed for public search
```

**Usage examples:**

```bash
# Repository search
python scripts/github_search.py repo "machine learning" --language python --stars ">1000"
python scripts/github_search.py repo "web framework" --sort stars --limit 10

# Code search
python scripts/github_search.py code "def main" --language python --limit 20
python scripts/github_search.py code "OAuth2" --repo "flask" --extension py

# Issue/PR search
python scripts/github_search.py issue "bug" --state open --label "help wanted"
python scripts/github_search.py issue "feature" --is-pr --author "username"

# Rate limit check
python scripts/github_search.py rate-limit

# Output formats
python scripts/github_search.py repo "react" --format json --pretty
python scripts/github_search.py repo "vue" --format markdown -o results.md
```

**Repository search filters:**
- `--language`: Programming language (e.g., python, javascript)
- `--stars`: Star count (e.g., ">1000", "100..500")
- `--forks`: Fork count
- `--user`: User or organization
- `--topic`: Repository topic
- `--license`: License type (e.g., mit, apache-2.0)
- `--created`: Created date (e.g., ">2024-01-01")
- `--pushed`: Last pushed date
- `--archived`: Archived status (true/false)
- `--sort`: Sort by stars, forks, help-wanted-issues, updated
- `--order`: Sort order (asc/desc)

**Code search filters:**
- `--language`: Programming language
- `--repo`: Repository (owner/name)
- `--path`: File path
- `--extension`: File extension

**Issue/PR search filters:**
- `--state`: open or closed
- `--is-pr`: Only pull requests
- `--is-issue`: Only issues
- `--author`: Issue author
- `--assignee`: Assignee
- `--label`: Label
- `--milestone`: Milestone
- `--repo`: Repository (owner/name)

**Configuration:**
Token priority (highest to lowest):
1. `--token` command line option
2. `GITHUB_TOKEN` environment variable
3. Configuration file (`~/.github-search.json`)

**Rate limits:**
- Authenticated: 30 searches/minute, 5000 core requests/hour
- Unauthenticated: 10 searches/minute, 60 core requests/hour

### 1. Reddit Search (`scripts/reddit_search.py`)
**NEW** - Search Reddit posts, subreddits, users, and retrieve detailed information.

**Key features:**
- Global Reddit search across all subreddits
- Subreddit-specific search
- Post details with optional comment tree extraction
- User activity history (posts and comments)
- Subreddit posts by category (hot, top, new, rising)
- No API key required (uses public JSON endpoints)
- Multiple output formats: text, JSON, Markdown
- Automatic retry and rate limiting protection
- Minimal dependencies (only requires `requests`)

**Installation:**
```bash
pip install requests
```

**Usage examples:**

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

**Commands:**

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

**Common parameters:**
- `--format`: 输出格式（text, json, markdown，默认: text）
- `--pretty`: 格式化 JSON 输出
- `-o, --output`: 保存输出到文件
- `--save-raw`: 保存原始响应到 responses/ 目录
- `--verbose`: 详细日志输出

**Output information:**
默认输出包含：
- 帖子标题
- 作者和子版块
- 评分（score）和点赞率（upvote_ratio）
- 评论数量（num_comments）
- 帖子链接
- 视频/NSFW 标记（如果适用）

使用 `--include-comments` 时会额外获取完整的评论树结构。

**Rate limiting:**
- 自动随机延迟 1-2 秒防止限流
- 自动重试机制（5次重试，指数退避）
- 无需 API 密钥，使用 Reddit 公开 JSON 端点

### 2. Multi-Platform Image Search (`scripts/image_search/multi_platform_image_search.py`)
**NEW** - Search and download images from 17 platforms simultaneously.

**Supported platforms:**
- Search engines: Baidu, Bing, Google, 360, Sogou, DuckDuckGo, Yandex, Yahoo
- Stock photos: Pixabay, Pexels, Unsplash, Foodiesfeed
- Anime images: Danbooru, Gelbooru, Safebooru
- Others: Huaban (花瓣网), DimTown (次元小镇)

**Key features:**
- Batch search across all 17 platforms or selected platforms
- Organized output: each platform gets its own subfolder
- Automatic metadata saving (JSON format)
- Progress tracking and summary reports (JSON + Markdown)
- Fully standalone (only requires `pip install pyimagedl`)

**Installation:**
```bash
pip install pyimagedl
```

**Usage:**
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

**Output structure:**
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

**Command-line parameters:**

| Parameter | Short | Description | Default |
|-----------|-------|-------------|---------|
| `--keyword` | `-k` | Search keyword (required) | - |
| `--platforms` | `-p` | Specify platform list | All platforms |
| `--num` | `-n` | Images per platform | 50 |
| `--output` | `-o` | Output directory | `image_downloads` |
| `--threads` | `-t` | Download threads | 5 |
| `--no-metadata` | - | Don't save metadata | False |
| `--delay` | - | Delay between platforms (seconds) | 1.0 |
| `--list-platforms` | - | List all platforms | - |

**Python API usage:**
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

**Metadata format:**
Each platform directory contains a `metadata.json` file with:
- Platform name and search keyword
- Timestamp and total images count
- Image details: index, identifier, URLs, file path, raw data (tags, likes, views, etc.)

**Search summary reports:**
- `search_summary.json`: Complete results in JSON format
- `search_summary.md`: Human-readable Markdown report with statistics, success/failure tables

### 1. Xiaohongshu Search (`scripts/tikhub_xhs_search.py`)
Search Xiaohongshu notes with filtering and sorting capabilities.

**Key features:**
- Filter by time range, content type (image/video)
- Sort by likes, comments, shares
- Extract hashtags (only `#` prefixed tags)
- Output includes: note ID, author, type, engagement metrics, tags, title, content

**Usage:**
```bash
python scripts/tikhub_xhs_search.py --keyword "关键词" --limit 10 --sort-field likes --sort-order desc
```

### 2. Xiaohongshu Search (`scripts/tikhub_xhs_search.py`)
Search Douyin videos with comprehensive filtering options.

**Key features:**
- Filter by publish time, duration, content type
- Sort by engagement metrics
- Support pagination with cursor

**Usage:**
```bash
python scripts/tikhub_douyin_search.py --keyword "关键词" --limit 10
```

### 3. Bilibili Search (`scripts/tikhub_bili_search.py`)
Search Bilibili videos and content.

**Usage:**
```bash
python scripts/tikhub_bili_search.py --keyword "关键词" --limit 10
```

### 4. Twitter Search (`scripts/tikhub_twitter_search.py`)
Search Twitter posts and timelines.

**Usage:**
```bash
python scripts/tikhub_twitter_search.py --keyword "关键词" --limit 10
```

### 5. Google Search (`scripts/official_google_search.py`)
Search web content using Google Custom Search API.

**Key features:**
- Clean output with title and link only
- Configurable result count
- No redundant fields in terminal output

**Usage:**
```bash
python scripts/official_google_search.py --query "search query" --num 10
```

### 6. RSS Feed Search (`scripts/rss_search/rss_search.py`)
Search and monitor content from RSS feeds with keyword filtering and multiple output formats.

**Key features:**
- Single or multiple RSS feed support
- Keyword search in title, summary, and content
- Multiple output formats: text, JSON, Markdown
- Result filtering and limiting
- Configuration file support for feed management

**Installation:**
```bash
pip install feedparser
```

**Usage:**
```bash
# Search single RSS feed
python scripts/rss_search/rss_search.py "AI" --feed http://example.com/feed.xml --limit 10

# Search multiple feeds from config file
python scripts/rss_search/rss_search.py "GPT" --feeds rss_feeds.txt --markdown

# Get latest entries without keyword
python scripts/rss_search/rss_search.py --feed http://example.com/feed.xml --limit 5

# Save results to file
python scripts/rss_search/rss_search.py "机器学习" --feed http://example.com/feed.xml --json --pretty -o results.json
```

**Parameters:**
- `query`: Search keyword (optional, returns all entries if omitted)
- `--feed`: Single RSS feed URL
- `--feeds`: Configuration file with multiple feed URLs (one per line)
- `--limit`: Maximum number of results (default: 10)
- `--json`: Output in JSON format
- `--pretty`: Pretty-print JSON output
- `--markdown`: Output in Markdown format
- `--full`: Include full content and details
- `-o, --output`: Save output to file
- `--timeout`: Request timeout in seconds (default: 30)
- `--case-sensitive`: Case-sensitive search

**Configuration file format (`rss_feeds.txt`):**
```
# AI News
http://feedmaker.kindle4rss.com/feeds/AI_era.weixin.xml

# Tech News
https://example.com/tech/rss.xml

# Lines starting with # are comments
```

## Configuration

### Environment Variables

Scripts read configuration from `.env` file in the skill directory or platform-specific config files. Command-line arguments override config values.

**Setup:**

1. **GitHub Search** - Three configuration methods (priority order):
   ```bash
   # Method 1: Configuration file (recommended)
   python scripts/github_search.py config --token YOUR_GITHUB_TOKEN

   # Method 2: Environment variable
   export GITHUB_TOKEN=YOUR_GITHUB_TOKEN

   # Method 3: Command line
   python scripts/github_search.py repo "query" --token YOUR_GITHUB_TOKEN
   ```
   - Get token at: https://github.com/settings/tokens
   - No special scopes needed for public search
   - Config file location: `~/.github-search.json`

2. **Social Media & Web Search** - `.env` file configuration:
   - Copy `.env.example` to `.env`
   - Fill in API credentials:
     - `TIKHUB_TOKEN`: TikHub API token (for Xiaohongshu, Douyin, Bilibili, Twitter)
     - `GOOGLE_API_KEY`: Google Custom Search API key
     - `GOOGLE_SEARCH_ENGINE_ID`: Google Custom Search Engine ID
   - Configure default search parameters (keyword, limit, sort options)

3. **Image Search** - No configuration needed:
   - `multi_platform_image_search.py` works out of the box
   - Only requires: `pip install pyimagedl`

4. **RSS Feed Search** - No API credentials needed:
   - `rss_search.py` works standalone with `pip install feedparser`
   - Optional: Create `rss_feeds.txt` for managing multiple feed URLs
   - Configuration file format: one URL per line, `#` for comments

### Common Parameters

- `--keyword` / `--query`: Search keyword
- `--limit`: Number of results to return (default: 10)
- `--sort-field`: Field to sort by (likes, comments, shares, etc.)
- `--sort-order`: Sort order (asc/desc)
- `--time-range`: Filter by time range (platform-specific)

## Output Format

### Terminal Output
- **Format**: Markdown with Chinese field names
- **Content**: Structured, human-readable results
- **Fields**: Platform-specific essential information (ID, author, engagement metrics, content)

### Raw Response Archiving
- **Location**: `responses/` directory
- **Naming**: Timestamp (YYYYMMDD_HHMMSS) + platform suffix
- **Format**: Original JSON response from API
- **Purpose**: Preserve complete data for later analysis without cluttering conversation context

## Execution Guidelines

### Before Running Scripts

1. Verify `.env` configuration exists and contains valid credentials
2. Ensure `responses/` directory exists (scripts create it automatically)
3. Confirm required Python dependencies are available (standard library only)

### Running Scripts

Execute scripts directly from the skill directory:

```bash
cd C:\Users\zijie\.claude\skills\union-search-skill
python scripts/tikhub_xhs_search.py --keyword "关键词" --limit 10
```

### After Execution

1. Check terminal output for formatted results
2. Locate raw response file in `responses/` directory
3. Reference saved file path for accessing complete API response data

## Best Practices

### Result Filtering
- Use `--limit` to control output volume (default: 10)
- Apply time filters to get recent content
- Sort by engagement metrics to find popular content

### Response Management
- Never paste complete raw JSON into conversation
- Reference `responses/` files when full data access is needed
- Use grep/jq to extract specific fields from saved responses

### Multi-Platform Searches
- Run scripts sequentially for different platforms
- Compare results across platforms using saved response files
- Aggregate metrics from multiple sources

## Error Handling

Common issues and solutions:
- **Missing credentials**: Check `.env` file configuration
- **API rate limits**: Reduce request frequency or limit result count
- **Network timeouts**: Increase `TIKHUB_TIMEOUT` value in `.env`
- **Invalid parameters**: Verify parameter names match script expectations

## Platform-Specific Notes

### Xiaohongshu
- Hashtags extracted only include `#` prefixed tags
- Content type filter: 0=all, 1=video, 2=image
- Sort fields: likes, comments, shares, publish_time

### Douyin
- Supports advanced filtering by duration and content type
- Pagination via cursor parameter
- Search ID and backtrace for result consistency

### Google
- Requires Custom Search Engine setup
- Result count limited by API quota
- Clean output optimized for terminal display
