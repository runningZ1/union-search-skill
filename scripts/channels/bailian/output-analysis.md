# 百炼输出结果分析

覆盖 `bailian_search.py` 的客户端、便捷函数和 JSON 脚本入口，以及 `union_search.py::_search_bailian`。当前通过 DashScope 文本生成接口强制联网，并请求返回来源。

## 结构与模块完整字段

源码访问的原始路径为 `output.search_info.search_results[]`、`output.choices[0].message.content`、顶层 `model/usage`，以及 `output.search_info.extra_tool_info`。以下为处理结构，不是原始完整响应声明。

| 位置与字段 | 类型、来源及缺失规则 |
| --- | --- |
| results | array；来源列表先限量再过滤空 url |
| results[].title | string；title 或 url，去除两端空白 |
| results[].href | string；url 去除空白 |
| results[].body | string；固定空字符串，模块不提取摘要 |
| results[].engine | string；固定 bailian |
| results[].site_name、icon | 通常 string；上游同名字段，假值转为空字符串 |
| results[].index | 原值或 null；上游 index，实测 integer |
| answer | 通常 string；第一条 choice 的 content；无 choice 时为空字符串 |
| model | 通常 string；顶层 model 缺失时使用请求模型 |
| usage | 通常 object；顶层 usage 缺失时为 {}，显式 null 会保留 |
| extra_tool_info | 通常 array；search_info 同名字段缺失时为 []，显式 null 会保留 |

客户端返回上述对象，脚本 `--json` 输出整个对象；`search_bailian` 便捷函数仅返回 `results`。answer 未进行类型转换，源码不能保证所有模型的 content 始终为字符串。index 是来源标记，不能当作相关性分数。

## 上游与统一 CLI 边界

HTTP 非 200 或顶层非空 code 会报错；缺少 object 类型的 search_info 也会报错；来源列表缺失或为假值则为空数组。空链接来源跳过，不补齐数量。未映射的来源字段、其他 choices 及其他响应元数据丢弃。

adapter 只取 `results`，因此 answer、model、usage、extra_tool_info 都不进入统一 CLI。条目保留于 `data.items[]` 或联合搜索 `data.results.bailian.items[]`，联合 `data.final_items[]` 另加 `_source_platform`；外层 `ok/errors` 是执行状态。

## 容量概览

| 官方每请求上限 | 模块默认 | 分页行为 | `--limit` 作用 |
| --- | --- | --- | --- |
| 来源条数上限未知，官方未公布固定值 | `max_results=None`，不截断返回来源 | 一次生成可能触发多轮检索；模块无分页累积或不足补充请求 | 不指定或 0 不额外截断；正数仅本地切片，不发送数量参数 |

本地样例：[examples/search-result.json](examples/search-result.json)。此文件保存真实 CLI 成功渠道对象，非原始 HTTP 响应。

## 常用参数与单次容量

核查日期：2026-10-25。官方来源：[联网搜索](https://help.aliyun.com/zh/model-studio/web-search)。

| 英文参数 | 含义、默认与范围 |
| --- | --- |
| `model` | 模块默认 `qwen-plus`，环境配置可覆盖；实际支持的搜索选项取决于模型 |
| `strategy` → `search_options.search_strategy` | 模块与官方默认 `turbo`；可选 `turbo/max/agent/agent_max` |
| `freshness` | 最近天数，可选 7、30、180、365，默认不限制；官方仅支持指定模型的 `turbo` 模式 |
| `sites` → `assigned_site_list` | 指定站点，模块默认不发送；官方最多 25 个，仅支持指定模型的 `turbo` 模式 |
| `vertical` → `enable_search_extension` | 垂直信息扩展，模块与官方默认 false |
| `max_results` | 模块默认 `None`，仅对已返回来源本地切片，不发送到服务 |
| `forced_search`、`enable_source`、`enable_search` | 模块固定 true，强制联网并要求来源 |

官方未公布 `search_results` 的固定单次来源数量上限；25 个站点限制和模型 token 限制均不能换算成来源条数。官方 `agent/agent_max` 仅允许同时使用其他搜索选项中的 `enable_source`，模块组合参数未做同等约束。统一 CLI `--limit` 默认不指定、0 表示不额外截断；指定正数只影响本地来源保留数量。一个模型生成请求可能触发多轮检索，模块没有分页累积逻辑；来源不足不会补充请求。

## 证据范围

已核对源码、adapter 和 `.work/output-analysis/api.json` 三条成功来源：条目文本字段为 string、index 为 integer、body 为空字符串。实测文件未保留客户端顶层四项，无法验证其真实值与嵌套类型；其他策略、垂直工具及不同模型未验证。
