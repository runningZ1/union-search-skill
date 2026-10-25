# 秘塔输出结果分析

覆盖 `metaso_search.py` 客户端、SearchResult/WebpageResult、JSON 格式化和 `union_search.py::_search_metaso`。服务读取路径为顶层 webpages、credits、total、searchParameters；客户端将字段转入 dataclass，未执行类型强制转换。

## 完整模块字段

| 位置与字段 | 类型、来源与缺失规则 |
| --- | --- |
| query | 通常 string；searchParameters.q，缺失为空字符串 |
| total、credits | 通常 integer；顶层同名字段，缺失为 0 |
| webpages | array；上游 webpages 逐项转换 |
| webpages[].position | 实测 integer；原 position，缺失为 0 |
| webpages[].title、link | 实测 string；原同名字段，缺失为空字符串 |
| webpages[].score | 实测 string；原 score，缺失为空字符串 |
| webpages[].date | 实测 string；原 date，缺失为 null |
| webpages[].summary | 本次 null；原 summary，缺失为 null |
| webpages[].snippet | 实测 string；原 snippet，缺失为 null |
| webpages[].authors | 实测 array<string> 或 null；原 authors，缺失为 null |
| search_parameters（客户端） | object；完整 searchParameters，缺失为 {}；JSON 格式化不输出此字段 |

以上是当前模块完整固定字段集合。显式 null 会按原值保留；dataclass 注解不等于运行时验证。score 虽被展示为相关度，实际为字符串，不能直接按数值排序，也没有经过验证的数值范围。summary 与 snippet 分别保留，摘要缺失不影响片段；includeRawContent 即使请求，上游额外正文也不在 dataclass 映射中。

## 上游和 CLI 边界

其他上游字段均丢弃。JSON 脚本输出 query/total/credits/webpages，adapter 固定使用 --summary，只取 webpages 并按 limit 切片，因此 query、credits、服务 total 不进入统一结果。条目保留全部八项字段，位于 `data.items[]` 或 `data.results.metaso.items[]`；联合 `data.final_items[]` 增加 `_source_platform`。渠道 total 是保留条数，与服务 total 不同；外层 ok/errors 为执行状态。

## 容量概览

| 官方每请求上限 | 模块默认 | 分页行为 | `--limit` 作用 |
| --- | --- | --- | --- |
| 未知；源码注释 1—50 未获官方证据确认 | 请求 `size="10"` | 当前实现无分页或累积请求 | 不指定或 0 时仍请求 10；正数通过 `--size` 发送同值，adapter 另做本地切片 |

本地样例：[examples/search-result.json](examples/search-result.json)。此文件保存真实 CLI 成功渠道对象，非原始 HTTP 响应。

## 常用参数与单次容量

核查日期：2026-10-25。官方核查入口：[搜索 API Playground](https://metaso.cn/search-api/playground)；本次无法读取官方参数说明，以下默认值来自当前源码，官方单次数量上限未核实。

| 英文参数 | 含义、模块默认与范围 |
| --- | --- |
| `query` → `q` | 搜索文本 |
| `size` | 客户端与脚本默认 10，以字符串发送；源码注释标注 1—50，但本次无官方证据确认 50 为服务上限 |
| `scope` | 客户端默认 `webpage`，另有 `file` 选项；当前 adapter 使用网页范围 |
| `include_summary` → `includeSummary` | 客户端与脚本默认 true，统一 adapter 也固定传入 `--summary` |
| `include_raw_content` → `includeRawContent` | 默认 false；当前 dataclass 不保留额外正文 |
| `concise_snippet` → `conciseSnippet` | 客户端默认 true，控制片段简洁程度 |

统一 CLI `--limit` 默认不指定、0 表示不额外截断，此时实际发送 `size="10"`；正数通过 `--size` 发送同值，adapter 另外本地切片。当前实现没有分页或累积请求，服务 `total` 与本次返回 `webpages` 长度不同；不能根据 total、代码注释或本地 limit 推断单次服务上限。

## 证据范围

已核对源码、adapter 和 `.work/output-analysis/api.json` 三条成功结果；summary 均为 null，authors 同时出现数组与 null。该文件未保留原始响应及客户端顶层，无法验证积分、服务总数和 searchParameters 的实际结构；file 范围、原始正文及非空摘要未验证。
