# Serper 输出结果分析

覆盖 `serper_search.py` 的客户端、`search_serper`、JSON 脚本和 `union_search.py::_search_serper`。当前实现只提取服务有机网页结果。

## 原始路径与完整模块字段

服务原始读取路径为顶层 `organic[]`；这里列出的字段是模块明确保留集合，未声明上游完整 JSON。

| 模块字段 | 类型、映射与缺失规则 |
| --- | --- |
| title | string；organic[].title 去除空白，空标题条目丢弃 |
| href | string；organic[].link 去除空白，空地址条目丢弃 |
| body | string；organic[].snippet 去除空白，缺失为空字符串 |
| engine | string；固定 serper |
| position | 原值或 null；organic[].position，实测 integer |
| source | 原值或 null；organic[].source，本次仅观察 null |

title/link/snippet 使用 get 默认值后直接 strip；上游显式 null 可能导致失败，不能统一理解为自动转为空字符串。position 代表返回位置，模块不把它转换为相关性分数。source 未做类型转换，其非空结构尚无实测证据。输出没有日期、独立全文或数字评分。

## 丢弃与数量规则

organic 缺失时默认空数组；模块先按 max_results 截取，再过滤空标题/链接，因此实际数量可以更少。其他条目字段、其他结果分区和顶层元数据全部丢弃。请求 num 是另一参数，模块发送时限制到最多 100，该数字仅有实现证据；脚本未将 max_results 直接转换为请求 num，所以 --max-results 主要控制本地截取，不能保证取得相同条数。

脚本 --json 输出含 results 的对象。adapter 传入页码、国家、语言、位置等参数，取 results 并再次限量；六个条目字段进入 `data.items[]` 或联合 `data.results.serper.items[]`。联合 `data.final_items[]` 增加 `_source_platform`，外层 ok/errors 与渠道 total 为执行元数据。

## 容量概览

| 官方每请求上限 | 模块默认 | 分页行为 | `--limit` 作用 |
| --- | --- | --- | --- |
| 未知；源码 `num` 最多 100 未获官方证据确认 | 客户端 `num=10`、`page=1`；`max_results=None` | 每次仅请求指定 page；无自动分页累积 | 不指定或 0 不额外截断；正数仅本地切片，统一 adapter 仍请求默认 `num=10` |

本地样例：[examples/search-result.json](examples/search-result.json)。此文件保存真实 CLI 成功渠道对象，非原始 HTTP 响应。

## 常用参数与单次容量

核查日期：2026-10-25。官方核查入口：[Serper](https://serper.dev/)；公开页面未给出本次可核实的 `num` 参数范围，官方单次上限未核实。

| 英文参数 | 含义、模块默认与范围 |
| --- | --- |
| `query` → `q` | 搜索文本 |
| `num` | 客户端默认 10，请求实际发送 `min(num,100)`；此 100 为模块限制，未核实官方承诺 |
| `max_results` | 默认 `None`，只切片本次 `organic` 数组，未用于计算 num |
| `page` | 默认 1，只请求该页 |
| `gl`、`hl` | 默认 `us`、`en`，国家与语言 |
| `location` | 地理位置，默认不发送 |
| `timeout` | 客户端默认 15 秒 |

统一 CLI `--limit` 默认不指定、0 表示不额外截断；即使指定 50，当前 adapter 仍只通过脚本请求默认 `num=10`，然后本地截取到最多 50，不会自动取得 50 条。客户端直接调用可另行指定 num；当前统一 adapter 不传 num。每次请求一个 page，没有自动分页累积；实际返回数量以服务 organic 数组为准，不能把本地截取、源码 100 或营销页面描述认作经核实的服务容量。

## 证据范围

已核对源码、adapter 和 `.work/output-analysis/api.json` 三条成功结果：四个文本字段为 string，position 为 integer，source 为 null。文件保存的是模块输出，无法复原 organic 其他字段或原始顶层结构；非空 source、其他页码与地域未独立验证。
