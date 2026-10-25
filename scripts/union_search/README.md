# Union Search

多渠道关键词搜索编排器。推荐从仓库根目录使用统一 CLI，默认只选择无需必填 API Key 的渠道。

## 快速开始

```bash
python union_search_cli.py list --type groups --pretty
python union_search_cli.py search "人工智能" --group general --limit 3 --pretty
python union_search_cli.py search "人工智能" --group api --limit 3 --pretty
python union_search_cli.py search "人工智能" --platforms github wikipedia --limit 3 --pretty
```

`api` 会请求该组的全部服务，需事先配置对应凭据。只想调用部分服务时，使用 `--platforms`。

## 分组

| 分组 | 范围 | 凭据要求 |
| --- | --- | --- |
| `general` | 8 个网页渠道，未指定渠道时使用 | 无需必填 API Key |
| `no_api_key` | 26 个搜索渠道，含 GitHub、Wikipedia 等 | 无需必填 API Key |
| `api` | 23 个搜索渠道，含 AnySearch | 用户指定时使用；AnySearch 必填 `ANYSEARCH_API_KEY` |
| `ai_tools` | Claude Code、Codex、Grok Build | 用户指定时使用；需要本机客户端登录与账号额度 |
| `reference` | Wikipedia、WolframAlpha、DuckDuckGo 即时答案 | 无需必填 API Key |
| `community` | GitHub、Reddit | 无需必填 API Key，GitHub Token 可选 |
| `social` | YouTube、知乎开放平台、小宇宙 FM | 用户指定时使用；三个渠道都需要凭据 |
| `all` | 全部 52 个搜索渠道 | 包含需 API 和本机账号的渠道，不含正文提取工具 |
| `tools` | Defuddle | Node.js 依赖；使用 `defuddle <url>` 专用入口 |

注册表共有 53 项能力，包含 52 个搜索渠道与 1 个正文工具。默认网页分组依次为 `baidu_direct`、`so360_direct`、`sogou_direct`、`duckduckgo`、`brave`、`yahoo`、`yandex_direct`、`quark_direct`。

网页渠道由本项目独立实现，无外部项目运行依赖。360、搜狗、DuckDuckGo、Brave 和 Yahoo 使用 `curl_cffi>=0.16,<0.17`；Yandex 与 Quark 使用匿名访问。`duckduckgo_html`、`brave_direct`、`yahoo_direct` 保留为兼容入口并共用同服务实现。一次联合请求按来源去重，仅执行同服务的首个入口。

`bing`、`yandex` 通过 SerpAPI 访问，接受任一非空的 `SERPAPI_API_KEY*` 变量；`bing_cn_direct`、`bing_int_direct`、`yandex_direct` 使用网页入口。Yahoo 的 `yahoo_direct` 为 `yahoo` 的兼容名称，共用实现并按来源去重。

“无需 API”指无需配置必填 API Key；部分渠道仍调用匿名远程接口。不同访问方式计为独立条目。分组和 CLI 凭据检查共用 [platform_metadata.py](platform_metadata.py)，新增渠道时须同步核对认证要求。

TikHub 搜索接入与相关六个入口已移除。独立的 `zhihu_official` 不受影响。RSS、微信等独立模块不属于本编排器的分组。

## 参数与行为

- `--platforms` 优先于 `--group`；两者都不指定时使用 `general`。
- 默认不做本地条数截断；`--limit 0` 同样表示不限。正整数 `--limit` 是每渠道上限；`--preset small/medium/large/extra` 对应 3/5/10/20 条。
- 不限条数仅针对已取得的结果，上游请求批量、分页容量、模型输出窗口及超时保持有效，不自动无限翻页。
- 每次搜索都清洗、聚合和去重。相同规范 URL、相同标题和相似度达到 0.9 的标题合并为一条，`sources` 保留全部来源与原始排名。
- `final_items` 统一为 `id`、`title`、`url`、`content`、`published`、`thumbnail`、`sources`；清除文本中的 HTML 和多余空白。`channels` 单独提供状态、条数、耗时和简洁错误，`timing.wall_ms` 记录整批耗时。
- 网页子进程共享整批截止时间，排队时间计入预算，到期终止未完成子进程。
- 网页 HTTP 请求按 host 跨 CLI 共享最小两秒间隔，状态保存在已忽略的 `.work/web-search-state.sqlite`。429 遵守 `Retry-After`，未提供时冷却 300 秒；已识别验证码冷却 900 秒。冷却期明确报错，不发请求、不重试、不更换渠道。等待同样计入截止时间。
- 单渠道使用 `platform <名称> --param key=value` 传入 `page`、`timelimit`、`proxy`、`region`、`country`、`safesearch`，不支持的参数会失败。DuckDuckGo 网页仅支持 `page`，不支持 `timelimit` 或非 `wt-wt` 的 `region`。
- `--max-workers` 控制并发，`--timeout` 设置超时秒数。
- 默认输出 JSON；`--pretty` 调整缩进，`--format markdown|text` 切换格式，`-o` 保存文件。
- 统一 CLI 平台失败时，顶层 `ok` 为 `false`、`type` 为 `error`，默认仍退出 `0`；添加 `--fail-on-platform-error` 后退出 `4`。部分平台失败时信封保留 `data`，可读取成功渠道结果并检查失败渠道状态。参数错误退出 `2`，未分类的执行异常退出 `1`。
- 渠道失败不会自动选择其他服务。无结果可能源于关键词、网络、限流或解析器问题。

各渠道的常用参数、默认值、官方单次结果容量和输出字段见[搜索输出字段文档索引](../../references/output_fields.md)，详细分析保存在服务目录的 `output-analysis.md`。单次请求上限、模块分页累计与本地 `limit` 分别说明。

## 自动归档

所有 `union_search()` 调用在返回前自动归档到项目根目录 `output/<带微秒时间_查询安全名称_uuid>/`。统一 CLI 的 `search`、旧模块入口和直接 Python 调用都经过该函数；单渠道 `platform`、直接渠道命令及其别名也会保存归档。`output/` 自动加入 Git 忽略规则，`-o` 仍可额外导出文件。编排结果的 `archive`、统一 CLI 信封的 `data.archive` 提供 `search_id` 和 `directory`。

目录名称由开始时间（精确到微秒）、安全化并截取至 48 个字符的查询词语、UUID 的前 8 个十六进制字符组成；安全化后为空时使用 `search`。

| 文件 | 保存内容 |
| --- | --- |
| `metadata.json` | 带时区的起止时间、查询词语、渠道、参数、状态、数量、耗时、处理步骤及文件索引 |
| `raw_results.json` | 按渠道保存适配器返回、执行 `normalize_item` 前的条目 |
| `channel_results.json` | 各渠道完整记录，包括 `raw_items`、清洗后的 `items`、状态、数量、耗时和错误 |
| `final_results.json` | 清洗、聚合成功渠道并去重后的 `final_items`，没有语义精准筛选 |
| `result.json` | 包含归档索引的完整搜索数据 |

`raw_results` 的原始层次为适配器返回条目，字段可能已经经过渠道模块处理；原始 HTTP 响应仍按各渠道自身规则保存。失败且没有返回条目的渠道通过 `channel_results` 和 `metadata` 检查。

`metadata.status` 在全部渠道成功时为 `success`，部分渠道失败时为 `partial_failure`，全部渠道失败时为 `failed`。成功但没有结果仍属于成功状态。`processing` 记录 `normalize_fields`、`aggregate_successful_channels`、`deduplicate_url_and_title`。

## 历史查询

历史查询直接读取 `output/` 下的归档目录，不使用数据库：

```bash
python union_search_cli.py history list --pretty
python union_search_cli.py history list --query "人工智能" --platform github --status success --since 2026-10-01 --until 2026-10-25 --limit 0 --offset 0 --pretty
python union_search_cli.py history show <search_id> --section channel_results --pretty
```

`history list` 默认返回最近 20 条，按开始时间从新到旧排列。`--query` 对查询词语进行不区分大小写的子串匹配，`--platform` 筛选包含该渠道的记录，`--status` 接受 `success/partial_failure/failed`。`--since` 和 `--until` 使用 `YYYY-MM-DD`，按开始日期筛选且包含两端日期。`--limit 0` 表示不限，`--offset` 指定跳过条数；二者均须非负。

`history show <search_id>` 默认读取 `metadata`；`--section` 支持 `metadata|raw_results|channel_results|final_results|result`。完整返回字段见[输出字段说明](../../references/output_fields.md#自动归档的数据层次)，CLI 参数见[历史查询说明](../cli/README.md#自动归档与历史查询)。

## 旧模块入口

需要直接调用底层编排器时，从仓库根目录的 Bash 环境运行，并将 `scripts` 加入模块搜索路径：

```bash
PYTHONPATH=./scripts python -m union_search.union_search --list-platforms
PYTHONPATH=./scripts python -m union_search.union_search "人工智能" --group general --json --pretty
```

旧模块与统一 CLI 使用相同分组和默认范围，但输出格式不同。旧模块支持 `--json`；统一 CLI 的搜索命令默认输出 JSON，不接受 `--json`。统一 CLI 的 `defuddle --json` 是提取元数据选项。

## 正文提取与媒体候选

```bash
python union_search_cli.py defuddle https://example.com --json --pretty
python union_search_cli.py defuddle --url https://example.com --format markdown -o ./out/article.md
python union_search_cli.py search "AI agent" --platforms youtube --limit 3 -o ./out/search.json --pretty
python union_search_cli.py download --from-file ./out/search.json --select 1,2 --output-dir ./downloads --fail-on-download-error --pretty
```

Defuddle 需要 Node.js、根目录 npm 依赖，以及通过 `npm --prefix scripts/url_to_markdown/engines/defuddle-node ci` 安装的固定版本正式 npm 包。默认成功信封的 `data` 提供正文和标题等字段，`--json` 增加作者、发布日期、元标签等元数据；`--format markdown` 输出标题和正文。URL 同时通过位置参数与 `--url` 提供时，当前实现使用位置参数。提取失败返回 `PLATFORM_FAILURE`，退出码为 `4`。

成功搜索信封的 `data.download_candidates` 提供 `index`、`platform`、`title`、`url`，索引从 `1` 开始。`download --from-file` 优先读取这些候选；对已有候选应用 `--platforms` 筛选及 URL 去重后，会重新连续编号，再执行 `--select` 和 `--limit`，因此筛选后的索引可能改变。候选 URL 不保证能由 yt-dlp 下载。

媒体下载需要 PATH 中的 `yt-dlp`，音视频合并和音频提取需要 `ffmpeg`。`--output-dir` 默认 `downloads`，`-o/--output` 保存 CLI 结果文件；相对路径以当前工作目录为基准。`--dry-run` 仍访问网络、解析元数据并创建输出目录。成功结果的 `data.download_count` 为提交的 URL 数量；yt-dlp 失败时返回保留 `data` 的 `DOWNLOAD_FAILURE` 信封，默认退出 `0`，添加 `--fail-on-download-error` 后退出 `4`。详细参数与结果字段见[统一 CLI 的媒体任务契约](../cli/README.md#媒体任务契约)。

## 验证与文档

```bash
python -m unittest discover -s tests -p test_platform_groups.py -v
```

这些纯本地测试读取真实注册表，验证能力数量、凭据分区、默认分组成员及顺序、分组元数据和兼容入口的实现映射，不请求外部服务。

详见 [项目 README](../../README.md)、[统一 CLI](../cli/README.md) 和[凭据指南](../../references/api_credentials.md)。
