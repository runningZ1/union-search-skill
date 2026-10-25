# Tavily 输出结果分析

覆盖 `tavily_search.py` 的 `TavilySearchClient.search`、JSON 脚本及 `union_search.py::_search_tavily`。客户端直接返回 Tavily SDK 的 search 返回对象，模块没有固定字段白名单。

## 结构与已证实字段

脚本 --json 序列化整个 SDK 结果；adapter 只提取顶层 results。下表完整列出本次统一输出实际条目字段；由于模块透传对象，不能将它视为所有请求的封闭字段集合。

| results[] 字段 | 实测类型与语义 |
| --- | --- |
| url | string；来源地址，模块不改名 |
| title | string；标题，模块不清洗 |
| content | string；服务检索内容文本，模块不截断 |
| score | number；服务评分原值，模块无范围校验 |
| raw_content | null；本次未取得该字段的非空正文证据 |
| id | string；上游/SDK 提供的条目标识，模块不生成 |

SDK 结果顶层的 query、answer、results 是展示函数明确使用的路径；其他顶层字段没有模块过滤。answer 由 include_answer 请求开关影响，但本次 adapter 未打开该开关。源码没有为 SDK 缺失字段补默认值，也没有过滤空标题、空地址或 null；上游返回的额外条目字段会继续透传。

## 上游与统一 CLI 边界

score 常用于检索相关性，但当前代码与本次样本不能证明其统一尺度、取值边界或跨查询比较的有效性。content 与 raw_content 应分别看待，不能依据字段存在就认定有完整正文。主题参数可能影响返回字段，当前未建立新闻、金融的封闭字段契约。

adapter 仅发送 query、可选 --max-results，读取 results 后切片；search-depth、topic、include-answer 没有从该 adapter 透传。结果顶层信息随之丢弃，条目进入 `data.items[]` 或 `data.results.tavily.items[]`；联合 `data.final_items[]` 增加 `_source_platform`，外层 ok/errors 为统一执行状态。

## 容量概览

| 官方每请求上限 | 模块默认 | 分页行为 | `--limit` 作用 |
| --- | --- | --- | --- |
| 20 条 | `max_results=None` 时省略参数，采用已安装 SDK 与服务默认行为；官方当前默认 10 | 官方 schema 未公布分页字段；模块无自动分页 | 不指定或 0 时省略 SDK `max_results`；正数原样传给 SDK 再本地切片，模块不预先限制到 20 |

本地样例：[examples/search-result.json](examples/search-result.json)。此文件保存真实 CLI 成功渠道对象，非原始 HTTP 响应。

## 常用参数与单次容量

核查日期：2026-10-25。官方来源：[Search API](https://docs.tavily.com/documentation/api-reference/endpoint/search)。

| 英文参数 | 含义、默认与范围 |
| --- | --- |
| `query` | 查询文本 |
| `max_results` | 官方当前默认 10、范围 0—20；模块默认 `None` 时省略，采用已安装 SDK 与服务的默认行为；显式值原样传给 SDK |
| `search_depth` | 官方默认 `basic`，可选 `basic/advanced/fast/ultra-fast`；模块默认不传，脚本 choices 仅前三项 |
| `topic` | 官方默认 `general`，可选 `general/news/finance`；模块默认不传 |
| `include_answer` | 模块默认 false；官方默认 false，另支持 true、`basic/advanced`；当前模块仅通过布尔开关开启 |

官方单次最多 20 条，当前 schema 未公布分页字段。统一 CLI `--limit` 默认不指定、0 表示不额外截断并省略 SDK max_results；这里 CLI 的 0 不会作为官方允许的 `max_results=0` 发送。正数传入 SDK 后 adapter 再本地切片，大于 20 未在当前模块中预先限制。当前 adapter 不透传深度、主题、回答开关；没有自动分页。官方默认与特定安装版本 SDK 的默认应分别核对，本文未调用服务测试最大容量。

## 证据范围

已核对源码、adapter 和 `.work/output-analysis/api.json` 三条成功条目。记录是处理后的结果列表，未保存 SDK 顶层或原始 HTTP JSON，不能声称枚举了完整原生响应。非空 raw_content、answer、其他检索深度及主题尚未验证。
