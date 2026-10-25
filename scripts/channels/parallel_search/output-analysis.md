# Parallel Search 输出结果分析

覆盖 `parallel_search.py` 的客户端、`search_parallel`、JSON 脚本及 `union_search.py::_search_parallel`。当前入口接受自然语言 objective 与多个 search_queries，返回摘录来源。

## 原生路径与完整模块字段

源码读取顶层 `results[]`、`warnings[]`、`search_id`、`session_id`。客户端返回数组，脚本输出含 results 的对象；这里只说明已读取结构。

| 模块字段 | 类型、上游映射与缺失规则 |
| --- | --- |
| title | string；title 或 url，去除空白 |
| href | string；url 去除空白；空地址条目丢弃 |
| body | string；excerpts 中非空 string 去除空白，以换行连接 |
| engine | string；固定 parallel |
| publish_date | 原值或 null；上游同名字段，实测 string |
| search_id、session_id | 原值或 null；顶层同名字段复制到每条结果，实测 string |
| warnings | string；顶层 warnings 中 object 的非空 message 以中文分号连接，无内容为空字符串 |

原 excerpts 数组的边界和其他类型元素丢失，body 未截断；它是若干摘录的拼接，源码没有完整网页正文契约。warnings 的编号、类别与其他属性未保留，message 之外的信息不能从输出恢复。日期没有解析；输出不包含相关性分数，列表次序也未被命名为质量分值。

## 保留边界与统一 CLI

HTTP 非 200 或缺少数组 results 会失败。模块先限量再过滤空地址，标题缺失使用地址，空 excerpts 允许保留条目。未映射的服务字段全部丢弃；空结果也使搜索标识和 warning 无法通过条目返回。请求中 include_domains 优先于 exclude_domains，但这属于请求条件，不是输出字段。

adapter 读取 results 并再次限量。单渠道统一输出位于 `data.items[]`，联合搜索位于 `data.results.parallel.items[]`；联合 `data.final_items[]` 添加 `_source_platform`。CLI 外层 ok/errors、渠道 total 为执行信息。

## 容量概览

| 官方每请求上限 | 模块默认 | 分页行为 | `--limit` 作用 |
| --- | --- | --- | --- |
| 未知；官方 schema 未公布数值上限 | 请求 `advanced_settings.max_results=10` | 当前接口无分页字段；session_id 用于上下文延续；模块只请求一次 | 不指定或 0 时仍请求 10；正数发送同值，并用于模块与 adapter 本地切片 |

本地样例：[examples/search-result.json](examples/search-result.json)。此文件保存真实 CLI 成功渠道对象，非原始 HTTP 响应。

## 常用参数与单次容量

核查日期：2026-10-25。官方来源：[Search API](https://docs.parallel.ai/api-reference/search/search)。

| 英文参数 | 含义、默认与范围 |
| --- | --- |
| `objective`、`search_queries` | 自然语言目标与查询列表；模块默认分别使用 query 与 `[query]` |
| `mode` | 模块默认 `fast`，可选 `turbo/fast/basic/advanced`；官方省略时默认 `advanced` |
| `max_results` → `advanced_settings.max_results` | 模块默认 `None` 时发送 10；官方默认 10，schema 未公布数值最小值或最大值 |
| `location` → `advanced_settings.location` | 国家定位，默认不发送；官方使用两位 ISO 国家代码 |
| `include_domains/exclude_domains` → `advanced_settings.source_policy` | 默认不发送；模块优先 inclusion；官方两类列表合计最多 200 项 |
| `after_date` | 包含该日期的发布时间下界，`YYYY-MM-DD`，默认不发送 |
| `timeout` | 模块默认 30 秒 |

官方未公布数值形式的单次结果上限。200 项是来源策略条目限制，不能解释为结果容量。统一 CLI `--limit` 默认不指定、0 表示不额外截断，此时仍发送 `advanced_settings.max_results=10`；正数发送同值并用于模块和 adapter 本地切片。当前接口未提供分页字段，`session_id` 用于上下文延续，不能当作分页游标；模块只调用一次。

## 证据范围

已核对源码、adapter 与 `.work/output-analysis/api.json` 三条成功结果，全部八个字段实测为 string。该文件未保存原 excerpts 和 warnings 对象，无法确认其完整字段；其他模式、多个查询及带非空 warning 的返回未验证。
