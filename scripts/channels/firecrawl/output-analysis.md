# Firecrawl 输出结果分析

覆盖 `firecrawl_search.py` 客户端、便捷函数、JSON 脚本和 `union_search.py::_search_firecrawl`。请求 `/v2/search`；源码接受 `data.web/news/images` 三类数组，也兼容 data 直接为数组的网页结构。

## 完整模块字段及映射

以下描述条件字段集合，未出现的条件字段不会补 null。

| 字段 | 类型、来源与条件 |
| --- | --- |
| title | string；网页 title 或 metadata.title，新闻 title，图片 title；空值使用对应 href |
| href | string；网页 url 或 metadata.sourceURL；新闻 url；图片 imageUrl |
| body | string；网页 description 或 metadata.description；新闻 snippet 或 description；图片为原 url |
| engine | string；固定 firecrawl |
| source_type | string；web、news、image，由处理分支生成 |
| position | 上游 position 或各分类从 1 开始的序号；实测网页为 integer |
| category | 仅网页 category 非空时保留原值 |
| markdown | 仅网页 markdown 非空时保留原值，通常 string |
| metadata | 仅网页 metadata 非空时保留原对象 |
| date、image | 仅新闻；来自 date、imageUrl，缺失为 null |
| page_url | 仅图片；原 url，缺失为空字符串 |
| width、height | 仅图片；imageWidth、imageHeight，缺失为 null |

网页和新闻缺少目标地址时丢弃；图片缺少 imageUrl 时丢弃，href 此时是图片资源地址。source_type 决定 body 与 href 的语义；position 是分类内位置，不能作为跨分类分数。模块没有相关性分数字段。

## 保留与统一 CLI

结果按网页、新闻、图片顺序拼接，最后统一切片，因此限量可能使后面的分类不出现。scrape 开启后可产生 markdown/metadata；其他抓取格式即使服务返回，也没有通用保留逻辑。上游 success/error、其他条目字段和顶层元数据不进入模块正常结果。

非 200、success 为 false 或 data 类型不受支持时失败。脚本包装 results；adapter 保留条目并再次限量，进入 `data.items[]` 或 `data.results.firecrawl.items[]`；联合 `data.final_items[]` 添加 `_source_platform`，外层 ok/errors 是执行状态。

## 容量概览

| 官方每请求上限 | 模块默认 | 分页行为 | `--limit` 作用 |
| --- | --- | --- | --- |
| 每来源 100 条 | 每来源请求 `limit=10`；来源默认 `web` | 官方 schema 未公布分页参数；模块无自动分页 | 不指定或 0 时仍请求每来源 10；正数发送为 `limit`，并对各来源合并结果整体本地切片 |

本地样例：[examples/search-result.json](examples/search-result.json)。此文件保存真实 CLI 成功渠道对象，非原始 HTTP 响应。

## 常用参数与单次容量

核查日期：2026-10-25。官方来源：[Search v2](https://docs.firecrawl.dev/api-reference/endpoint/search)。

| 英文参数 | 含义、默认与范围 |
| --- | --- |
| `max_results` → `limit` | 模块默认 `None` 时发送 10；官方默认 10、范围 1—100，多来源时分别适用于每个来源 |
| `sources` | 模块默认 `["web"]`；实现可处理 `web/news/images`，当前官方另列 `alexandria`，模块未映射其 tools |
| `categories` | 模块默认不发送；官方列出 `developer/gov/research/pdf`，`gov` 需单独使用 |
| `include_domains/exclude_domains` → `includeDomains/excludeDomains` | 域名筛选，默认不发送 |
| `tbs` | 时间或排序筛选，默认不发送；例如 `qdr:d/w/m/y` |
| `location`、`country` | 地理位置与国家，模块默认不发送；官方 country 默认 `US` |
| `scrape`、`formats` → `scrapeOptions.formats` | 模块默认不抓取；开启时默认 `["markdown"]` |

官方单次每来源最多 100 条。模块按 web、news、images 合并后再次执行整体 `max_results` 切片，因此本地总条数可能小于各来源容量之和。统一 CLI `--limit` 默认不指定、0 表示不额外截断，此时仍请求每来源 10；正数传入服务 `limit` 并用于合并后的本地截断。官方此 schema 未公布分页参数，模块也没有自动分页；服务返回数量还受匹配结果影响。

## 证据范围

已核对源码、adapter 和 `.work/output-analysis/api.json` 三条成功网页结果，实际只有六个基础字段，position 为 integer，其余为 string。新闻、图片、抓取正文和 metadata 内部字段均仅有源码映射证据；未保存完整原始 HTTP 响应，不补充虚构结构。
