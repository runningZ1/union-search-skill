# 智谱输出结果分析

覆盖 `zhipu_search.py` 的客户端、便捷函数、JSON 入口及 `union_search.py::_search_zhipu`。同一入口支持 search_std、search_pro、search_pro_sogou、search_pro_quark，当前映射读取相同字段。

## 服务路径与模块全部字段

源码访问顶层 `search_result[]`、`search_intent[0].keywords`、`request_id` 或 `id`，不构成服务完整 JSON 声明。

| 模块字段 | 类型、映射与缺失规则 |
| --- | --- |
| title | string；原 title 或 link，去除空白 |
| href | string；原 link，空地址跳过 |
| body | string；原 content，假值转为空字符串，去除空白 |
| engine | string；固定 zhipu |
| media、publish_date | 通常 string；原同名字段，假值转为空字符串 |
| refer | 原值或 null；上游 refer，实测 string |
| keywords | 通常 string；仅首条意图中的 keywords，缺失或假值为空字符串 |
| request_id | 原值或 null；顶层 request_id 优先，其次 id，实测 string |

keywords 和 request_id 被重复放入每个条目；空结果时这两项也随之无法获得。refer 是引用标记，没有代码证据证明它是分数或顺序编号。日期未解析，输出没有相关性数值。意图数组剩余元素和每条意图其他字段均未保留。

## 正常空值与 CLI 边界

非 200、顶层非空 error 或非数组 search_result 会报错。模块先切片再过滤空链接，标题缺失以链接补充。搜狗请求 count 调整到 10、20、30、40、50 中最接近的档位，最终模块仍按 max_results 切片；实际条数可以更少。脚本 `--json` 输出 `results` 对象，其他上游元数据丢弃。

adapter 保留全部九个条目字段，进入单渠道 `data.items[]` 或联合搜索 `data.results.zhipu.items[]`；联合 `data.final_items[]` 追加 `_source_platform`。外层 ok/errors 与渠道 total 属于统一执行信息。

## 容量概览

| 官方每请求上限 | 模块默认 | 分页行为 | `--limit` 作用 |
| --- | --- | --- | --- |
| std/pro 50 条；sogou 档位最高 50，同时设置域名与时间筛选时 count 被忽略；quark 上限未知 | 请求 `count=10`，引擎默认 search_std，可由环境覆盖 | 模块无自动分页 | 不指定或 0 时请求 10；正数限制到 1—50，sogou 取最接近的十条档位，再按原 limit 本地切片 |

本地样例：[examples/search-result.json](examples/search-result.json)。此文件保存真实 CLI 成功渠道对象，非原始 HTTP 响应。

## 常用参数与单次容量

核查日期：2026-10-25。官方来源：[网络搜索 API](https://docs.bigmodel.cn/api-reference/工具-api/网络搜索)。

| 英文参数 | 含义、默认与范围 |
| --- | --- |
| `query` → `search_query` | 官方最多 70 字符，模块也检查该长度和非空 |
| `search_engine` | 模块默认 `search_std`，另可选 `search_pro/search_pro_sogou/search_pro_quark`，环境可覆盖 |
| `max_results` → `count` | 官方通用 schema 默认 10、范围 1—50；描述明确支持 std/pro/sogou，未确认 quark 支持。模块默认请求 10，显式值限制到 1—50 |
| `domain` → `search_domain_filter` | 指定域名，默认不发送 |
| `recency` → `search_recency_filter` | 官方默认 `noLimit`；可选 `oneDay/oneWeek/oneMonth/oneYear/noLimit`，模块默认不发送 |
| `content_size` | `medium/high` 控制摘要内容量，模块默认不发送，官方默认未明确 |
| `search_intent` | 官方与模块默认 false，true 时先识别意图 |

官方 std/pro 单次最多 50；sogou 仅接受 10、20、30、40、50，且同时设置域名与时间筛选时官方说明 count 被忽略，因此不能保证该组合按 count 返回。模块为 sogou 选择最接近的数量档位，例如 limit=14 请求 10，最终可能少于 14。quark 的单次上限本次未确认，不能直接套用通用 50。统一 CLI `--limit` 默认不指定、0 表示不额外截断，此时实际请求 10；正数用于构造 count 并在模块与 adapter 本地切片，没有自动分页。

## 证据范围

源码、adapter 和 `.work/output-analysis/api.json` 已核对，三条结果成功，列出的模块字段实测均为 string。未保存服务原始响应，不能证明 refer、request_id 的其他类型契约；其他搜索引擎、意图开启、时间和域名条件未分别实测。
