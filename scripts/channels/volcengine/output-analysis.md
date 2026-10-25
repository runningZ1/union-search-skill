# 火山引擎输出结果分析

覆盖 `volcengine_search.py` 的 global/web/summary、JSON 与 SSE 处理，以及 `union_search.py::_search_volcengine`。客户端正常 JSON 返回完整响应；SSE 会选择末个事件，补入较早事件的 WebResults/ResultCount/SearchContext，并把 Delta.Content 合并到 Choices[0].Message.Content。

## 路径与模块完整字段边界

客户端无字段白名单；adapter 按版本读取 `Result.Documents[]`（global）或 `Result.WebResults[]`（custom），custom 还兼容 `Data.SearchResults[]`。下表完整列出本次条目字段；透传模式允许出现其他字段。

| 字段 | 实测类型、映射及条件 |
| --- | --- |
| Rank | integer；上游原值 |
| Url、Title | string；上游大小写字段原样保留 |
| Snippet | string；global 将原 Snippet 数组内 Type=text 的 Text 以换行拼接并覆盖；custom 原样保留 |
| DocumentInfo | object；实测 ContentCharCount/ContentTokenCount 为 integer，Filetype/PublishTime 为 string |
| HostInfo | object；实测 Hostname/IconUrl/AuthorityLevel 为 string |
| title、url | string；仅 global 由 Title/Url 新增，原字段仍保留；缺失默认空字符串 |
| 其他条目字段 | 原值透传，但 Content、LogoUrl 在 adapter 中明确删除 |

Content/LogoUrl 的删除仅作用于条目顶层，嵌套字段不受这项删除影响。Rank 为位置编号，AuthorityLevel 为字符串等级；代码没有数值分数尺度或等级顺序定义。日期与 token 数量均不转换，Snippet 也不等于完整正文。

## 统一输出与缺失规则

adapter 缺少 Result 时，custom 才尝试兼容路径；缺失结果列表可成为空数组，非数组结果则失败，非对象条目跳过。客户端检查 ResponseMetadata.Error 与 Result.ErrorCode；SSE 转换不保存事件时间和全部中间事件。

统一 CLI 仅保留经过 adapter 处理的条目，顶层 ResponseMetadata、Choices、SearchContext、计量及其他响应字段不再返回。单渠道为 `data.items[]`，联合为 `data.results.volcengine.items[]`；联合 `data.final_items[]` 增加 `_source_platform`，外层 ok/errors 是执行元数据。

## 容量概览

| 官方每请求上限 | 模块默认 | 分页行为 | `--limit` 作用 |
| --- | --- | --- | --- |
| Custom `Count` 50 条；Global `DocCount` 20 条 | 两种端点均请求 10 条；版本默认 custom，可由环境覆盖 | 当前实现无自动分页 | 不指定或 0 时请求 10；正数在 Global adapter 限制到 20，在 Custom 交模块校验 50 上限，再本地切片 |

本地样例：[examples/search-result.json](examples/search-result.json)。此文件保存真实 CLI 成功渠道对象，非原始 HTTP 响应。

## 常用参数与单次容量

核查日期：2026-10-25。官方来源：[Collab 智能体 API](https://docs.volcengine.com/docs/NetworkedQAAgent/CollabAgentAPI?lang=zh)。官方搜索可见参数说明确认 `Count` 最高 50、`DocCount` 最高 20，二者默认均为 10；页面正文直取为空，因此其他参数的官方完整约束未核实。

| 英文参数 | 含义、模块默认与范围 |
| --- | --- |
| `version` | 模块默认 `custom`，可选 `global`，环境可覆盖 |
| `count` → `Count`（Custom） | 模块默认 10，web/web_summary 检查正数且最多 50 |
| `count` → `DocCount`（Global） | 模块默认 10，范围 1—20 |
| `max_snippet_length` → `MaxSnippetLength` | Global 默认 500，模块范围 1—3000，限制文本长度 |
| `max_image_count_per_doc` → `MaxImageCountPerDoc` | Global 默认 3，模块范围 0—10，限制每文档图片数 |
| `need_content/need_url/need_summary` | Custom 默认 false，控制正文、原文链接和摘要 |
| `time_range` → `TimeRange` | 默认不限；模块接受 `OneDay/OneWeek/OneMonth/OneYear` 或日期区间 |
| `sites/block_hosts` | 默认不发送，模块各最多 5 个域名 |
| `auth_info_level/query_rewrite/industry` | Custom 默认 0、false、不指定；模块分别允许 0/1、布尔、`finance/game` |

单次容量须按端点区分：Custom 网页 50，Global 文档 20；`TotalDocCount` 等匹配总量不等于本次 Documents 长度。统一 CLI `--limit` 默认不指定、0 表示不额外截断，此时请求默认 10；Global 正数在 adapter 限制到 20，Custom 正数交模块校验 50 上限，再对返回条目本地切片。当前实现不自动分页；片段长度、每文档图片数和 SSE 事件数都不代表搜索结果数量。

## 证据范围

源码、adapter 与 `.work/output-analysis/api.json` 已核对。三条真实结果含新增 title/url 和字符串 Snippet，符合 global 转换，类型如表。原始 HTTP/SSE 未保存，无法枚举完整响应；custom、流式回答合并、其他嵌套结构仅有源码证据。
