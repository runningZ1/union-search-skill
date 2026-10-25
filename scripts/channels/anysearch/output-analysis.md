# AnySearch 输出结果分析

覆盖 `anysearch_search.py` 的 `AnySearchClient.search`、`search_anysearch` 和 `--json`，以及 `union_search.py::_search_anysearch`。

## 结构与上游映射

服务成功条件为 HTTP 200 且顶层 `code == 0`；源码读取 `data.results[]` 和 `data.metadata`。这仅表示已知访问路径，不是服务完整响应结构。模块返回数组，脚本 JSON 包装为 `results`。

| 模块全部字段 | 类型、来源与缺失处理 |
| --- | --- |
| title | string；原条目 title，空值改用 url，去除两端空白 |
| href | string；url 去除空白；空地址条目丢弃 |
| body | string；优先 snippet，否则 content 前 300 字符 |
| engine | string；固定 anysearch |
| content | string；content，缺失或 null 变为空字符串 |
| score、quality_score | 原值或 null；分别来自同名字段；实测均为 null |
| source、published_at | 通常 string；同名字段，假值变为空字符串 |
| total_results、search_time_ms | metadata 同名字段；缺失为 null，实测 integer |

`score` 与 `quality_score` 没有转换或范围校验，源码无法证明二者的尺度、方向及跨查询可比性。日期同样没有解析或时区校验。元数据被复制进每条结果，空结果时无法通过模块输出取得元数据。

## 模块与 CLI 的保留边界

模块先对原数组执行 `[:max_results]`，再丢弃空 url，因此返回数量可能小于请求上限。上游未列出的条目字段、顶层状态和未映射 metadata 不保留。`_search_anysearch` 取模块 `results` 并再次限量，条目字段原样进入统一 CLI：单渠道为 `data.items[]`，联合搜索为 `data.results.anysearch.items[]`；联合 `data.final_items[]` 增加 `_source_platform`。外层 `ok/errors/meta` 表示调用状态，不属于服务数据。

## 容量概览

| 官方每请求上限 | 模块默认 | 分页行为 | `--limit` 作用 |
| --- | --- | --- | --- |
| 10 条 | `max_results=None` 时请求 10 条 | 官方未公布分页参数；模块只请求一次 | 不指定或 0 不额外截断；正数发送为 `max_results` 并本地切片，超过 10 可能不符合官方范围 |

本地样例：[examples/search-result.json](examples/search-result.json)。此文件保存真实 CLI 成功渠道对象，非原始 HTTP 响应。

## 常用参数与单次容量

核查日期：2026-10-25。官方来源：[Search API](https://anysearch.com/docs/api-endpoints/v1-search)。

| 英文参数 | 含义、默认与范围 |
| --- | --- |
| `query` | 搜索文本，模块要求非空 |
| `max_results` | 官方默认 10、范围 1—10；模块默认 `None` 时实际发送 10，显式值直接发送，未在本地校验官方范围 |
| `zone` | 区域，可选 `cn`、`intl`；模块默认不发送 |
| `domains`、`tags`、`content_types` | 模块可发送的列表，默认不发送；当前官方页面未确认这些字段；官方公布的是单值 `tag` |
| `freshness` → `constraint.freshness` | 模块接受 `day/week/month/year`，默认不发送；本次官方页面未确认该字段 |
| `timeout` | 模块 HTTP 超时，默认 30 秒，不是服务数量参数 |

官方单次结果上限为 10；统一 CLI `--limit` 默认不指定，或以 0 表示不额外限制，仍只发起一次搜索并遵守上游容量。指定正数时通过模块发送同值 `max_results`，随后模块与 adapter 本地切片；大于 10 不会自动分页，可能不符合官方参数范围。官方未公布分页参数。实际请求数与最终保留数量须分别读取请求体和输出，空地址过滤也会减少保留条数。

## 证据范围

依据本目录源码、对应 adapter 和 `.work/output-analysis/api.json` 的真实三条结果；字符串字段及两个整数元数据已观察，两个分数字段仅观察到 null。该文件是处理后的 CLI 输出，不能还原完整原始 JSON；其他查询、非空分数、垂直领域和时间限制未验证。
