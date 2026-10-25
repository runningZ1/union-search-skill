# Kimi 输出结果分析

覆盖 `kimi_search.py` 的 `KimiSearchClient.search`、便捷函数、JSON 脚本入口和 `union_search.py::_search_kimi`。入口分为 `/tools/search` 与 `/tools/search_pro`，模块字段集合相同，正文来源处理兼容两种返回。

## 原始路径与完整模块字段

源码要求服务顶层 `search_results` 为数组；以下为读取路径及转换结构，不表示原始完整响应。

| 模块字段 | 类型、映射及缺失规则 |
| --- | --- |
| title | string；title 或 url，去除空白 |
| href | string；url 去除空白，空地址条目跳过 |
| body | string；优先将 chunks 中 object 的非空 text 去除空白后以换行连接，否则取 content、snippet、空字符串 |
| engine | string；固定 kimi |
| site_name | 通常 string；同名字段，假值转为空字符串 |
| publish_date | 通常 string；原 date，假值转为空字符串 |
| tier | string；本次实际选择的 search 或 search_pro，来自请求配置 |

`chunks` 的分块边界、其他分块字段及原 content/snippet 的分别取值没有保留；body 是合并后的文本。include_content 仅在基础 search 请求中发送，search_pro 不发送这个参数。日期没有解析，也未提供可靠的时区或粒度契约。输出没有相关性分数，不能用 tier 推断单条结果质量。

## 模块和统一 CLI

请求 limit 限定在 1—20，模块再对原列表切片后过滤空 url；缺失标题用地址补充。HTTP 非 200 或 search_results 非数组会失败；正常空数组返回空结果。未映射的条目和顶层字段均丢弃。脚本 `--json` 输出 `results` 对象，便捷函数返回数组。

adapter 读取 `results`，按 limit 再切片，保留七个字段。单渠道 CLI 为 `data.items[]`，联合搜索为 `data.results.kimi.items[]`；联合 `data.final_items[]` 增加 `_source_platform`。外层 ok/errors 是统一执行状态。

## 容量概览

| 官方每请求上限 | 模块默认 | 分页行为 | `--limit` 作用 |
| --- | --- | --- | --- |
| search 与 search_pro 均为 20 条 | `max_results=None` 时请求 20 条；官方默认 5 条 | 模块无自动分页 | 不指定或 0 时仍请求 20；正数限制到 1—20 后发送为 `limit`，模块与 adapter 再本地切片 |

本地样例：[examples/search-result.json](examples/search-result.json)。此文件保存真实 CLI 成功渠道对象，非原始 HTTP 响应。

## 常用参数与单次容量

核查日期：2026-10-25。官方来源：[Web Search 最佳实践](https://platform.kimi.com/docs/guide/best-practices-for-web-search)。以下针对独立搜索 API。

| 英文参数 | 含义、默认与范围 |
| --- | --- |
| `query` → `text_query` | 非空查询，基础搜索不自动改写或扩展 |
| `tier` | 模块默认 `search`，环境可覆盖；可选 `search/search_pro` |
| `max_results` → `limit` | 官方两种接口均默认 5、范围 1—20；模块默认 `None` 时发送 20，显式值限制到 1—20 |
| `include_content` | 基础接口是否返回正文，模块与官方默认 false；Pro 不发送此字段 |
| `sites` | 模块默认不发送、最多 5 个；官方在 Pro 中说明最多 5 个站点，使用 OR |
| `start/end` → `time_window` | 模块默认不发送；官方在 Pro 中说明可用 `YYYY/YYYY-MM/YYYY-MM-DD` |
| `timeout` → `timeout_seconds` | 模块默认 30 秒，HTTP 超时为该值加 5 秒；官方范围 1—60，未确认服务默认 |

官方每次最多 20 条。基础接口的站点与时间筛选支持情况在当前官方页面未确认，模块仍允许构造这些字段。统一 CLI `--limit` 默认不指定、0 表示不额外截断，此时实际请求 20；正数限制到 20 后发送，模块与 adapter 再按原数量本地切片并过滤空地址。没有自动分页，输出数量可能少于请求值。

## 证据范围

已读取源码、adapter 及 `.work/output-analysis/api.json` 三条成功条目，全部七个字段实测为 string。该证据是模块处理后的输出，不能确认本次 body 究竟取自 chunks、content 或 snippet，也不能恢复上游分块结构；专业搜索、正文选项、站点与时间窗口未独立验证。
