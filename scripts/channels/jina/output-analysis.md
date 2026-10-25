# Jina 输出结果分析

覆盖 `jina_search.py` 的 `JinaSearch.search`、JSON 脚本与 `union_search.py::_search_jina`。请求 `s.jina.ai` 时明确发送 `X-Respond-With: no-content` 和 JSON Accept，正文能力以该请求方式为边界。

## 结构与完整模块字段

源码仅从服务顶层 `data[]` 读取条目，非对象条目被跳过。模块返回数组，脚本 --json 外层包含 query、total_results、results；total_results 是本地保留条数。

| 模块字段 | 类型、上游映射及缺失规则 |
| --- | --- |
| title | 实测 string；原 title，缺失为空字符串，显式 null 原样保留 |
| href | 实测 string；原 url，缺失为空字符串，显式 null 原样保留 |
| body | 实测 string；description 优先，其次 content，最后空字符串 |
| query（脚本外层） | string；输入查询 |
| total_results（脚本外层） | integer；len(results) |
| results（脚本外层） | array；以上三个条目字段组成的列表 |

模块不去除空白、不截断、不验证标题和地址是否为空，也不保证 body 的非空上游值必为字符串。body 是描述优先的文本；当前 no-content 请求不能用于证明完整网页正文已返回。模块没有 engine、日期或相关性分数。

## 上游丢弃与统一 CLI

data 缺失时使用空数组，顶层非对象也返回空数组；HTTP 失败会报错。列表先限量再过滤非对象，可能少于请求数量。所有未映射条目字段及顶层状态、计量等信息均未保留。`--save-response` 保存的是模块包装结果，名称不表示保存了原始 HTTP JSON。

adapter 读取 results 并再次限量，丢弃脚本 query/total_results。三项条目字段进入单渠道 `data.items[]` 或联合搜索 `data.results.jina.items[]`；联合 `data.final_items[]` 增加 `_source_platform`。统一 CLI 外层 ok/errors 是执行信息，其 total 表示保留数量。

## 容量概览

| 官方每请求上限 | 模块默认 | 分页行为 | `--limit` 作用 |
| --- | --- | --- | --- |
| 上限与服务默认返回数量均未知 | `max_results=None`，不发送 `num`，不额外切片 | 官方列出 page，但默认与范围未知；模块未暴露且不翻页 | 不指定或 0 不额外截断；正数仅对一次响应本地切片，不发送 `num` |

本地样例：[examples/search-result.json](examples/search-result.json)。此文件保存真实 CLI 成功渠道对象，非原始 HTTP 响应。

## 常用参数与单次容量

核查日期：2026-10-25。官方来源：[Jina API Reference](https://docs.jina.ai/)。

| 英文参数 | 含义、默认与范围 |
| --- | --- |
| `query` → `q` | 模块发送的查询文本 |
| `max_results` | 模块默认 `None`，仅本地切片，不作为数量参数发送 |
| `num` | 官方当前页面列出的可选结果数量参数；本次完整页面提取未确认默认值与范围，模块未发送 |
| `page` | 官方列出的分页偏移参数；默认与范围未核实，模块未暴露 |
| `X-Respond-With` | 模块固定 `no-content`，官方说明用于省略网页正文 |
| `Accept` | 模块固定 `application/json`；HTTP 超时固定 30 秒 |

官方单次数量上限和默认返回数量本次未核实；当前取得的官方页面内容未明确数值范围。统一 CLI `--limit` 默认不指定、0 表示不额外截断；指定正数也仅对这一次响应本地切片，既不会发送 `num`，也不会翻页。服务实际返回数量须检查该次响应，模块保留条数不能证明服务上限。

## 证据范围

源码、adapter 和 `.work/output-analysis/api.json` 已核对，三条成功结果中 title/href/body 均为 string。真实文件已处理，不能确认每条 body 的优先来源或服务完整字段；缺失字段、空地址、其他响应方式未独立验证。
