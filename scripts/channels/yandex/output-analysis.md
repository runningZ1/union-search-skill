# Yandex 输出结果分析

覆盖 `yandex_search.py`、`yandex_no_api.py`、`union_search.py::_search_yandex/_search_native_web` 及 structured_results。API 与网页直连的正常输出经过不同转换。

## API 原始结构与完整字段

SerpAPI 读取顶层 `organic_results[]`，模块先限量，再为每项生成以下全部字段。

| API 模块字段 | 类型、来源与缺失规则 |
| --- | --- |
| title | 实测 string；原 title，缺失为空字符串 |
| href | 实测 string；原 link，缺失为空字符串 |
| body | 实测 string；原 snippet，缺失为空字符串 |
| displayed_link | 实测 string；原同名字段，缺失为空字符串 |

显式 null 原样保留，不过滤空地址与标题。脚本外层为 query/page/lang/lr/total_results/results，其中 total_results 为本地条数。其他上游字段和元数据不保留；源码没有分数映射。

## 网页直连完整字段与映射

上游为 `/search/site/` 的 HTML，读取 b-serp-item、唯一的 h3 标题链接、b-serp-item__text。模块生成 title、url、content、href、body、engine 六个字段，均为 string；href 等于 url、body 等于 content、engine 固定 yandex。缺少唯一标题链接或无结果容器直接失败，空摘要允许，标题和 HTTP 地址由公共 result 函数校验。

进入 adapter 后转换成完整字段集合：title/string、url/string、content/string、published/null、thumbnail/null、sources/array。文本清理 HTML/空白，url 删除 fragment 与已知跟踪参数；原 href/body/engine 不直接保留。sources[] 包含 platform=yandex_direct、engine=yandex、rank/integer，rank 是返回位置，不是评分。

## 容量概览

| 官方每请求上限 | 模块默认 | 分页行为 | `--limit` 作用 |
| --- | --- | --- | --- |
| API 上限未知，官方默认 20 个分组不能换算为条数上限；直连固定条数未知 | 两种入口均 `page=1`、`max_results=None`；API 不发送 groups_on_page | 两种入口每次取指定单页，`p=page-1`；均无自动分页 | 不指定或 0 不额外截断；正数仅本地切片，不改变 API groups_on_page 或直连请求数量 |

本地样例：[API 主样例](examples/search-result.json)、[网页直连样例](examples/search-result-yandex_direct.json)。这些文件保存真实 CLI 成功渠道对象，非原始 HTTP 响应；同名 `-info.json` 文件记录查询时间与来源层次。

## 常用参数与单次容量

核查日期：2026-10-25。官方来源：[SerpAPI Yandex Search API](https://serpapi.com/yandex-search-api)。当前商业入口使用 SerpAPI。

| 英文参数 | 含义、默认与范围 |
| --- | --- |
| `query` → `text` | 查询文本 |
| `page` → `p` | 模块默认 1，第二页起发送 `page-1`；官方 p 从 0 开始 |
| `max_results` | 模块默认 `None`，仅本地切片，不发送结果数量 |
| `yandex_domain` | 模块与官方默认 `yandex.com` |
| `lang`、`lr` | 模块默认 `en`、`84`；官方该域名默认语言 en、地区 84（美国） |
| `groups_on_page` | 官方每页分组数默认 20，未列最高值；模块未发送或暴露该参数 |
| `page/max_results/timeout`（网页直连） | 默认 1、None、20 秒；发送 `p=page-1`，数量仅本地截取 |

官方当前文档未公布单次结果的数值上限；默认 20 个分组也不能直接当作 20 条有机结果或硬上限。统一 CLI `--limit` 默认不指定、0 表示不额外截断；正数只影响本地截取，不会修改 groups_on_page，也不会自动翻页。商业入口每次取一个选定页。网页直连使用 `/search/site/` HTML，官方未承诺当前端点的固定单页数量；同样只取指定单页。

## CLI 与证据范围

API 条目四字段进入 `data.items[]` 或 `data.results.yandex.items[]`，联合 final_items 增加 `_source_platform`。直连保留转换后的六字段，位于相应 yandex_direct 路径；只有全部渠道均适用结构化网页格式的联合搜索，final_items 才增加 id 并按该格式合并来源，混合渠道批次仍可能带 `_source_platform`。脚本外层查询与条数不保留，统一 CLI 外层 ok/errors 表示执行状态。

已核对两份实现、adapter、公共结果转换及 `.work/output-analysis/api.json/no-api.json`，两个入口各三条成功；直连 published/thumbnail 为 null，sources 为数组。实测未保存完整原始 JSON/HTML；其他地域、页码、非空日期和缩略图未验证。
