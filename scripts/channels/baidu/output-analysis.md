# 百度输出结果分析

覆盖 `baidu_search.py`、`baidu_no_api.py`、`union_search.py::_search_baidu/_search_native_web` 和 structured_results。

## 千帆 API 与完整字段边界

原生入口读取 `references[]`，直接删除每个对象的 snippet 后返回，其他字段全部透传；脚本输出 JSON 数组。以下列出本次全部保留字段，模块没有固定白名单。

| 字段 | 实测类型与用途 |
| --- | --- |
| id | integer；上游引用标识 |
| url、title、date | string；地址、标题和原始日期文本 |
| content、markdown_content | string；上游内容与 Markdown 内容，不做截断 |
| icon、web_anchor、type、website | string；图标、网页锚点、类型和网站信息，原值保留 |
| video、image、aladdin | null；非空结构未验证 |
| is_aladdin | boolean；上游标记 |
| web_extensions | object；实测 images 为 array 或 null，author_info 为 null |
| rerank_score、authority_score | integer；上游评分原值，无数值尺度和等级方向验证 |

缺失字段不补默认值，显式 null 保留。references 缺失默认 []，但显式 null 未转换；顶层 code 非空会失败。snippet 被删除后无法由输出恢复；服务其他顶层字段均不返回。adapter 接受数组并限量，不进一步修改这些条目；CLI 位于 `data.items[]` 或 `data.results.baidu.items[]`，联合 final_items 增加 `_source_platform`。

## 网页直连与完整字段

上游是 HTML，模块解析 content_left 结果容器，标题取 h3/c-title，地址优先 data-tools.url 或 mu，摘要组合 summary-text/c-abstract 等节点；排除广告及特定图片、视频入口。

模块全部字段为 title、url、content、href、body、engine、link_type：前六项 string，href=url、body=content、engine=baidu，link_type 为 direct 或 redirect。缺标题跳过，空摘要允许，地址需为 HTTP(S)；保留的百度跳转链接标记 redirect。

adapter 转换为 title/string、url/string、content/string、published/null、thumbnail/null、sources/array，清理文本与跟踪参数。sources[] 保存 platform、engine、rank，跳转条目另有 link_type=redirect；原重复别名不保留。全部渠道均采用结构化网页格式时，联合 final_items 另增 id 并支持合并来源。统一外层 ok/errors 为执行信息。

## 容量概览

| 官方每请求上限 | 模块默认 | 分页行为 | `--limit` 作用 |
| --- | --- | --- | --- |
| 千帆网页资源 50 条；网页直连固定条数未知 | API 请求 10 条；直连 `max_results=None`，不额外截断 | API 未公布分页参数；直连固定第一页；均无自动分页 | 不指定或 0 时 API 仍请求 10；正数传为 `count`，最多 50，再本地切片；直连仅本地截取 |

本地样例：[API 主样例](examples/search-result.json)、[网页直连样例](examples/search-result-baidu_direct.json)。这些文件保存真实 CLI 成功渠道对象，非原始 HTTP 响应；同名 `-info.json` 文件记录查询时间与来源层次。

## 常用参数与单次容量

核查日期：2026-10-25。官方来源：[百度搜索 API](https://ai.baidu.com/ai-doc/AppBuilder/pmaxd1hvy)。

| 英文参数 | 含义、默认与范围 |
| --- | --- |
| `query` → `messages[-1].content` | 查询文本；模块构造一条 user 消息 |
| `count` → `resource_type_filter[].top_k` | 模块脚本默认 10，非正数改为 10，大于 50 改为 50；资源类型固定 `web`。官方 web 默认 20，最高 50 |
| `search_source` | 模块固定 `baidu_search_v2`，官方支持该值 |
| `freshness` → `search_filter.range.page_time` | 模块支持 `pd/pw/pm/py` 或 `YYYY-MM-DDtoYYYY-MM-DD`，默认不限时间；生成 `gte/lt` 日期边界 |
| `search_filter.match.site` | 官方支持最多 20 个站点；当前模块脚本未暴露该筛选入口 |
| `max_results`、`timeout`（网页直连） | 默认不额外截断、15 秒；当前实现固定请求第一页，未暴露 page 参数 |

官方网页资源单次最多 50 条，未公布分页参数；统一 CLI `--limit` 默认不指定，0 表示不额外截断，此时脚本仍请求 10。正数传入 `count` 后受上述 50 条处理，再进行 adapter 本地切片。模块底层 `baidu_search(api_key, request_body)` 接受已构造请求体，不负责上述脚本默认值。百度网页直连每次只请求指定 HTML 页面，未核实官方对该直连端点承诺固定单页条数；扩大本地数量不能取得后续页面。

## 证据范围

依据源码、adapter、公共转换及 `.work/output-analysis/api.json/no-api.json`。API 三条成功，类型如表；原始响应未保存。网页直连本次在解析 data-tools 的 JSON 时失败，零条结果，其字段仅有源码证据；未验证跳转地址、非空媒体对象及评分语义。
