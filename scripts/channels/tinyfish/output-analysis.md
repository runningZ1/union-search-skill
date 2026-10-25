# TinyFish 输出结果分析

覆盖 `tinyfish_search.py` 的客户端、`search_tinyfish`、JSON 入口和 `union_search.py::_search_tinyfish`。当前对搜索 endpoint 发起 GET，请求参数为 query 及可选 location、language；max_results 用于本地截取。

## 原始结构与完整模块字段

源码读取顶层 `results[]` 和 `total_results`，要求 results 为数组。以下为映射关系，不是服务完整响应结构。

| 模块字段 | 类型、映射与缺失规则 |
| --- | --- |
| title | string；原 title 或处理后的 url，去除两端空白 |
| href | string；原 url 去除空白；没有 scheme 时添加 https:// |
| body | string；原 snippet，缺失或 null 为空字符串 |
| engine | string；固定 tinyfish |
| site_name | 通常 string；原同名字段，假值为空字符串 |
| position | 原值，假值时使用从 1 开始的原列表位置；实测 integer |
| total_results | 顶层同名字段，缺失为 null；实测 integer |

url 为空时跳过该条目；补充 scheme 之后没有进一步规范化域名、清理参数或校验目标网页。position 取上游值或顺序位置，不是相关性分数。total_results 是上游总量元数据，复制到每条结果；它与模块保留数量、统一 CLI 的 total 具有不同含义。输出不包含日期与正文。

## 缺失和保留边界

模块先切片再过滤地址，因此实际结果可以少于 max_results；该数量不会发送到服务。title 缺失可保留链接作为标题，snippet 缺失可保留空 body。非 200 或缺少数组 results 直接报错。其他上游字段和顶层元数据未映射，空结果时 total_results 无法通过条目获得。

脚本 `--json` 包装为 results；adapter 读取并再次限量，七个条目字段原样进入单渠道 `data.items[]` 或联合 `data.results.tinyfish.items[]`。联合 `data.final_items[]` 加入 `_source_platform`，外层 ok/errors 表示统一执行状态。

## 容量概览

| 官方每请求上限 | 模块默认 | 分页行为 | `--limit` 作用 |
| --- | --- | --- | --- |
| 未知；官方示例条数不能证明容量 | `max_results=None`，不发送数量参数，不额外切片 | 官方未说明请求分页参数；模块无自动分页或补充请求 | 不指定或 0 不额外截断；正数仅本地切片，不改变请求数量 |

本地样例：[examples/search-result.json](examples/search-result.json)。此文件保存真实 CLI 成功渠道对象，非原始 HTTP 响应。

## 常用参数与单次容量

核查日期：2026-10-25。官方来源：[Search API](https://docs.tinyfish.ai/search-api)。

| 英文参数 | 含义、默认与范围 |
| --- | --- |
| `query` | GET 查询文本，模块要求非空 |
| `location`、`language` | 地理位置与语言，模块默认不发送；官方未明确默认或完整取值范围 |
| `max_results` | 模块默认 `None`，仅本地切片，不发送数量参数 |
| `timeout` | 模块 HTTP 超时，默认 15 秒 |
| `domain_type` | 官方默认 `web`；当前模块未暴露 |

官方未公布可核实的单次结果上限，也未说明请求分页参数；官方响应示例的 `total_results=10` 与 `page=0` 不能证明固定容量或分页范围。统一 CLI `--limit` 默认不指定、0 表示不额外截断；正数只改变本地保留数量。实际请求始终只有 query 及可选 location/language，没有自动翻页或补足结果；输出 total_results 与实际保留条数应分别理解。

## 证据范围

已核对源码、adapter 及 `.work/output-analysis/api.json` 三条成功条目，文本字段为 string，position 与 total_results 为 integer。实测保存的是处理后结果，未保留服务完整 JSON；缺少 scheme 的链接、其他语言与位置未独立验证。
