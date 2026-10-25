# Google 输出结果分析

覆盖 `google_search.py`、`google_no_api.py`、`google_hk_no_api.py`，以及 `union_search.py::_search_google/_search_no_api_direct`。

## Custom Search 原始结构与模块字段

客户端返回 `response.json()` 整体，脚本 --json 透传完整对象；没有模块字段白名单。源码明确使用 items、queries.request[].searchTerms、searchInformation.formattedTotalResults/formattedSearchTime；图片展示还访问 items[].image.width/height/thumbnailLink。这些访问路径不代表原始完整响应。

| items[] 字段 | 实测类型及保留情况 |
| --- | --- |
| kind、title、htmlTitle | string；资源类型、纯文本与带标记标题 |
| link、displayLink | string；目标地址与展示域名 |
| snippet、htmlSnippet | string；纯文本与带标记片段 |
| formattedUrl、htmlFormattedUrl | string；展示地址，不应等同于目标 link |
| pagemap | object；实测 cse_thumbnail、cse_image、metatags 及 Event 等可变键，其值为 array |
| image（条件字段） | 图片搜索展示逻辑使用的对象；本次网页搜索未观察，完整子字段未证实 |
| 其他字段 | 客户端和 adapter 均透传，缺失不补值、null 不转换 |

上表覆盖本次实际条目字段，并标出代码条件路径。pagemap 保存网页提取的可变元数据，不能假定每条都有相同键。模块不清洗、限长或过滤地址，不生成评分。API 请求 num 限制在 1—10。

## 网页直连完整字段

两个直连入口上游均为 HTML，解析 g/tF2Cxc 容器中的 h3 标题、a.href 及 IsZvec/VwiK3b 摘要；国际入口还支持 vvjwJb 标题。模块全部字段为 title、href、body、engine，均由解析器生成 string；engine 分别为 google、google_hk。缺标题或链接跳过，地址须以 http 开头，缺摘要为空字符串。模块会拼接容器中的链接值，未保证一定只有一个目标。页面其他元数据未保留，解析异常条目跳过。

## 容量概览

| 官方每请求上限 | 模块默认 | 分页行为 | `--limit` 作用 |
| --- | --- | --- | --- |
| Custom Search 10 条；两个直连入口固定条数未知 | API `num=10`、客户端 `start=1`；直连不额外截断 | API 累计仅可访问前 100 个匹配项，当前脚本与 adapter 未暴露 start；直连每次一页；均无自动分页 | 不指定或 0 时 API 仍请求 10；正数经 `num` 限制到 10 后本地切片；直连仅本地截取 |

本地样例：[examples/search-result.json](examples/search-result.json)。此文件保存真实 CLI 成功渠道对象，非原始 HTTP 响应。

## 常用参数与单次容量

核查日期：2026-10-25。官方来源：[Custom Search cse.list](https://developers.google.com/custom-search/v1/reference/rest/v1/cse/list)。

| 英文参数 | 含义、默认与范围 |
| --- | --- |
| `query` → `q`、`cx` | 查询与搜索引擎标识，凭据之外的必需请求信息 |
| `num` | 模块默认 10，发送时限制到 1—10；官方每次最多 10，默认 10 |
| `start` | 客户端默认 1，结果起始位置，从 1 开始；独立脚本和当前统一 adapter 未暴露此参数 |
| `lr` | 文档语言限制，客户端默认不指定；脚本 `--lang` 添加 `lang_` 前缀 |
| `search_type` → `searchType`、`img_size` → `imgSize` | 默认网页；图片模式发送 `image`，尺寸仅图片模式生效 |
| `max_results`（网页直连） | 默认不额外截断；两个独立脚本未暴露 page 参数，每次获取一个 HTML 响应 |

官方 Custom Search 单次最多 10 条，累计仅能访问前 100 个匹配项，官方注明 `start + num > 100` 会报错。累计可访问数量不等于单次容量。统一 CLI `--limit` 默认不指定、0 表示不额外截断，此时实际请求 10；正数经 `num` 限制到 10，再做本地切片，没有自动分页。两个网页直连入口也只请求指定单页，官方未承诺这些 HTML 解析入口固定返回条数，不能套用 Custom Search 数值。

## CLI 与证据范围

API adapter 仅取 items 并限量，顶层分页、查询、统计等随之丢弃；直连 adapter 取 results，不经过 structured_results 转换。单渠道为 `data.items[]`，联合为 `data.results.google/google_direct/google_hk_direct.items[]`，联合 final_items 增加 `_source_platform`；外层 ok/errors 为执行信息。

已核对源码、adapter 和 `.work/output-analysis/api.json/no-api.json`。API 三条成功，实际字段类型如表；两个直连入口均成功但为空，不能验证条目类型或页面是否真正无结果。完整原始 JSON/HTML 未保存，图片搜索与 pagemap 其他结构未验证。
