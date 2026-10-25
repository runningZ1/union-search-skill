# Exa 输出结果分析

覆盖 `exa_search.py` 的客户端、便捷函数、JSON 脚本与 `union_search.py::_search_exa`；目录另有独立 `exa_mcp.py`，其输出边界另述。

## API 结构与完整模块字段

REST 源码读取顶层 `results[]`，默认请求 text 内容且限制 maxCharacters 为 500。模块只保留以下字段，脚本包装为 results 对象。

| 模块字段 | 类型、映射与缺失规则 |
| --- | --- |
| title | string；原 title 去除空白，空标题丢弃 |
| href | string；原 url 去除空白，空地址丢弃 |
| body | string；按 contents.text、text、excerpt、summary 的顺序取首个非空文本，否则为空字符串 |
| engine | string；固定 exa |
| score | 原值或 null；上游同名字段，实测仅 null |

body 超过 500 字符时，取前 500 字符并在最后空格处截断，再加省略号；它无法作为全文证据。缺失 title/url 默认空字符串，但显式 null 会在 strip 时失败。缺失 results 默认空数组；其他字段不校验完整类型。

上游其他条目字段及顶层元数据都被丢弃。score 没有归一化、范围校验或必有值保证，不能从本次 null 推断评分尺度。adapter 默认传 --type auto，取 results 并按 limit 截取；五个字段保留在 `data.items[]` 或 `data.results.exa.items[]`，联合 `data.final_items[]` 增加 `_source_platform`，外层 ok/errors 为执行状态。

## 独立 MCP 脚本

`exa_mcp.py` 通过 mcporter 提供 web、code、company、people、crawl、deep、check。正常 JSON stdout 经 json.loads 后直接返回，未定义固定字段表；不能仅凭展示函数读取 results/title/url/content 就认定完整响应只有这些字段。非 JSON 输出包装为 `raw: string`，错误路径可含 `error` 与 `raw`。此脚本未被 `_search_exa` 使用，其 --json 保留该返回对象，服务工具原始结构未实测。

## 容量概览

| 官方每请求上限 | 模块默认 | 分页行为 | `--limit` 作用 |
| --- | --- | --- | --- |
| REST 公开 schema 上界 100 条；具体模式可能更低，逐模式数值未知；独立 MCP 容量未核实 | REST 请求 `numResults=10` | REST 无自动分页；独立 MCP 未实测 | 不指定或 0 时 REST 仍请求 10；正数发送为 `numResults` 并本地切片，模块不自动限制到 100 |

本地样例：[examples/search-result.json](examples/search-result.json)。此文件保存真实 CLI 成功渠道对象，非原始 HTTP 响应。

## 常用参数与单次容量

核查日期：2026-10-25。官方来源：[Search API](https://exa.ai/docs/reference/search)。

| 英文参数 | 含义、默认与范围 |
| --- | --- |
| `query` | 查询文本 |
| `max_results` → `numResults` | 模块默认 `None` 时发送 10；官方默认 10，公开 schema 范围 1—100，并说明可能受搜索模式限制 |
| `search_type` → `type` | 模块与官方默认 `auto`；脚本保留 `auto/neural/keyword` 选项，当前官方主要列出 `auto/lite/deep-lite/deep`，不能推定旧选项与当前模式等价 |
| `include_text` → `contents.text` | 模块默认 true，固定发送 `maxCharacters=500`；关闭时省略 contents |
| `timeout` | 模块默认 15 秒 |

官方公开 schema 的单次结果数上界为 100，具体模式可能有更低限制，当前页面未完整列出各模式数值；数量参数不保证实际返回足额。统一 CLI `--limit` 默认不指定、0 表示不额外截断，此时实际请求 10；指定正数发送同值 `numResults`，模块没有自动限制到 100，也没有翻页。adapter 本地切片与 body 的 500 字符截取分别限制条数和文本长度；独立 MCP 脚本未用于该 REST 入口，不能套用此处容量。

## 证据范围

依据两份源码、adapter 和 `.work/output-analysis/api.json` 的三条成功 REST 条目；title/href/body/engine 为 string，score 为 null。该文件是处理后输出，不能恢复上游完整结构。MCP、非空分数、neural/keyword 与关闭文本模式未调用；本文未开展网络请求。
