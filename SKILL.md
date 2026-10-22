---
name: union-search-skill
description: 当用户需要跨多个平台搜索内容时使用此技能：GitHub（仓库、代码、问题）、Reddit、YouTube、微信公众号、知乎开放平台、小宇宙 FM、Google、Bing、百度、DuckDuckGo、Brave、Yahoo、Wikipedia 等通用搜索引擎（含无需 API Key 的直连渠道），Tavily、Exa、Serper、Firecrawl、Jina、DeepSeek、腾讯元宝、TinyFish、AnySearch、阿里云百炼、Parallel、Ollama、智谱、Kimi、秘塔、火山引擎等 AI 搜索服务，以及 Claude Code、Codex、Grok Build 本机原生搜索；也用于网页正文提取、从 16 个图片平台批量下载图片（保留元数据）和 yt-dlp 媒体下载。提供统一 CLI、分组选择、跨渠道去重和机器可读的 JSON 输出。
---

# 联合搜索技能

## 目的

通过统一 CLI 把同一个查询分发到多个搜索渠道，返回结构化结果。注册表共有 50 个搜索渠道、1 个正文提取工具和 16 个图片平台，以 `python union_search_cli.py list` 的输出为准。

## 何时使用此技能

- 跨多个平台搜索内容（开发者社区、搜索引擎、AI 搜索服务、社交与播客）
- 需要无 API Key 的搜索方案
- 提取网页正文、批量下载图片或媒体
- 需要机器可读的结果、错误码和环境检查

## 分组选择

- 默认使用 `general`：25 个无需必填 API Key 的搜索渠道。
- 需要凭据的 22 个渠道在 `api` 分组，按需显式选择；只用其中几家时用 `--platforms`。
- 使用本机 AI coding 工具原生搜索时，选 `ai_tools` 分组，或指定 `claude_code`、`codex`、`grok_build`；需 Python 3.10+、本机登录与账号额度，详见 [AI 工具说明](scripts/channels/ai_tools/README.md)。
- `search`、`no_api_key` 是 `general` 的兼容别名。
- `dev`、`social` 按用途划分；`social` 的三个渠道均需 API Key。
- `all` 包含全部 50 个搜索渠道，包括三个本机账号渠道；Defuddle 单列 `tools`，用专用 `defuddle` 命令处理 URL。
- GitHub Token 和 AnySearch Key 可选；无需必填 Key 不代表不调用远程接口。

## 快速开始

### 1. 配置凭据

在项目根目录从模板创建 `.env`，只填写需要的渠道：

```bash
cp .env.example .env
```

详细配置见 [API 凭据获取指南](references/api_credentials.md)。

用户希望自动获取或填写 API Key 时，阅读 [Agent 自动获取与配置指南](references/agent_api_key_setup.md)。先核对渠道和变量名，获得用户对平台操作、密钥保存和验证范围的授权，再使用当前工具提供的浏览器或 Computer Use 能力执行。登录验证交给用户接管，完成后继续；结果中只报告脱敏状态。

### 2. 执行搜索

统一入口是项目根目录的 `union_search_cli.py`：

```bash
# 联合搜索：同时搜索一个分组
python union_search_cli.py search "AI Agent" --group general --preset small

# 指定多个渠道
python union_search_cli.py search "AI Agent" --platforms github wikipedia tavily --limit 3 --deduplicate

# 单个渠道
python union_search_cli.py platform github "machine learning" --limit 5

# 提取网页正文
python union_search_cli.py defuddle https://example.com --pretty

# 能力发现与环境检查
python union_search_cli.py schema --pretty
python union_search_cli.py doctor --platforms github
```

常用参数：

- `--preset`：预设结果数量（`small`=3，`medium`=5，`large`=10，`extra`=20）
- `--limit` / `-l`：每个渠道的结果上限；默认不限，`0` 表示不限，负数报错。默认返回本次取得的全部结果，不自动遍历所有分页。
- `--platforms` / `-p`：指定渠道（空格分隔）
- `--group` / `-g`：指定分组（`general`、`api`、`ai_tools`、`dev`、`social`、`preferred`、`tools`、`all`）
- `--deduplicate`：跨渠道去重
- `--format`：`json`（默认）、`markdown`、`text`
- `--pretty`：格式化 JSON 输出
- `-o` / `--output`：保存输出到文件
- `--fail-on-platform-error`：任一渠道失败时以退出码 `4` 结束
- `--quiet`：关闭 stderr 诊断，stdout 的结果信封保持不变

统一 CLI 默认输出 JSON，不接受 `--json` 参数。

### 3. 读取结果

机器可读输出遵循固定信封：`schema_version`、`ok`、`type`、`data`（成功）或 `error`（失败）、`meta`。`error` 含稳定错误码、`retryable`、`outcome` 和可执行的 `next_actions`。退出码 `0` 完成、`2` 参数错误、`3` 缺少依赖、`4` 平台暂不可用。搜索默认在渠道失败时仍返回 `0`，必须检查 `ok`。

- 永远不要把完整的原始 JSON 粘贴到对话中；用 `-o` 保存后按需提取字段。
- 零条结果可能源于验证码、限流或解析器失效，先单独查询该渠道再下结论。

## 渠道模块

所有渠道位于 `scripts/channels/`，每个服务一个目录，目录内的 `README.md` 说明参数与凭据。同一服务的 API 版本与无 API Key 直连版本放在同一目录。

### 开发者与社区

| 平台 | 描述 | 文档 |
|------|------|------|
| **GitHub** | 仓库、代码、问题/PR 搜索 | [README](scripts/channels/github_search/README.md) |
| **Reddit** | 帖子、子版块、用户搜索 | [README](scripts/channels/reddit/README.md) |

### 社交、内容与播客

| 平台 | 描述 | 文档 |
|------|------|------|
| **YouTube** | 视频、评论搜索 | [README](scripts/channels/youtube/README.md) |
| **微信** | 微信公众号文章搜索 | [README](scripts/channels/wechat/README.md) |
| **知乎开放平台** | 站内搜索、全网搜索、热榜、直答 | [README](scripts/channels/zhihu_official/README.md) |
| **小宇宙 FM** | 播客搜索 | [README](scripts/channels/xiaoyuzhoufm/README.md) |
| **RSS** | 订阅源内容搜索 | [README](scripts/channels/rss_search/README.md) |

### AI 搜索服务（需 API Key）

| 平台 | 描述 | 文档 |
|------|------|------|
| **Tavily** | AI 驱动搜索引擎 | [README](scripts/channels/tavily_search/README.md) |
| **Exa** | 神经搜索，代码/公司/人物/深度研究 | [README](scripts/channels/exa/README.md) |
| **Firecrawl** | 网页搜索，可同时抓取正文 | [README](scripts/channels/firecrawl/README.md) |
| **Jina** | 网页搜索 | [README](scripts/channels/jina/README.md) |
| **DeepSeek** | 联网搜索，返回相关度与权威度 | [README](scripts/channels/deepseek/README.md) |
| **腾讯元宝** | 腾讯云联网搜索，覆盖腾讯内容生态 | [README](scripts/channels/yuanbao/README.md) |
| **TinyFish** | 轻量实时搜索，返回站点名与摘要 | [README](scripts/channels/tinyfish/README.md) |
| **AnySearch** | 实时搜索，支持垂直领域与匿名访问 | [README](scripts/channels/anysearch/README.md) |
| **阿里云百炼** | 通义千问联网搜索，附带模型回答 | [README](scripts/channels/bailian/README.md) |
| **Parallel** | 自然语言目标，返回摘录 | [README](scripts/channels/parallel_search/README.md) |
| **Ollama** | 托管网页搜索，返回标题、链接与摘要 | [README](scripts/channels/ollama_search/README.md) |
| **智谱** | 基础、高级、搜狗、夸克网络搜索 | [README](scripts/channels/zhipu/README.md) |
| **Kimi** | 基础与专业独立搜索，返回摘要或正文片段 | [README](scripts/channels/kimi/README.md) |
| **秘塔搜索** | AI 驱动搜索，智能摘要 | [README](scripts/channels/metaso/README.md) |
| **火山引擎** | 字节跳动融合信息搜索 | [README](scripts/channels/volcengine/README.md) |
| **Cloudflare** | 经 AI Gateway 调用 Ceramic.ai、Exa、Linkup（独立模块，未注册为 CLI 渠道） | [README](scripts/channels/cloudflare/README.md) |
| **Querit** | 内容检索，返回页面时间与站点权威度（独立模块，未注册为 CLI 渠道） | [README](scripts/channels/querit/README.md) |

Serper、Yandex（SerpAPI）、Bing（SerpAPI）、Google Custom Search 与百度千帆的脚本分别位于 `serper/`、`yandex/`、`bing/`、`google_search/`、`baidu/`。

### 通用搜索引擎（无需 API Key）

| 平台 | 描述 | 文档 |
|------|------|------|
| **DuckDuckGo** | 隐私搜索引擎，另有 HTML 与即时答案版本 | [README](scripts/channels/duckduckgo/README.md) |
| **Brave** | 隐私搜索引擎 | [README](scripts/channels/brave/README.md) |
| **Yahoo** | 雅虎搜索引擎 | [README](scripts/channels/yahoo/README.md) |
| **Bing** | 中国版与国际版直连 | [README](scripts/channels/bing/README.md) |
| **Google** | 直连与香港直连 | [README](scripts/channels/google_search/README.md) |
| **Wikipedia** | 百科全书搜索 | [README](scripts/channels/wikipedia/README.md) |

百度、360、搜狗、头条、集思录、Startpage、Ecosia、Qwant、Mojeek、WolframAlpha 的直连脚本位于同名目录下的 `*_no_api.py`，共享基类在 `scripts/channels/no_api/`。

### 其他工具

| 工具 | 描述 | 文档 |
|------|------|------|
| **联合搜索编排** | 并发调度、分组与凭据元数据 | [README](scripts/union_search/README.md) |
| **统一 CLI** | 参数、能力注册、错误码与输出信封 | [README](scripts/cli/README.md) |
| **图片搜索** | 16 个平台批量图片下载（含火山引擎） | [README](scripts/union_image_search/README.md) |
| **网页正文提取** | Defuddle、Jina、Firecrawl 引擎 | [README](scripts/url_to_markdown/README.md) |

## 单渠道脚本

`scripts/channels/` 下的脚本都可以独立运行，例如：

```bash
python scripts/channels/tavily_search/tavily_search.py "AI agent" --json
python scripts/channels/baidu/baidu_no_api.py "人工智能" --json -m 5
```

单渠道脚本大多支持 `--json` 与 `--max-results`（多数提供 `-m` 简写）；具体参数以各模块 README 和 `--help` 为准。脚本从项目根目录 `.env` 读取凭据，命令行参数优先于环境变量。部分脚本支持保存原始响应，文件写入该脚本目录下的 `responses/`。

## 参考文档

- **[API 凭据获取指南](references/api_credentials.md)** - 各平台 API 凭据的获取方式
- **[Agent 自动获取与配置指南](references/agent_api_key_setup.md)** - 让 Agent 获取并写入 API Key
- **[速率限制说明](references/rate_limits.md)** - 各平台的速率限制和配额
- **[平台特定说明](references/platform_notes.md)** - 各平台的特殊说明和注意事项
- **[问题排查指南](references/troubleshooting.md)** - 常见问题的诊断和解决方案
- **[Google 搜索技巧](references/google_search_guide.md)** - Google 搜索高级指令速查
- **[百度 API Key 获取](references/baidu_apikey_fetch.md)** - 百度千帆凭据

## 常见问题速查

| 问题 | 解决方案 | 详细文档 |
|------|----------|----------|
| 缺少凭据 | 运行 `doctor --platforms <name>`，检查 `.env` | [API 凭据](references/api_credentials.md) |
| API 速率限制 | 降低 `--max-workers` 或限制结果数量 | [速率限制](references/rate_limits.md) |
| 网络超时 | 增加 `--timeout` 或使用代理 | [问题排查](references/troubleshooting.md) |
| 无效参数 | 使用 `--help` 或查看模块 README | 各模块 README |
| 403 Blocked | 使用代理或降低请求频率 | [问题排查](references/troubleshooting.md) |
| 平台特定问题 | 查看平台说明 | [平台说明](references/platform_notes.md) |

## 项目结构

```
union-search-skill/
├── union_search_cli.py         # 统一 CLI 入口
├── SKILL.md                    # 本文件
├── README.md                   # 项目说明
├── .env.example                # 环境变量模板
├── requirements.txt            # Python 依赖
├── package.json                # 根目录 Node.js 依赖（微信 JS、Defuddle）
├── config/mcporter.json        # Exa MCP 调用配置
├── scripts/
│   ├── cli/                    # CLI 解析、能力注册、错误码与输出
│   ├── union_search/           # 多渠道编排、分组与凭据元数据
│   ├── channels/               # 搜索渠道，每个服务一个目录
│   │   ├── no_api/             # 无 API Key 引擎共享基类
│   │   ├── ai_tools/           # Claude Code / Codex / Grok Build 原生搜索
│   │   ├── github_search/ reddit/ youtube/ wechat/ zhihu_official/ xiaoyuzhoufm/ rss_search/
│   │   ├── google_search/ bing/ baidu/ duckduckgo/ duckduckgo_instant/ brave/ yahoo/ yandex/ wikipedia/
│   │   ├── so360/ sogou/ toutiao/ jisilu/ startpage/ ecosia/ qwant/ mojeek/ wolfram/
│   │   └── tavily_search/ exa/ serper/ firecrawl/ jina/ deepseek/ yuanbao/ tinyfish/ anysearch/
│   │       bailian/ parallel_search/ ollama_search/ zhipu/ kimi/ metaso/ volcengine/ cloudflare/ querit/
│   ├── union_image_search/     # 图片搜索与下载
│   ├── url_to_markdown/        # 网页正文提取
│   └── downloader/             # yt-dlp 视频与音频下载
├── references/                 # 参考文档
├── tests/                      # 离线回归测试
└── assets/readme/              # README 视觉素材
```

## 配置优先级

所有工具支持三种配置方式（优先级从高到低）：

1. **命令行参数**：`--token YOUR_TOKEN` 或 `--api-key YOUR_KEY`
2. **环境变量**：在项目根目录的 `.env` 文件中配置，或用 `--env-file` 指定
3. **配置文件**：工具特定的配置文件（如 GitHub 的 `~/.github-search.json`）
