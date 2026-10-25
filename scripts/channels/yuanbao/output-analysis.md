# 腾讯元宝输出结果分析

覆盖 `yuanbao_search.py` 客户端、便捷函数、JSON 脚本和 `union_search.py::_search_yuanbao`。实际调用腾讯云 SearchPro；原始来源位于 `Response.Pages[]`，每项需先通过 `json.loads` 从 JSON 字符串解析成对象。

## 完整模块字段与上游映射

| 模块字段 | 类型、来源和缺失规则 |
| --- | --- |
| title | string；解析对象 title 或 url，去除空白 |
| href | string；url 去除空白，空地址跳过 |
| body | string；passage 优先，其次 content，最后空字符串 |
| engine | string；固定 yuanbao |
| content | 实测 string；同名字段缺失为空字符串，显式 null 保留 |
| site、favicon | 通常 string；同名字段，假值为空字符串 |
| date | 原值或 null；实测 string，无日期解析 |
| score | 原值或 null；实测 number |
| authority_level | 原值或 null；本次仅观察 null |
| images | 原 pics 优先，其次 images，最后 []；实测 array |
| deeplinks | 原同名字段或 []；实测 array |

images 与 deeplinks 的内部结构没有转换，模块也未校验其一定为数组；表中 array 为实测类型。score 在终端显示为相关度，但未定义尺度和跨查询可比性；authority_level 的等级和排序方向未由源码证明。body 与 content 分别保留，二者可能重复，也可能分别承载片段与更多文本。

## 缺失、丢弃与 CLI

HTTP 非 200、Response 非对象、Response.Error 非空、Pages 非数组均失败；Pages 内 JSON 无法解析也会失败。请求 Cnt 向上调整到 10—50 的档位，模块过滤空地址后再限量，实际条数可以更少。

未映射的页内字段、Response 的其他元数据不保留。脚本 JSON 包装为 results；adapter 取该列表，全部条目字段进入 `data.items[]` 或 `data.results.yuanbao.items[]`，联合 `data.final_items[]` 增加 `_source_platform`。外层 ok/errors 为统一执行状态。

## 容量概览

| 官方每请求上限 | 模块默认 | 分页行为 | `--limit` 作用 |
| --- | --- | --- | --- |
| 50 条；Cnt 在 lite 版本不支持 | 请求 `Cnt=10` | 官方未公布搜索分页机制；模块无自动分页 | 不指定或 0 时请求 10；正数向上取 10/20/30/40/50 档位，最多请求 50，再按原 limit 本地切片 |

本地样例：[examples/search-result.json](examples/search-result.json)。此文件保存真实 CLI 成功渠道对象，非原始 HTTP 响应。

## 常用参数与单次容量

核查日期：2026-10-25。官方来源：[SearchPro](https://cloud.tencent.com/document/api/1806/121811)。

| 英文参数 | 含义、默认与范围 |
| --- | --- |
| `query` → `Query` | 非空查询 |
| `max_results` → `Cnt` | 官方允许 10、20、30、40、50，最高 50，未公布默认；模块默认请求 10，显式值向上取档并最多 50 |
| `mode` → `Mode` | 模块默认不发送；官方默认 0，可选 0 公开网页、1 权威垂直、2 混合 |
| `site` → `Site` | 默认不发送；官方支持单域名限定，或以 `exclude:` 排除最多 5 个域名 |
| `industry` → `Industry` | 默认不发送，可选 `gov/news/acad/finance` |
| `freshness` → `Freshness` | 默认不发送；官方支持 `d[N]`（1—30）、`m[N]`（1—12）、`y[N]`（1—5）及日期/日期区间 |
| `deeplinks` → `Deeplinks` | 模块默认 false，true 时发送；官方旗舰版支持，每结果最多 10 个附件链接 |
| `timeout` | 模块默认 30 秒 |

官方单次搜索结果最多 50；Cnt、Mode、Industry 在 lite 版本不支持，Deeplinks 只适用于旗舰版本。统一 CLI `--limit` 默认不指定、0 表示不额外截断，实际请求 Cnt=10；例如 limit=13 会请求 Cnt=20，再本地保留最多 13。limit 大于 50 仍只请求 50，模块与 adapter 不自动分页。附件链接上限和图片数量不能累计为搜索结果容量；官方未公布搜索分页机制。

## 证据范围

已核对源码、adapter 和 `.work/output-analysis/api.json` 三条成功结果；该文件不能保留 Pages 的原字符串形态，解析路径由源码证明。图片与子链接的非空内部结构、authority_level 非空值、不同 Mode/Industry 与旗舰子链接能力未验证。
