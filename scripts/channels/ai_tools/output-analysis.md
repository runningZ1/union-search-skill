# AI Tools 输出结果分析

## 容量表与结果留样

| 官方单次上限 | 模块默认 | 分页 | `limit` 作用 |
| --- | --- | --- | --- |
| 三个账号后端均未确认固定条数承诺，不能套用其他公开 API 的上限 | `limit=None`，不做本地数量截取；实际受后端返回、去重、工具轮次与超时影响 | 无页码或游标遍历；Claude/Grok 一次运行可调用多轮工具，无固定轮次数量保证 | Claude/Grok 同时写入提示词并本地截取；Codex 仅去重后本地截取；外层再次截取，`0` 为不限本地条数 |

真实结果见 [Codex 主样例](examples/search-result.json)、[Claude Code 样例](examples/search-result-claude_code.json) 和 [Grok Build 样例](examples/search-result-grok_build.json)。三个文件分别保存统一 CLI 的 `data.results.codex`、`data.results.claude_code`、`data.results.grok_build` 渠道对象，属于 CLI 渠道对象证据层；未保存原始 HTTP 响应或原生 CLI 事件流。每个样例的 3 条结果用于核对字段，容量依据下文已有资料与实现。

## 常用参数与返回数量

资料整理日期：2026-10-25。参数依据 `adapter.py`、`worker.py` 和 `native_search/backends/`；此次补充仅阅读实现与联网核对资料，沿用下文既有样本，没有重新执行渠道搜索。

| 参数 | 含义 | 默认值或未指定行为 | 范围与实际约束 |
| --- | --- | --- | --- |
| 渠道 / `platform` | 选择账号后端 | 需显式选择渠道或 `ai_tools` 分组 | `claude_code`、`codex`、`grok_build`；分组分别调用三个后端 |
| `query` | 搜索关键词 | 必填 | 非空字符串 |
| 统一 `--limit` / 适配器 `limit` | 每个渠道最多保留的条目数 | 未指定为 `None`；`0` 同样转换为不限本地条数 | 正整数或 `0`；适配器拒绝负数、布尔值及其他类型，没有固定数字上限 |
| `--param recency_days=N` | 最近若干天 | `None`，不附加时间条件 | 转换后必须为正整数；Claude/Grok 写入提示词，Codex 请求使用 `recency` |
| `--param domains=a.com,b.com` | 域名条件 | `None`，不附加域名条件 | 逗号分隔字符串或非空字符串元素列表；Claude/Grok 提示词表达为优先这些域名，Codex 传入 `domains`；不保证三者过滤强度相同 |
| 适配器 `timeout` | worker 和子进程的运行期限 | 直接调用适配器为 `180` 秒 | 必须大于零；统一 CLI 的 `--timeout` 还控制调用等待期限，不能据此增加结果数量 |
| `CLAUDE_SEARCH_MODEL` / `GROK_MODEL` | 原生 CLI 模型 | 分别为 `haiku`、`grok-4.5` | 具体可用模型由账号与客户端决定 |

**官方每请求条数上限：三个账号后端均未确认固定承诺。** Claude Code、Grok Build 的公开 CLI 文档没有给出这里所用原生搜索工具的固定返回条数；Codex 使用 `chatgpt.com/backend-api/codex/alpha/search`，公开 Codex CLI 文档没有为此内部端点提供稳定的数量契约。不能套用 Anthropic、OpenAI 或 xAI 的其他公开搜索 API 参数与上限。

Claude/Grok 在提示词中请求最多 N 条，然后去重、切片；Codex 的 N 只用于本地 `_hits` 去重后切片，没有发送官方 `count/max_results` 参数。外层适配器再次执行 `results[:limit]`。因此统一 `--limit N` 是最终数量上限，无法保证上游取得 N 条，也不能解释成一次原生工具请求的条数。

模块每次调用所选后端，没有按页码或游标自动遍历结果；Claude/Grok 在一次运行中可能调用多轮工具，这种模型行为没有固定分页数量保证。不指定 limit 只取消本地切片上限，仍受账号额度、搜索覆盖、模型输出长度、工具轮次、去重与超时影响。本实现没有固定总条数上限，也没有完整取回所有命中的承诺。

官方来源（资料整理日期：2026-10-25）：[Claude Code CLI 参数](https://code.claude.com/docs/en/cli-reference)、[Codex CLI 与 ChatGPT 登录](https://learn.chatgpt.com/docs/codex/cli)、[Grok Build CLI](https://docs.x.ai/build/overview)。这些入口用于核对实际客户端，不作为内部搜索端点条数保证。

## 依据、环境与真实验证

依据 `adapter.py`、`worker.py`、`native_search/backends/{claude,codex,grok,cli_json}.py`、`native_search/textutil.py`，以及统一搜索与 CLI 的输出实现。本文只分析输出格式、字段类型、可空性、来源映射和 CLI 保留。

运行前确认 Python 3.12.4、Node.js v22.23.2，以及 `requests`、`python-dotenv`、`yt-dlp` 和三个本地 CLI 可用。统一 CLI 的 `doctor --platforms claude_code codex grok_build` 返回三个本地认证检查通过；这项检查自身不验证远端搜索。没有安装依赖或手动修改认证，也没有读取 `.env` 值；环境文件由现有 CLI 自行加载。运行时临时目录通过 `TEMP/TMP/TMPDIR` 指向根目录 `.work/output-analysis/runtime`。

本次真实搜索命令从项目根目录执行：

```text
python scripts/union_search_cli.py search "sustainable clothing circular fashion textile recycling" --group ai_tools --limit 3 --timeout 180 --max-workers 3 --pretty --output .work/output-analysis/ai-tools.json
```

结果保存于根目录 `.work/output-analysis/ai-tools.json`。顶层 `ok=true`、`errors=[]`，`summary.successful=3`、`failed=0`、`total_items=9`。三个后端均为 `status="success"`、`total=3`、`has_results=true`，整体约 34.8 秒。此次只验证搜索路径，没有执行 fetch/research，也没有另存原生事件流。以下原生事件结构来自实现阅读，不能把适配后的 JSON 当作原生完整响应。

| CLI 渠道名 | 条目 `backend` | 本次条目字段 | 渠道耗时 |
| --- | --- | --- | --- |
| `claude_code` | `"claude"` | `title/url/snippet/backend/untrusted` | 23264 ms |
| `codex` | `"codex"` | `title/url/snippet/ref_id/backend/untrusted` | 5139 ms |
| `grok_build` | `"grok"` | `title/url/snippet/published_at/backend/untrusted` | 34514 ms |

这些成功状态说明现有搜索与输出校验通过，未独立访问九个来源核验正文和日期。

## 原生响应层与结构化结果层

| 后端 | 原生输出来源 | 实现读取的事件或字段 | 进入适配结果的范围 |
| --- | --- | --- | --- |
| Claude | 本地 CLI，`--output-format stream-json --verbose --json-schema ...` | JSON 事件中递归查找 `type="tool_use"` 或 `"server_tool_use"`，且 `name="WebSearch"`；结构化结果读取方式见下文 | 最后一个合法的结构化 `results` 数组 |
| Grok | 本地 CLI，`--output-format streaming-messages-json`，提示词中附 JSON schema | 同样查找工具事件，搜索要求 `name="web_search"`；虽然 CLI 也开放 `web_fetch`，单有抓取事件不满足搜索工具证据要求 | 最后一个合法的结构化 `results` 数组 |
| Codex | HTTP 请求返回的 JSON 对象 | 顶层 `results` 中的结果对象，以及可选 `output` 文本 | `_hits` 重新构造的结果数组 |

Claude/Grok 的解析器从输出中逐个解码 JSON 对象，支持以下候选路径：

- 事件的 `structured_output` 或 `structuredOutput` 对象。
- 本身符合结果形状的 JSON 对象，即顶层具有 `results` 数组。
- 事件的字符串 `result` 或 `text` 中嵌入的合法 JSON 对象。

候选按读取顺序收集并取最后一个。搜索结果的基本形状要求每条为对象，且 `title/url/snippet` 都是字符串。事件的 `is_error` 为真时会使解析失败。工具事件仅验证原生工具被调用；其 `input`、工具响应正文、调用标识等不会自动映射到结果条目。

`SEARCH_SCHEMA` 要求顶层只有 `results`，条目必需 `title/url/snippet`，可选 `published_at:string`，不声明额外属性。Claude 将 schema 作为 CLI 参数，Grok 将其加入提示词。Python 本地 `_valid` 只验证基本结果字段，并未完整执行 schema 的额外字段和日期约束。因此 schema 声明与本地实际校验强度需要分别理解；额外条目字段若通过上游返回，可以被后续路径原样保留。

Codex 当前搜索路径没有解析上述 CLI 事件流，也没有把工具事件写入输出。它读取 HTTP JSON 响应；不能将 `ref_id` 解释为 Claude/Grok 工具调用标识。

## 搜索条目字段与来源映射

| 字段 | 类型、可空性 | Claude / Grok 来源 | Codex 来源 |
| --- | --- | --- | --- |
| `title` | 必需 `string`，允许空字符串；不允许 `null` | 模型在结构化结果中提供的 `title`，后续不改名 | 依次取原生 `title/name` 中首个非空字符串并去除两端空白；没有时取 URL 域名 |
| `url` | 必需 `string`；worker 要求为具有主机名的 HTTP(S) 地址 | 结构化结果 `url` | 依次取 `url/link/href` 中首个非空字符串并去除两端空白 |
| `snippet` | 必需 `string`，可为空；不允许 `null` | 结构化结果 `snippet`；提示词要求引用原文短句，但没有逐句来源核验字段 | 依次取 `snippet/text/content/description` 中首个非空字符串并去除两端空白；没有时 `""` |
| `published_at` | schema 可选 `string`；缺失时不补值；日期格式未验证 | 结构化条目中的同名字段；本地未单独校验其类型，因此显式 `null` 也可能透传 | `_hits` 没有映射此字段 |
| `ref_id` | 可选非空 `string`；缺失时不补值 | schema 未声明；当前实现不专门生成 | 依次取原生 `ref_id/ref` 中首个非空字符串 |
| `backend` | 必需 `string`，非空、非 `null` | 外层适配器按渠道写入 `"claude"` 或 `"grok"` | 外层适配器写入 `"codex"` |
| `untrusted` | 必需 `boolean`，固定为 `true` | 外层适配器写入 | 外层适配器写入 |

Claude/Grok 的结构化输出是模型在搜索之后组织的结果，不是工具原始结果逐字段透传。`published_at` 没有来自原生事件时间的自动映射。本次 Claude 三条均未出现该字段；Grok 三条均出现字符串，分别为 `2026-10-19`、`2024-09-03`、`2026-08-24`。本次 Codex 三条 `ref_id` 为 `turn0search0/turn0search1/turn0search2`，未出现 `published_at`。

Codex 若没有构造出结构化条目，实现还会从 `output` 的 Markdown 链接构造 `title/url/snippet`，其中 `snippet=""`，不生成 `ref_id`。本次成功条目均有 `ref_id`，没有验证该文本派生分支。Codex 重新构造条目时，不保留未映射的原生字段，例如其他来源时间或远端附加元数据。

## 后端、worker 与渠道适配的容器变化

后端 `search` 返回 `{results:array<object>, backend:string, untrusted:true}`。worker 验证后端一致性、数组及三项基本字符串字段、URL 形状，返回 `{ok:true,backend,results,untrusted:true}`。失败时 worker 只返回 `{ok:false,error:string}`，错误文字使用异常类型与状态码描述，避免直接输出上游 CLI 或认证响应正文。

外层 `adapter.search` 将 worker 容器转换成条目数组，并在每个条目上写入 `backend/untrusted`。worker 顶层 `ok` 不作为业务条目字段保留；它控制外层是否报错。后端级元数据没有独立加入最终渠道对象。

正常返回结果的条目 `title/url/snippet` 必然存在且为字符串。`url` 不允许为空或 `null`；`title/snippet` 可以为空。可选字段的缺失与 `null` 不等价，适配器没有把缺失 `published_at/ref_id` 自动填为 `null`。这些渠道没有额外生成统一网页条目的 `content/published/thumbnail/sources` 字段。

## 统一 CLI 的保留范围

联合搜索的 `data.results.<渠道>` 包含：

| 字段 | 类型与含义 |
| --- | --- |
| `platform`、`keyword` | `string`，CLI 渠道名和查询 |
| `success` | `boolean`，渠道执行是否成功 |
| `error` | 正常为 `null`，失败为 `string` |
| `items` | `array<object>`，保留搜索条目及可选字段 |
| `total` | `integer`，实际条目数量 |
| `timestamp` | `string`，本地创建渠道对象的时间文本 |
| `timing_ms` | `integer`，渠道耗时 |
| `has_results` | 成功执行时写入 `boolean`；失败分支可能缺失 |
| `status` | 正常渠道对象为 `"success"/"empty"/"failed"`；联合超时等特殊失败对象可能缺失 |
| `warning` | 空结果时可选 `string` |
| `error_details` | 普通失败时可选 `object`，含错误分类等字段 |

本次全部渠道 `error=null`，没有验证失败、空结果或超时响应。失败结构以上述实现为依据；联合层特殊失败对象可能省略 `keyword/timestamp/has_results/status/error_details`，消费方不能把正常分支的全部字段视为失败分支必需字段。

`data.final_items` 复制成功条目并增加 `_source_platform:string`。本次分别为 `claude_code/codex/grok_build`，它与条目 `backend` 的命名有所区别。数组按选定渠道顺序聚合；`data.results` 的键写入顺序由完成时间决定，不能依赖两个位置的排列一致。所有条目字段，包括 Codex 的 `ref_id`、Grok 的 `published_at`，均在本次 `final_items` 保留。

联合容器还包含 `keyword/platforms/limit_per_platform/timestamp/results/summary/final_items/timing/channels`。`summary` 的计数为 `integer`，`deduplicate_enabled` 为 `boolean`；本次关闭跨渠道去重，`raw_total_items=deduplicated_total_items=9`。`channels` 每条包含 `platform/status/count/duration_ms/error`，本次错误均为 `null`。

CLI 适配器追加 `adapter_timing_ms:integer`、`download_candidates:array<object>`，并在 `summary` 加入 `downloadable_items`。本次九个候选对象含 `index:integer`、`platform/title/url:string`，是下载候选视图，不包含 `snippet/ref_id/published_at/backend/untrusted`，完整信息保存在 `items/final_items`。候选数量表示识别出的地址数量，没有执行媒体下载。

顶层信封包含 `schema_version:string`、`ok:boolean`、`type:string`、`success:boolean`、`command:string`、`query:string|null`、`timestamp:string`、`duration_ms:integer`、`errors:array<object>`、`meta:object` 和可选 `data`；失败时增加 `error:object`。任一渠道失败会使联合搜索顶层 `ok=false`，仍保留成功渠道数据，进程退出码还受错误退出选项控制。统一 CLI 的搜索 JSON、text、Markdown 输出均保留完整信封字段，Markdown 使用 JSON 代码块。

## 同模块其他返回形状的边界

代码中存在未接入当前 worker 搜索入口的 `fetch`，以及 Codex `research`：

| 方法 | 实现返回形状 |
| --- | --- |
| Claude/Grok `fetch` | `title/url/markdown:string`、`truncated:boolean`、`backend:string`、`untrusted:true`；标题或 URL 为空值时使用域名或请求 URL |
| Codex `fetch` | `title` 来自请求域名，`url` 为请求地址，`markdown` 来自原生 `output`，另有 `truncated/backend/untrusted` |
| Codex `research` | `brief:string`、`sources:array<object>`、`backend:"codex"`、`untrusted:true`，`sources` 使用搜索条目映射 |

worker 只接受 `check/search`，统一 CLI 的 ai_tools 搜索不会输出 `markdown/truncated/brief/sources`。这些字段仅由当前代码说明，未经本次实际调用验证。
