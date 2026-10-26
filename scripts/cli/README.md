# Unified CLI

统一 CLI 入口：

```bash
python union_search_cli.py <command> [options]
```

也可直接运行：

```bash
python scripts/cli/main.py <command> [options]
```

## Commands

- `search`: 多平台聚合搜索
- `platform`: 单平台搜索
- `image`: 多平台图片搜索/下载
- `download`: 使用 yt-dlp 下载视频/音频（支持从搜索结果文件导入）
- `list`: 列出平台、分组和图片平台
- `schema`: 输出机器可读的能力描述（命令、平台、限额、错误码）
- `errors`: 输出错误码与退出码注册表
- `doctor`: 环境变量和依赖检查
- `defuddle`: 从 URL 提取网页正文为 Markdown，可附带元数据

## Examples

```bash
python union_search_cli.py list --pretty
python union_search_cli.py doctor --env-file .env --pretty
python union_search_cli.py search "LLM" --platforms github duckduckgo --limit 3 --pretty
python union_search_cli.py platform tavily "AI news" --limit 5 --pretty
python union_search_cli.py google "AI news" --limit 5 --pretty
python union_search_cli.py bing "AI news" --limit 5 --pretty
python union_search_cli.py bsearch "AI news" --limit 5 --pretty
python union_search_cli.py search "AI agent" --platforms youtube --limit 3 -o ./out/search.json --pretty
python union_search_cli.py image "cat" --platforms pixabay --limit 5 --output-dir ./search_output/images --pretty
python union_search_cli.py download "https://www.youtube.com/watch?v=dQw4w9WgXcQ" --max-height 1080 --output-dir ./downloads --pretty
python union_search_cli.py download "https://youtu.be/Zh9IscszDQg" --cookies-file C:/path/cookies.txt --restrict-filenames --continue-download --pretty
python union_search_cli.py download --from-file ./out/search.json --platforms youtube --select 1,2 --output-dir ./downloads --pretty
```

## 机器契约

默认 `--format json` 输出一个 JSON 信封，诊断信息走 stderr。`--format markdown|text` 切换呈现格式；`--help` 和 `--version` 输出普通文本。使用 `-o/--output` 时，结果写入指定文件，文件路径写入 stderr。`image` 和 `download` 的 `--output-dir` 设置下载目录，分别默认为 `image_downloads` 和 `downloads`，与结果文件参数独立；相对路径以当前工作目录为基准。

```json
{"schema_version": "1.0", "ok": true, "type": "result", "data": {}, "meta": {"request_id": "req_...", "duration_ms": 42}}
```

成功时 `data` 包含结果；失败时 `ok` 为 `false`，`type` 为 `error`，并带 `error` 对象：`code`、`message`、`retryable`、`outcome`、`details`、`next_actions`。部分平台失败时信封保留 `data`，调用方可读取成功渠道的结果并检查失败渠道。`success`、`command`、`query`、`errors` 字段保留。

退出码：`0` 正常完成，`1` 内部错误，`2` 参数或用法错误，`3` 缺少依赖或资源，`4` 超时、限流或服务暂不可用，`130` 被中断。错误码注册表可用 `python union_search_cli.py errors --pretty` 查看；实际退出码还取决于命令的失败选项：

- `search`、`platform` 和直接渠道命令的渠道失败默认退出 `0`，指定 `--fail-on-platform-error` 后退出 `4`。
- `download` 的 yt-dlp 非零退出默认仍让 CLI 退出 `0`，指定 `--fail-on-download-error` 后退出 `4`。
- `image` 收到平台失败汇总时退出 `0`，没有对应的失败退出选项；`defuddle` 提取失败退出 `4`。
- 参数解析失败退出 `2`；适配器执行异常、子进程异常及未分类的依赖错误可能归为 `INTERNAL_ERROR` 并退出 `1`。不能根据错误注册表推断所有依赖问题都退出 `3`。

通用网页搜索的 `data.final_items` 使用统一字段：`id`、`title`、`url`、`content`、`published`、`thumbnail`、`sources`。`sources` 保留 `platform`、`engine`、`rank`；按 URL 去重时合并来源。`data.channels` 分离渠道状态、结果数、耗时和分类错误；`data.timing` 使用毫秒并记录整批截止时间。

网页请求跨 CLI 按 host 保持至少两秒间隔。429 按 `Retry-After` 冷却，缺失时为 300 秒；验证码为 900 秒。状态保存在 `.work/web-search-state.sqlite`。冷却期返回 `COOLDOWN`，不会自动重试或切换来源；等待计入搜索截止时间。

自动化调用须同时检查退出码与顶层 `ok`；退出 `0` 不保证所有平台或媒体下载成功。

全局旗标 `--quiet` 关闭 stderr 诊断，`--no-color` 关闭人类可读输出的颜色，两者写在子命令前后都生效。

## 分组与默认行为

注册表共有 52 项能力：51 个搜索渠道与 1 个正文提取工具。

- `general`、`search`、`preferred`：相同的 8 个网页渠道，依次为 `baidu_direct`、`so360_direct`、`sogou_direct`、`duckduckgo`、`brave`、`yahoo`、`yandex_direct`、`quark_direct`；`general` 为默认分组。
- `no_api_key`：25 个无需必填 API Key 的搜索渠道，包含上述网页渠道和 GitHub、Wikipedia 等渠道。
- `api`：23 个需要 API Key 的搜索渠道，按需显式选择；AnySearch 必须配置 `ANYSEARCH_API_KEY`。
- `bing`、`yandex` 为 SerpAPI 渠道，`doctor` 接受任一非空的 `SERPAPI_API_KEY*` 变量；对应网页直连入口使用 `bing_cn_direct`、`bing_int_direct`、`yandex_direct`。Yahoo 的 `yahoo` 和兼容名称 `yahoo_direct` 均无需 API Key，共用实现并按来源去重。
- `ai_tools`：三个本机账号渠道 `claude_code`、`codex`、`grok_build`，需 Python 3.10+、对应客户端登录和额度。参见 [AI 工具搜索](../channels/ai_tools/README.md)。
- `dev`、`social`：按内容用途筛选；`social` 的 YouTube、知乎开放平台、小宇宙均需 API。
- `all`：51 个搜索渠道，包含本机账号渠道，不含正文提取工具；`tools` 单列 Defuddle。
- TikHub 接入及其六个搜索入口已移除；知乎开放平台独立保留。

各服务的参数含义、模块默认值、官方单次结果上限、分页及本地截断方式见[搜索输出字段文档索引](../../references/output_fields.md)及对应服务目录的 `output-analysis.md`。`--limit 0` 只取消本地条数限制，服务容量和分页仍然有效。

## Notes

- 默认输出为 `json`，可用 `--format markdown|text` 切换。搜索、图片和媒体下载命令不接受 `--json`；`defuddle --json` 控制提取引擎返回的元数据，外层输出格式仍由 `--format` 控制。
- 搜索、单渠道、直接渠道别名、图片和下载候选默认不设置本地条数上限；`--limit 0` 表示不限，负数报参数错误。正整数上限和显式 `--preset` 继续有效。
- JSON 和文本输出保留信封全部字段；Markdown 通常将完整信封放入代码块，`defuddle` 的 Markdown 输出仅呈现标题和正文。API 请求批量、站点分页容量、模型输出窗口与超时保持有效；原生图片搜索返回本次单页有限结果，SDK 图片平台不限条数时请求 10,000 张，火山引擎每次最多 5 张。不自动穷尽上游所有分页。
- `search`/`platform` 支持 `--fail-on-platform-error`，平台失败时返回退出码 `4`。
- `platform` 支持重复传入 `--param key=value`；网页参数包括 `page`、`timelimit`、`proxy`、`region`、`country`、`safesearch`，具体支持范围由渠道决定，不支持时明确失败。DuckDuckGo 网页仅支持 `page`，不支持 `timelimit` 或非 `wt-wt` 的 `region`。
- 例如：`python union_search_cli.py platform duckduckgo "Python" --param page=2 --limit 3 --pretty`。
- `duckduckgo_html`、`brave_direct`、`yahoo_direct` 保留为兼容入口，与同服务渠道共用实现；一次联合请求按来源去重，仅执行同服务的首个入口，`--deduplicate` 单独控制结果去重。
- 网页渠道由本项目独立实现，无外部项目运行依赖。360、搜狗、DuckDuckGo、Brave、Yahoo 需要 `curl_cffi>=0.16,<0.17`；新增 `yandex_direct`、`quark_direct` 使用匿名访问。
- 单平台可直接使用平台名命令（例如 `google`, `bing`），等价于 `platform <name>`.

## 图片任务契约

```bash
python union_search_cli.py image "mountain landscape" --search-only --limit 5 --pretty
python union_search_cli.py image "mountain landscape" --platforms baidu bing wikicommons --limit 5 --output-dir ./images --pretty
python union_search_cli.py list --type images --pretty
```

图片平台共 24 个：12 个原生平台与 12 个保留的 SDK 平台。`image` 默认使用 `baidu bing wikicommons`，搜索后下载。`--search-only` 只返回搜索结果与元数据，仅支持原生平台，不支持的平台明确报错。`--platforms` 可显式选择保留的 SDK 平台。原生平台由本项目独立实现，平台失败时不自动切换到 SDK 或其他来源。

`--limit` 默认 `0`，保留本次取得的全部结果；原生搜索只返回本次单页的有限结果，不自动遍历全部分页。`--output-dir` 设置图片目录，`-o` 保存结果信封，`--no-metadata` 关闭平台目录的元数据文件。

每张图片的 `metadata` 为字典，统一包含 `title`、`image_url`、`source_url`、`thumbnail`、`width`、`height`、`author`、`license`、`image_variant`、`provider`、`id`、`file_path`、`download_status`。缺失字段为 `null`；纯搜索时 `file_path` 为空。`image_variant` 标明来源原始或最大可用版本，全部结果不保证都是来源原文件。

结果的 `data.items` 合并各平台的图片元数据列表；`data.summary.total_found` 表示找到的图片数量，`total_images` 表示下载数量，`search_only` 标明是否纯搜索。下载文件使用 Pillow `Image.verify()` 检查实际内容，并记录 `sha256` 与 `bytes`。单张图片下载失败时保留该图片的元数据、状态与错误；部分平台或图片失败时返回 `ok: false`、`PARTIAL_FAILURE`，信封保留 `data`。收到失败汇总时退出码仍为 `0`，调用方必须检查顶层状态与逐图片记录。

原生图片解析使用 `chompjs>=1.2`，文件校验使用 `Pillow>=12`；SDK 平台使用 `pyimagedl`。完整平台名单、独立脚本和结果目录见[图片模块说明](../union_image_search/README.md)。

## Defuddle 正文提取

```bash
python union_search_cli.py defuddle https://example.com --json --pretty
python union_search_cli.py defuddle --url https://example.com --format markdown -o ./out/article.md
```

需要 Node.js 和 npm 依赖。在根目录执行 `npm ci`，再执行 `npm --prefix scripts/url_to_markdown/engines/defuddle-node ci` 安装固定版本的正式 Defuddle 包。`--timeout` 默认 60 秒，应用于引擎的每次子进程调用。URL 可通过位置参数或 `--url` 提供；同时提供时，当前实现优先使用位置参数。`--debug` 可以解析，当前处理器未将其传给引擎。

默认成功结果的 `data` 包含 `url`、`title`、`content`、`markdown`、`description`、`domain` 和 `adapter_timing_ms`；`--json` 还返回 `favicon`、`image`、`author`、`published`、`meta_tags`。提取失败返回 `PLATFORM_FAILURE` 和退出码 `4`。

## 媒体任务契约

`download` 接收多个直接 URL，也可通过 `--from-file` 读取搜索结果 JSON；两种输入可以合并。成功搜索信封的 `data.download_candidates` 包含 `index`、`platform`、`title`、`url`，从 `1` 开始编号。读取文件时优先使用已有候选，也支持从 `results`、`final_items` 生成候选。

- `--platforms`、`--select` 和 `--limit` 只作用于文件候选。已有候选先按平台筛选、按 URL 去重，再从 `1` 连续编号；`--select 1,2` 使用这个编号，随后应用条数上限。加入平台筛选后，编号可能与原文件不同。
- 直接 URL 排在文件候选前面，合并后按 URL 去重并保持顺序。`--limit` 默认不限，`0` 表示不限，负数返回参数错误。
- 需要 PATH 中的 `yt-dlp`；音视频合并和音频提取需要 `ffmpeg`。默认目录为 `downloads`，yt-dlp 文件模板为 `%(uploader)s/%(title)s [%(id)s].%(ext)s`，默认禁用播放列表下载。
- `--audio-only` 提取音频，`--audio-format` 默认 `mp3`；`--media-format` 传递格式选择器，`--max-height` 传递分辨率排序偏好。`--restrict-filenames` 和 `--continue-download` 默认启用，可分别用 `--no-restrict-filenames`、`--no-continue-download` 关闭。
- `--cookies-file` 接收 Netscape 格式文件，`--cookies-from-browser` 指定浏览器。对 YouTube URL，未显式指定文件时依次检查 `YTDLP_COOKIES_FILE`、`~/.claude/skills/yt-dlp-skill/cookies/cookies.txt`、`~/.agents/skills/yt-dlp-skill/cookies/cookies.txt`，使用首个存在的文件。显式指定的文件不存在时，当前实现不会传递该文件，也不继续自动发现。
- `--retries`、`--fragment-retries`、`--retry-sleep` 和 `--proxy` 传给 yt-dlp；`--timeout` 默认 3600 秒。`--dry-run` 传递 `--simulate --skip-download`，仍会访问网络、解析媒体元数据并创建输出目录。

成功信封的 `data` 包含 `success`、`exit_code`、`command`、`output_dir`、`download_count`、`cookies_file_used`、`stdout`、`stderr`、`adapter_timing_ms`、`candidates` 和 `resolved_urls`。`download_count` 表示提交给 yt-dlp 的 URL 数量，不能据此认定文件已成功下载；`candidates` 仅记录文件候选，`resolved_urls` 记录全部合并去重后的 URL。

yt-dlp 返回非零退出码时，外层为 `DOWNLOAD_FAILURE` 错误信封，仍保留上述 `data` 供检查执行结果，默认 CLI 退出码为 `0`，使用 `--fail-on-download-error` 后为 `4`。缺少输入返回 `INVALID_ARGUMENT` 和退出码 `2`；文件读取、候选选择、空候选、缺少 yt-dlp 或下载超时等适配器异常当前返回 `INTERNAL_ERROR` 和退出码 `1`。
