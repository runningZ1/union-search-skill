# 搜索、正文提取与下载执行指南

## 工作目录与依赖

以根目录 `SKILL.md` 所在位置作为执行目录，入口为 `python union_search_cli.py`。从其他目录调用绝对路径时，显式指定支持的 `--env-file` 和输出目录，避免把调用方目录的配置当成技能配置。

Python 依赖通过 `python -m pip install -r requirements.txt` 安装。微信 JavaScript 和 Defuddle 的 Node.js 依赖见 [项目 README](../README.md) 及 [正文提取说明](../scripts/url_to_markdown/README.md)。媒体下载需要 yt-dlp，音频转换还需要 FFmpeg。

先执行 `doctor --platforms <渠道>`。`doctor` 检查本地依赖和凭据存在状态，远程可用性需要实际请求确认。仅安装当前任务缺少的依赖。

## 凭据

已有 `.env` 时保留其内容。仅在文件不存在且任务确实需要凭据时从 `.env.example` 创建，然后按 [凭据指南](api_credentials.md) 填写所选服务。不要为无需凭据的任务强制创建配置。

统一搜索命令使用环境变量和支持的 `--env-file`。独立脚本的 `--api-key`、`--token` 和配置文件能力各不相同，使用前读取对应帮助。不要将某个脚本的参数套用到全部命令。

代用户获取、保存或验证密钥时，读取 [Agent 配置指南](agent_api_key_setup.md)，在已授权范围内操作；结果仅报告脱敏状态。

## 渠道选择

`python union_search_cli.py list --type groups --pretty` 提供当前分组，`schema` 提供机器可读能力。注册表当前有 53 项能力，其中包含 52 个搜索渠道和 1 个正文工具；另有 24 个图片平台，包含 12 个原生平台与 12 个 SDK 平台。执行时以清单为准。

| 条件 | 选择方法 |
|------|----------|
| 用户明确指定平台 | 使用 `--platforms` 或 `platform <名称>` |
| 用户未指定平台 | 按内容类型选择相关且可用的渠道；通用联合搜索可使用默认 `general` |
| 通用网页搜索 | `general`、`search`、`preferred` 均含 8 个网页渠道，`general` 为默认分组 |
| 无必填 API Key | `no_api_key` 含 26 个渠道，包括网页搜索、GitHub、Wikipedia 等 |
| 使用 API 服务 | `api` 含 23 个渠道；检查凭据后选择需要的服务 |
| 使用本机账号搜索 | `ai_tools` 含三个渠道，要求 Python 3.10+、工具已登录和账号额度 |
| 开发者或社交内容 | 查看 `dev`、`social` 的成员；`social` 的三个渠道均需凭据 |
| 全渠道搜索 | `all` 含全部搜索渠道，包括本机工具；执行前确认请求范围和环境 |

GitHub Token 可选。AnySearch 属于 `api` 分组，必须配置 `ANYSEARCH_API_KEY`。无需必填 Key 的渠道仍可能调用远程服务、遭遇限流或验证码。微信目前是独立模块，使用其 README 中的脚本入口。

微信公众号搜索使用 `node scripts/channels/wechat/search_wechat.js "人工智能" -n 5 -o .work/wechat.json`。该入口需要 Node.js 与根目录 npm 依赖，结果结构为 `query`、`total`、`articles`，不采用统一 CLI 信封。具体参数见 [微信说明](../scripts/channels/wechat/README.md)。

默认网页分组依次为 `baidu_direct`、`so360_direct`、`sogou_direct`、`duckduckgo`、`brave`、`yahoo`、`yandex_direct`、`quark_direct`。网页渠道由本项目独立实现，无外部项目运行依赖；360、搜狗、DuckDuckGo、Brave、Yahoo 使用 `curl_cffi>=0.16,<0.17`，Yandex 和 Quark 使用匿名访问。

`duckduckgo_html`、`brave_direct`、`yahoo_direct` 保留兼容入口，与同服务渠道共用实现。一次联合请求按来源去重，仅执行同服务的首个入口；`--deduplicate` 控制结果去重。

单渠道可通过重复的 `--param key=value` 指定 `page`、`timelimit`、`proxy`、`region`、`country`、`safesearch`，具体渠道不支持时明确失败。DuckDuckGo 网页仅支持 `page`，不支持 `timelimit` 或非 `wt-wt` 的 `region`，例如 `python union_search_cli.py platform duckduckgo "Python" --param page=2 --limit 3 --pretty`。

## 搜索与原文核实

```bash
python union_search_cli.py search "Python packaging" --platforms github wikipedia --limit 3 --deduplicate --fail-on-platform-error -o .work/search.json
python union_search_cli.py platform github "Python packaging" --limit 3 -o .work/github.json
python union_search_cli.py defuddle "https://example.com" --format markdown -o .work/article.md
```

`--limit` 控制每个渠道的上限。默认和 `0` 表示保留本次取得的全部结果，不自动遍历全部分页。`--preset small/medium/large/extra` 分别对应 3/5/10/20 条。独立脚本的数量参数可能为 `--max-results`，以对应帮助为准。

搜索结果用于发现来源。比较事实、引用观点或说明当前状态时，读取相关原文，保留标题、链接和适用时间。多个渠道命中同一页面时使用 `--deduplicate` 按规范 URL 合并，`data.final_items[].sources` 保留全部来源和原始排名。同名不同网址分别保留；不要把渠道数量当成独立证据数量。网页结果统一提供标题、URL、摘要、日期、缩略图和来源，渠道错误与耗时放在 `data.channels`，整批耗时放在 `data.timing`。

正文提取的默认输出仍是 JSON 信封；需要 Markdown 文件时明确传入 `--format markdown`。引擎选择与凭据见 [正文提取说明](../scripts/url_to_markdown/README.md)。

## 图片搜索与下载

```bash
python union_search_cli.py list --type images --pretty
python union_search_cli.py image "mountain landscape" --search-only --limit 5 --pretty
python union_search_cli.py image "mountain landscape" --platforms bing --limit 5 --output-dir .work/images -o .work/images.json
```

`image` 默认使用 `baidu bing wikicommons` 搜索并下载图片。仅需图片地址、来源和元数据时使用 `--search-only`；该选项仅支持本项目的原生平台，不支持的平台明确报错。可通过 `--platforms` 显式选择保留的 SDK 平台；平台失败时不自动切换来源。默认和 `--limit 0` 保留本次取得的全部结果，原生搜索限于本次单页，不自动遍历全部分页。

图片 `metadata` 为字典，统一字段为 `title`、`image_url`、`source_url`、`thumbnail`、`width`、`height`、`author`、`license`、`image_variant`、`provider`、`id`、`file_path`、`download_status`，缺失字段为 `null`。`image_variant` 标明来源原始或最大可用版本，不能将全部结果视为来源原文件。纯搜索不生成图片文件。

下载时指定输出目录和数量，检查实际文件经过 Pillow `Image.verify()` 校验，并核对 `sha256`、`bytes`、元数据及单张图片的下载状态。单张图片失败记录保留在结果中，部分失败时 `ok: false`，信封保留 `data`。返回已验证的文件位置及失败范围。平台专用能力与独立脚本参数见 [图片说明](../scripts/union_image_search/README.md)。

## 媒体下载

直接下载用户指定的媒体 URL：

```bash
python union_search_cli.py download "<媒体URL>" --output-dir .work/media --fail-on-download-error -o .work/media.json
```

从搜索结果选择媒体：

```bash
python union_search_cli.py search "Python tutorial" --platforms youtube --limit 3 --fail-on-platform-error -o .work/videos.json
python union_search_cli.py download --from-file .work/videos.json --select 1 --output-dir .work/media --fail-on-download-error -o .work/media.json
```

先读取真实结果中的 `data.download_candidates`，再使用从 1 开始的索引。添加 `--platforms` 时，下载器先筛选平台、按 URL 去重，再从 1 重新编号；`--select` 使用筛选后的编号。YouTube 搜索需要 `YOUTUBE_API_KEY`。仅有普通网页链接时，先确认它是 yt-dlp 支持的媒体来源。

音频提取可使用 `--audio-only --audio-format mp3`，需要 FFmpeg。`--dry-run` 会请求远程元数据并创建输出目录。Cookie、格式和其他选项以 `download --help` 为准。

## 失败与完成条件

检查顶层 `ok`，失败时读取 `error.code`、`retryable`、`outcome`、`next_actions` 和诊断信息。搜索部分失败时信封保留 `data`，须逐渠道检查成功结果和错误。下载失败时检查信封以及实际目录，本地文件可能已经生成。检查实际目录，避免把已生成的文件描述为全部失败或完整成功。

网页请求跨命令按 host 保持至少两秒间隔；429 遵守 `Retry-After`，缺失时冷却 300 秒，验证码冷却 900 秒。冷却期明确返回错误，不自动重试或切换来源，等待也计入截止时间。

搜索默认允许单渠道失败并返回退出码 `0`；需要严格退出状态时使用 `--fail-on-platform-error`。媒体下载使用 `--fail-on-download-error`。图片任务始终检查结果信封与实际目录。

完成搜索需要有可追溯来源和明确的覆盖范围。完成下载需要有实际文件与对应位置。凭据缺失、网络阻断、限流或解析失败时，报告具体渠道和错误，不将失败解释为资料不存在。
