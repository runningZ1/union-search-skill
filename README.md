<a id="top"></a>

# Union Search Skill

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

![Union Search：通过统一 CLI 选择搜索渠道，将结果交给人或 Agent。流程示意，非运行截图。](assets/readme/hero.svg)

面向 Claude Code、Codex 和命令行用户的多平台搜索工具，提供联合搜索、图片下载、网页正文提取与媒体下载入口。

## 本次重大更新说明

距离上一次集中更新与推送已过去数月，本次属于一次重大更新，涉及搜索渠道与分组、统一 CLI 和输出格式、Agent 接入、API Key 配置引导，以及项目文档和开源协议说明。老用户升级后，请重新阅读下方的快速开始与渠道说明，检查现有命令、配置和自动化脚本是否仍然适用。

本次改动范围较大，可能仍有遗漏、兼容性问题或尚未发现的瑕疵。各平台的接口、登录要求、配额与页面也会变化；代码中已接入某个渠道，不代表它在所有账号、网络和运行环境下都能正常使用。建议先选择少量需要的渠道完成配置和实际搜索，再用于日常任务。

**如果遇到无法正常使用、结果异常、文档不清楚或其他问题，请及时提交 [GitHub Issues](https://github.com/runningZ1/union-search-skill/issues)。** 欢迎提供可复现的例子，帮助后续修复与完善。反馈时请附上所用渠道、执行命令、预期与实际表现、运行环境及脱敏报错，具体见[问题反馈说明](#contributing)。

<p align="center">
  <a href="#quickstart">快速开始</a> ·
  <a href="#examples">使用示例</a> ·
  <a href="#platforms">渠道与状态</a> ·
  <a href="#agents">Agent 接入</a> ·
  <a href="SKILL.md">技能说明</a>
</p>

把同一个问题交给多个指定渠道，控制每个平台的结果数，并以 JSON、Markdown 或文本输出。需要进一步阅读时，可提取网页正文；需要素材时，可调用图片和媒体下载命令。

| 你要完成的事 | 使用入口 | 输出或用途 |
| --- | --- | --- |
| 查找开源项目与技术资料 | `platform github`、`search --platforms …` | 单渠道结果或多渠道汇总，可选跨渠道去重 |
| 收集网页与社交平台信息 | `search --group …`、`platform <name>` | 按任务选择渠道，凭据要求各不相同 |
| 下载图片和媒体素材 | `image`、`download` | 本地文件；媒体下载基于 yt-dlp |
| 阅读网页正文 | `defuddle <url>` | 提取正文，可保存为 Markdown |
| 让 Agent 发现能力与处理错误 | `schema`、`errors`、`doctor` | 机器可读的能力、错误码与环境检查结果 |

目录：[快速开始](#quickstart) · [使用示例](#examples) · [渠道与状态](#platforms) · [配置与依赖](#configuration) · [Agent 自动配置 API Key](#api-key-setup) · [Agent 接入](#agents) · [故障排查](#troubleshooting) · [项目结构](#structure) · [参与维护](#contributing) · [许可证与致谢](#credits)

<a id="quickstart"></a>

## 快速开始

### 1. 获取代码并安装依赖

```bash
git clone https://github.com/runningZ1/union-search-skill.git
cd union-search-skill
python -m pip install -r requirements.txt
```

如果已将此目录安装为 Skill，直接进入技能目录执行后续命令。Agent 使用前先阅读 [SKILL.md](SKILL.md)。

### 2. 检查环境

```bash
python union_search_cli.py doctor --platforms github --pretty
```

`doctor` 检查依赖与凭据是否存在，不会验证远程服务是否可用。图片、下载和正文提取依赖不同，按[配置与依赖](#configuration)启用。

需要配置 API 时，从模板创建 `.env`。以下命令只在文件不存在时复制，保留已有配置：

```bash
python -c "from pathlib import Path; p = Path('.env'); p.exists() or p.write_bytes(Path('ENV_TEMPLATE.txt').read_bytes())"
```

按需要填入对应渠道的凭据，不必配置全部服务。GitHub 仓库搜索可先不填 Token；认证通常能提高请求额度。

### 3. 执行第一次搜索

```bash
python union_search_cli.py platform github "readme topic:documentation" --limit 3 --pretty --fail-on-platform-error
```

默认输出 JSON，`--pretty` 只调整缩进。优先查看顶层 `ok`，再读取成功结果中的 `data.items`；有结果时继续查看标题和链接。无需额外传入 `--json`，统一 CLI 不接受这个参数。

<a id="examples"></a>

## 使用示例

### 指定渠道联合搜索

```bash
python union_search_cli.py search "AI agent" --platforms github wikipedia --limit 3 --deduplicate --pretty --fail-on-platform-error
```

默认不限制本地返回条数，返回本次取得的全部结果；`--limit 0` 同样表示不限。正整数 `--limit N` 是每个平台的结果上限。`--deduplicate` 启用跨渠道去重；`--max-workers` 控制并发，`--timeout` 设置超时秒数。渠道失败不会自动替换成另一家服务，需要调用方选择其他渠道。

“不限”不等于无限翻页：API 单次请求量、站点页面容量、模型输出窗口和超时仍然生效。API 保留合法的请求批量参数，但返回数据不再被默认截取为前 5 / 10 / 20 条。图片命令默认不做本地截断；底层图片 SDK 的现有批量请求范围为 10,000 张，仍受来源限制。显式 `--preset` 会启用相应条数上限。

### 保存便于阅读的结果

```bash
python union_search_cli.py search "Python packaging" --platforms github --limit 5 --format markdown -o out/search.md
```

JSON、Markdown 和文本输出均保留完整数据，Markdown 使用 JSON 代码块呈现各渠道的完整字段，不再只展示前几项摘要。`-o` 保存到文件，目标目录会自动创建。

### 按分组搜索

```bash
python union_search_cli.py list --type groups --pretty
python union_search_cli.py search "Python" --group general --preset small --pretty
python union_search_cli.py search "AI agent" --group api --preset small --pretty
```

`general` 无需配置必填 API Key，也是未指定渠道和分组时的默认范围。`api` 需要先配置各服务的凭据，会调用整个 API 分组；只想使用其中几家时，改用 `--platforms tavily metaso`。

`small`、`medium`、`large`、`extra` 分别对应每渠道 3、5、10、20 条。无需 API Key 不等于不访问远程接口：GitHub、Wikipedia 和 AnySearch 等可匿名调用。无 Key 渠道仍可能遇到验证码、限流或空结果。

### 提取网页正文

安装 Node.js 与下文列出的 Node 依赖后：

```bash
python union_search_cli.py defuddle "https://example.com" --pretty
python union_search_cli.py defuddle "https://example.com" --format markdown -o out/article.md
```

这里调用本地 Defuddle 引擎。仓库中还保留了[其他正文提取工具](scripts/url_to_markdown/)，其参数与调用方式请查阅对应模块。

### 下载图片

```bash
python union_search_cli.py image "mountain landscape" --platforms bing --limit 5 --output-dir image_downloads --pretty
```

图片命令依赖 `pyimagedl`，默认保留元数据。可用平台名称通过 `list` 查看，部分图库还需要各自的 API Key。

### 从搜索结果下载媒体

```bash
python union_search_cli.py search "Python tutorial" --platforms youtube --limit 3 -o out/videos.json --pretty --fail-on-platform-error
python union_search_cli.py download --from-file out/videos.json --select 1 --output-dir downloads --pretty
```

第一步需要 `YOUTUBE_API_KEY`。搜索结果中的 `download_candidates` 提供候选索引，先查看候选再用 `--select` 选择。媒体下载依赖 yt-dlp；合并音视频或提取音频还需要 FFmpeg。下载能力取决于目标站点与登录状态，详见 [CLI 文档](scripts/cli/README.md)。

<a id="platforms"></a>

## 渠道与状态

当前代码注册了 **52 个搜索渠道和 1 个正文提取工具**。搜索渠道分为 **25 个无需必填 API Key**、**24 个需要 API Key** 和 **3 个使用本机 AI coding 工具登录态** 的条目；不同访问方式按独立条目计算，并不代表全部已验证可用。图片 CLI 的注册表列出 **16 个平台**。后续以运行结果为准：

```bash
python union_search_cli.py list --pretty
python union_search_cli.py schema --pretty
```

| 分组 | 内容 | 使用提示 |
| --- | --- | --- |
| `general` | 百度 / Bing 直连、DuckDuckGo、Wikipedia、GitHub、Reddit、匿名 AnySearch 等 25 个条目 | 默认分组，无需必填 API Key |
| `api` | Google API、Bing / Yandex SerpAPI、Tavily、Exa、Serper、Kimi 等 24 个条目 | 需配置对应凭据；小宇宙使用 `METASO_API_KEY` |
| `ai_tools` | Claude Code、Codex、Grok Build | 使用本机登录态与账号额度，不进入默认分组 |
| `search` / `no_api_key` | 与 `general` 相同 | 兼容旧命令；旧 `search` 不再混入 API 渠道 |
| `dev` | GitHub、Reddit | 主题子集，无需必填 API Key；Reddit 标记为 `degraded` |
| `social` | YouTube、知乎开放平台、小宇宙 FM | 主题子集，三个渠道均需 API Key |
| `preferred` | 代码中预设的 6 个无 API Key 渠道 | 预设分组，不代表当前网络下全部可用 |
| `tools` | Defuddle | 网页正文提取，应使用专用 `defuddle` 命令 |
| `all` | 全部 52 个搜索渠道 | 显式选择，包含 API 和本机账号渠道；不含 Defuddle |

图片渠道：`baidu`、`bing`、`google`、`i360`、`pixabay`、`yandex`、`sogou`、`yahoo`、`unsplash`、`gelbooru`、`safebooru`、`danbooru`、`pexels`、`huaban`、`foodiesfeed`、`volcengine`。

### 已知边界

- TikHub 接入已移除，包括小红书、抖音、Bilibili、Twitter、微博及旧知乎搜索；独立的 `zhihu_official` 保留。
- 分组与 CLI 凭据检查共用元数据，Exa、Serper 和小宇宙已归入需 API 分组。
- Reddit 和火山引擎标记为 `degraded`，分别有访问受限和历史解析不稳定的问题。
- 注册表中的 `stable` 是代码元数据，不是实时健康检查结果。零条结果也可能源于验证码或选择器失效。
- RSS、微信等独立模块可通过 [SKILL.md](SKILL.md) 的模块导航查找，并非都注册为统一 CLI 子命令。

<a id="configuration"></a>

## 配置与依赖

Claude Code、Codex、Grok Build 的原生搜索已直接集成在仓库内，使用 `--group ai_tools` 或单独指定 `claude_code`、`codex`、`grok_build`。需要 Python 3.10+ 与对应本机账号权限，详见 [AI 工具搜索说明](scripts/ai_tools/README.md)。

| 功能 | 依赖或配置 | 说明 |
| --- | --- | --- |
| Python 搜索入口 | [requirements.txt](requirements.txt) | 用 `python -m pip install -r requirements.txt` 安装 |
| GitHub 搜索 | `GITHUB_TOKEN` 可选 | 代码搜索等能力以 GitHub 的认证要求为准 |
| Google API 搜索 | `GOOGLE_API_KEY`、`GOOGLE_SEARCH_ENGINE_ID` | 对应 `google`，不同于 `google_direct` |
| YouTube / 知乎开放平台 / 小宇宙 | `YOUTUBE_API_KEY` / `ZHIHU_ACCESS_SECRET` / `METASO_API_KEY` | 使用独立服务，不依赖 TikHub |
| AI 搜索服务 | 对应服务的 API Key | 查看 [凭据指南](references/api_credentials.md) 和各模块文档 |
| 图片下载 | `pyimagedl`，部分平台另需凭据 | 安装 Python 依赖后由 `doctor` 检查 |
| 媒体下载 | yt-dlp、可选 FFmpeg 和 Cookie | 合并格式及音频提取需要 FFmpeg |
| Defuddle / 微信 JS 模块 | Node.js、npm 和模块依赖 | 按下面的命令安装 |

```bash
npm install
npm --prefix scripts/url_to_markdown/engines/defuddle-node install
python union_search_cli.py doctor --pretty
```

命令默认从当前工作目录读取 `.env`，请在仓库根目录执行，或通过 `--env-file` 指定路径。检查器主要依据注册表判断凭据是否存在，具体认证要求仍以模块文档和服务响应为准。

更多配置见 [环境变量模板](ENV_TEMPLATE.txt)、[渠道说明](references/platform_notes.md) 与[速率限制说明](references/rate_limits.md)。

<a id="api-key-setup"></a>

## 用 Agent 自动配置 API Key

不想逐个平台查找、复制和填写密钥时，可让具备 Computer Use 和本地文件读写能力的 Codex 或其他 Agent 协助完成。Agent 先列出所需凭据和操作范围，获得授权后访问官方控制台，获取密钥并写入本地配置，再按授权范围验证搜索。登录、验证码和双重验证由用户接管。

将下面的提示词发给 Agent，替换项目路径和所需渠道即可：

```text
请为我的 Union Search Skill 配置 API Key。
项目路径：<本机 union-search-skill 的绝对路径>
需要的渠道：tavily、exa、metaso（按需替换，不必配置全部平台）。

先阅读项目的 references/agent_api_key_setup.md、SKILL.md 和环境变量模板，
核对这些渠道需要的凭据、官方入口和本地保存位置。
向我说明操作范围，包括是否创建新 Key、是否进行可能消耗额度的验证，
获得我明确授权后，使用你自带的 Computer Use 按指南完成配置。
遇到登录或验证码时让我接管，完成后从中断处继续。
保留已有有效配置，不在聊天中展示密钥，最后报告各渠道的配置和验证状态。
```

完整的批量配置、授权回复、失败续接提示词，以及各平台的查找方向，见 [Agent 自动获取与配置 API Key 指南](references/agent_api_key_setup.md)。凭据可存放在项目本地文档文件夹 `local_dev_doc/api-credentials/`，通过 `--env-file` 加载；也可按用户选择写入根目录 `.env`。保存密钥后仍需检查依赖、权限、额度与接口响应，才能确认对应渠道可用。

<a id="agents"></a>

## Agent 接入

Agent 先阅读 [SKILL.md](SKILL.md)，再通过 CLI 发现当前能力：

```bash
python union_search_cli.py schema --pretty
python union_search_cli.py errors --pretty
python union_search_cli.py doctor --platforms github --pretty
```

统一入口默认把 JSON 写入 stdout，把诊断信息写入 stderr。`--quiet` 可关闭诊断日志。程序应读取 `schema_version`、`ok`、`type` 和 `meta`，成功时读取 `data`，失败时读取 `error`。

以下仅示意成功信封的结构，省略兼容字段，**不是实际搜索输出**：

```json
{
  "schema_version": "1.0",
  "ok": true,
  "type": "result",
  "data": {},
  "meta": { "request_id": "req_example", "duration_ms": 42 }
}
```

失败时检查 `error.code`、`error.retryable`、`error.outcome` 和 `error.next_actions`。错误建议中出现的 `union-search …` 可按本仓库调用方式替换为 `python union_search_cli.py …`。

| 退出码 | 含义 | 调用方动作 |
| --- | --- | --- |
| `0` | 命令完成 | 继续检查 `ok` 与结果是否为空 |
| `1` | 内部错误 | 保留诊断信息 |
| `2` | 参数或用法错误 | 修正参数 |
| `3` | 缺少依赖或资源 | 按错误建议处理 |
| `4` | 超时、限流、服务暂不可用 | 根据错误信息决定是否有限重试 |
| `130` | 被中断 | 停止后续动作 |

搜索默认可在平台失败时仍返回退出码 `0`，此时 JSON 的 `ok` 为 `false`，不能只靠退出码判断成功。需要脚本严格失败时，在 `search` 或 `platform` 命令上添加 `--fail-on-platform-error`，平台失败将返回 `4`。当前失败信封不保留成功的部分结果，调用方应缩小渠道范围后重新查询。

<a id="troubleshooting"></a>

## 故障排查

| 现象 | 先做什么 |
| --- | --- |
| `unrecognized arguments: --json` | 删除 `--json`；统一 CLI 默认输出 JSON，缩进用 `--pretty` |
| 缺少凭据或模块 | 运行 `doctor --platforms <name>`，对照对应模块的说明 |
| HTTP 403 / 429 | 检查认证、网络出口与服务限流；缩小渠道范围，降低 `--max-workers` |
| 请求完成但没有结果 | 换一个明确关键词；检查是否为验证码页面或解析器失效 |
| 一个渠道失败导致联合结果 `ok: false` | 单独查询该渠道；需要其他结果时，只选择其余渠道重跑 |
| 图片命令不可用 | 检查 `pyimagedl` 是否安装在当前 Python 环境中 |
| Defuddle 无法运行 | 检查 Node.js、根目录 npm 依赖与 `defuddle-node` 子目录依赖 |
| 媒体下载遇到 403 或格式合并失败 | 检查 yt-dlp、FFmpeg，必要时显式传入 `--cookies-file` |

```bash
python union_search_cli.py platform --help
python union_search_cli.py search --help
python union_search_cli.py doctor --platforms github google --pretty
```

详细说明见[故障排查文档](references/troubleshooting.md)。

<a id="structure"></a>

## 项目结构

```text
union-search-skill/
├── README.md                 # 项目入口与上手流程
├── SKILL.md                  # Agent 使用指引与模块导航
├── LICENSE                   # 项目 MIT 许可证
├── THIRD_PARTY.md            # 第三方依赖、集成来源与致谢
├── union_search_cli.py       # 统一命令入口
├── assets/readme/            # README 本地视觉素材
├── scripts/
│   ├── cli/                  # 参数、能力注册、错误与输出契约
│   ├── union_search/         # 多渠道搜索编排
│   ├── union_image_search/   # 图片搜索与下载
│   ├── downloader/          # yt-dlp 媒体下载适配
│   ├── url_to_markdown/     # 网页正文提取
│   └── …                   # 各渠道独立模块
├── references/              # 凭据、渠道和排障文档
├── ENV_TEMPLATE.txt         # 环境变量模板
├── requirements.txt         # Python 依赖
└── package.json             # 根目录 Node.js 依赖
```

完整参数见 [CLI 文档](scripts/cli/README.md)，联合编排说明见[联合搜索模块](scripts/union_search/README.md)。

<a id="contributing"></a>

## 参与维护

使用中遇到功能不可用、结果异常、升级兼容问题或文档错误，请及时到 [GitHub Issues](https://github.com/runningZ1/union-search-skill/issues) 反馈。提交前可先搜索已有 Issue；没有相同问题时，使用[新建 Issue](https://github.com/runningZ1/union-search-skill/issues/new)描述情况，也欢迎提交 Pull Request。

为便于复现，请尽量提供：

- 所用版本或提交号，以及操作系统、Python / Node.js 版本。
- 出问题的渠道、完整执行命令和最少复现步骤。
- 预期表现、实际表现、退出码，以及脱敏后的错误信息或截图。
- 对应渠道的 `doctor` 检查结果，以及问题是否每次都能复现。

请勿上传真实 API Key、Token、Cookie、完整 `.env` 文件或包含凭据的截图。暂时无法判断原因也可以先提 Issue，说明已观察到的情况即可。

添加或修改渠道时，同步检查平台适配器、分组、凭据元数据、CLI 帮助与模块文档。区分“脚本存在”“本地命令通过”和“远程返回有效结果”，避免把一次测试写成长期可用承诺。

<a id="credits"></a>

## 许可证与致谢

本项目现阶段暂定采用 **MIT 开源协议**，完整文本见 [LICENSE](LICENSE)。本仓库原创代码与文档按该协议提供，使用、修改和分发时请保留相应版权与许可声明。第三方代码、依赖及其附带资源保留各自的许可证，不因本项目采用 MIT 而改变。

主要依赖与集成项目包括：

| 用途 | 相关项目 |
| --- | --- |
| HTTP 请求、配置和 HTML 解析 | [Requests](https://github.com/psf/requests)、[python-dotenv](https://github.com/theskumar/python-dotenv)、[lxml](https://github.com/lxml/lxml) |
| 日志与结构化数据校验 | [Loguru](https://github.com/Delgan/loguru)、[Pydantic](https://github.com/pydantic/pydantic) |
| 图片、媒体下载与处理 | [pyimagedl / imagedl](https://github.com/CharlesPikachu/imagedl)、[yt-dlp](https://github.com/yt-dlp/yt-dlp)、[FFmpeg](https://ffmpeg.org/) |
| 搜索服务 SDK | [tavily-python](https://github.com/tavily-ai/tavily-python)、[firecrawl-py](https://pypi.org/project/firecrawl-py/) |
| 网页提取与 Node.js 工具 | [Defuddle](https://github.com/kepano/defuddle)、[Cheerio](https://github.com/cheeriojs/cheerio)、[Commander.js](https://github.com/tj/commander.js)、[jsdom](https://github.com/jsdom/jsdom) |

完整的直接依赖、可选组件、迁入代码来源、外部服务边界与文档参考见 [第三方项目与依赖说明](THIRD_PARTY.md)。该清单依据当前仓库整理，不代表已完成全部传递依赖的许可证审计。

MIT 协议不包含第三方 API 的使用额度、账号权限或搜索结果内容的授权。各搜索服务、本机 AI 客户端及其账号仍按各自条款使用。Computer Use 配置指南是一套由用户授权后交给 Agent 执行的流程，需要用户自己的工具、账号与凭据。

[返回顶部](#top)
