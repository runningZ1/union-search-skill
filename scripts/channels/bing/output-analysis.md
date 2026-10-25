# Bing 输出结果分析

覆盖 `bing_serpapi_search.py`、`bing_cn_no_api.py`、`bing_int_no_api.py` 和对应 `_search_bing`、`_search_no_api_direct`。API 与网页直连各有独立字段集合。

## API 原始路径与完整字段

SerpAPI 路径是 `organic_results[]`；模块只读取以下四项，并在 --json 中包装 query/page/lang/country/total_results/results。total_results 为本地 len(results)。

| 模块条目字段 | 类型、映射及缺失规则 |
| --- | --- |
| title | 实测 string；原 title，缺失为空字符串 |
| href | 实测 string；原 link，缺失为空字符串 |
| body | 实测 string；原 snippet，缺失为空字符串 |
| displayed_link | 实测 string；原同名字段，缺失为空字符串 |

字段用 get 直接读取，显式 null 会保留；模块不要求标题和地址非空，不清洗文本。其他条目字段、search_metadata 及其他顶层信息不保留，metadata 仅用于错误检查。列表顺序保留，输出没有分数字段。

## 两个网页直连入口

上游为 HTML，无原生 JSON。中国入口读取 b_algo 或 b_ans 容器中的 h2 链接或 b_title，国际入口只读取 b_algo 的 h2 链接；摘要分别取 b_caption/段落文本。完整条目字段为 title、href、body、engine，均由解析器生成 string，engine 分别固定 bing_cn、bing_int。缺少标题或链接时跳过，缺少摘要为空字符串；解析异常的条目会被跳过。两个脚本均包装为 results，页面其他信息、日期、展示域名和排序分数均未提取。

## 容量概览

| 官方每请求上限 | 模块默认 | 分页行为 | `--limit` 作用 |
| --- | --- | --- | --- |
| SerpAPI Bing 上限未知；两个直连入口固定条数未知 | API 请求 `count=10`、`page=1`；直连不额外截断 | API 每次一页，`first=(page-1)*10+1`；直连每次一个 HTML 响应；均无自动分页 | 不指定或 0 时 API 仍请求 10；正数影响 API `count` 与本地切片；直连仅本地截取 |

本地样例：[API 主样例](examples/search-result.json)、[国际网页直连样例](examples/search-result-bing_int_direct.json)。这些文件保存真实 CLI 成功渠道对象，非原始 HTTP 响应；同名 `-info.json` 文件记录查询时间与来源层次。

## 常用参数与单次容量

核查日期：2026-10-25。官方来源：[SerpAPI Bing Search API](https://serpapi.com/bing-search-api)。当前商业入口使用 SerpAPI。

| 英文参数 | 含义、默认与范围 |
| --- | --- |
| `query` → `q` | 搜索文本 |
| `page` → `first` | 模块默认 1，按 `(page-1)*10+1` 生成起始位置；官方 `first` 默认 1 |
| `max_results` → `count` | 模块默认 `None` 时实际发送 10，正数发送同值并在本地切片；当前 SerpAPI 官方页未说明 `count` 的默认或上限 |
| `country` → `cc`、`market` → `mkt` | 模块默认 `us`、不指定市场；有 `mkt` 时不发送 `cc`，官方要求二者互斥 |
| `safe_search` → `safeSearch` | 模块默认 `Moderate`，可选 `Off/Moderate/Strict` |
| `device`、`no_cache` | 模块默认 `desktop`、false；控制设备与缓存 |
| `max_results`（网页直连） | 默认不额外截断；两个独立脚本未暴露 page 参数，每次获取一个 HTML 响应 |

SerpAPI Bing 单次返回数量上限本次未核实，不能将模块请求的 10 写成官方上限。统一 CLI `--limit` 默认不指定、0 表示不额外截断，实际仍请求 `count=10`；正数影响 `count` 和本地切片。模块每次只取一页，页码偏移仍固定按 10 计算，调整 `count` 不会改变该计算。中国与国际网页直连也只请求指定 HTML 单页，官方未承诺此实现的固定返回数量；没有自动翻页。

## 统一 CLI 与证据

API adapter 仅取 results，丢弃脚本外层查询参数和条数；直连 adapter 同样取 results。各自字段原样进入 `data.items[]` 或 `data.results.<平台>.items[]`，平台为 bing、bing_cn_direct、bing_int_direct；联合 `data.final_items[]` 增加 `_source_platform`。这两个直连入口当前不经过 structured_results 统一字段转换。外层 ok/errors 是执行状态。

已核对源码、adapter、`.work/output-analysis/api.json` 与 no-api.json。API 和国际直连各三条，类型符合上表；中国直连成功但为空，无法验证条目实例。API 完整原始响应与网页 HTML 未保存；空结果不能证明页面没有结果，也不能用来确认字段可空性。未独立验证其他页码、语言及国家条件。
