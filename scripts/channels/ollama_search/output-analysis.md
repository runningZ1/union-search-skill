# Ollama Web Search 输出结果分析

覆盖 `ollama_search.py` 的客户端、`search_ollama`、JSON 脚本入口，以及 `union_search.py::_search_ollama`。该入口调用托管 `/api/web_search`；请求结果数被限制在 1—10，未指定时请求 10 条。

## 结构与完整字段表

服务正常返回路径由源码确定为顶层 `results[]`；模块要求它是数组。这里只列源码实际读取的路径，不声明服务完整结构。客户端返回数组，脚本 `--json` 输出含 `results` 的对象。

| 模块全部字段 | 类型、上游映射与缺失规则 |
| --- | --- |
| title | string；原 title 或 url，再去除两端空白 |
| href | string；原 url，去除两端空白；空值条目丢弃 |
| body | string；原 content，缺失或 null 转为空字符串后去除空白 |
| engine | string；固定 ollama |

四个字段均在真实条目中观察为字符串。body 保存服务 content 文本，没有额外摘要长度限制；字段名称不足以证明其包含整篇网页。模块没有日期、来源站点、原始顺序编号和相关性分数，也没有把缺失的这些信息补充进输出。服务可能提供的其他字段不在当前映射范围内。

## 限量、丢弃与统一 CLI

模块先切片再处理条目，空地址不会补齐，返回数量可能少于请求数量。标题缺失时改用地址，正文缺失时仍保留该条目。HTTP 非 200、results 缺失或不是数组时直接报错；有效空数组可以正常返回。

adapter 仅取模块 `results` 并再次限量，四个条目字段原样进入统一 CLI。单渠道位置为 `data.items[]`，联合搜索位置为 `data.results.ollama.items[]`；联合 `data.final_items[]` 添加 `_source_platform`。外层 `ok/errors` 反映调用状态，total 是实际保留数量，不能当作上游索引总量。

## 容量概览

| 官方每请求上限 | 模块默认 | 分页行为 | `--limit` 作用 |
| --- | --- | --- | --- |
| 10 条 | `max_results=None` 时请求 10 条；官方默认 5 条 | 官方未提供分页机制；模块无自动分页 | 不指定或 0 时仍请求 10；正数限制到 1—10 后发送，模块与 adapter 再本地切片 |

本地样例：[examples/search-result.json](examples/search-result.json)。此文件保存真实 CLI 成功渠道对象，非原始 HTTP 响应。

## 常用参数与单次容量

核查日期：2026-10-25。官方来源：[Web Search](https://docs.ollama.com/capabilities/web-search)。

| 英文参数 | 含义、默认与范围 |
| --- | --- |
| `query` | 查询文本，模块要求非空 |
| `max_results` | 官方默认 5、最高 10；模块默认 `None` 时实际请求 10，显式值限制到 1—10 |
| `timeout` | 模块 HTTP 超时，默认 30 秒 |
| `endpoint` | 模块默认 `https://ollama.com/api/web_search`，环境或构造参数可覆盖 |

官方单次最多 10 条，当前文档未提供分页机制。统一 CLI `--limit` 默认不指定、0 表示不额外截断，此时请求仍为 10；指定正数限制到 10 后发送。模块与 adapter 还执行本地切片并过滤空地址，因此最终结果可能少于请求值；增加 limit 不会取得后续页面。

## 证据范围

依据源码、对应 adapter 和 `.work/output-analysis/api.json` 的三条成功结果；该文件能验证模块输出类型，不能还原未保存的服务完整原始响应。未验证其他查询、接近十条上限的返回、空正文与上游额外字段。
