# 网页公共输出结构分析

本目录提供网页解析与请求状态的公共实现，不对应独立搜索来源。各服务的原生 HTML/JSON 字段、容量与样例见下列索引。

## 容量表与服务索引

| 官方单次上限 | 模块默认 | 分页 | `limit` 作用 |
| --- | --- | --- | --- |
| 公共模块无独立服务容量，按具体渠道的官方约束与实际响应确定 | 统一 CLI `--limit 0` 表示不做本地截取；具体模块仍有自己的默认请求容量 | 公共层不自动遍历全部页面，页码参数按渠道实现处理 | 正数限定每渠道保留数；`0` 不能取消服务单次请求或分页限制 |

| 服务 | 输出分析、容量及真实留样入口 |
| --- | --- |
| Brave | [Brave 输出分析](../brave/output-analysis.md) |
| DuckDuckGo 网页 | [DuckDuckGo 输出分析](../duckduckgo/output-analysis.md) |
| DuckDuckGo Instant | [Instant Answer 输出分析](../duckduckgo_instant/output-analysis.md) |
| Ecosia | [Ecosia 输出分析](../ecosia/output-analysis.md) |
| 集思录 | [集思录输出分析](../jisilu/output-analysis.md) |
| Mojeek | [Mojeek 输出分析](../mojeek/output-analysis.md) |
| Qwant | [Qwant 输出分析](../qwant/output-analysis.md) |
| 夸克 | [夸克输出分析](../quark/output-analysis.md) |
| 360 搜索 | [360 输出分析](../so360/output-analysis.md) |
| 搜狗 | [搜狗输出分析](../sogou/output-analysis.md) |
| Startpage | [Startpage 输出分析](../startpage/output-analysis.md) |
| 今日头条 | [今日头条输出分析](../toutiao/output-analysis.md) |
| Wolfram Alpha | [Wolfram Alpha 输出分析](../wolfram/output-analysis.md) |
| Yahoo | [Yahoo 输出分析](../yahoo/output-analysis.md) |
| 百度 | [百度输出分析](../baidu/output-analysis.md) |
| Bing | [Bing 输出分析](../bing/output-analysis.md) |
| Google | [Google 输出分析](../google_search/output-analysis.md) |
| Yandex | [Yandex 输出分析](../yandex/output-analysis.md) |

公共模块不单独留存搜索样例。各服务样例的证据层为 CLI 渠道对象或独立入口响应，具体以对应文档标注为准；字段可能经过解析、标准化与本地状态包装，未保存原始 HTTP 响应的样例不能证明完整上游格式。空结果与失败记录只证明调用状态。

## 统一网页条目

联合搜索的每个渠道经过 `union_search/structured_results.py` 的 `normalize_item()` 后使用以下结构。

| 字段 | 类型 | 构造规则 |
|---|---|---|
| `title` | string | title/name/Title/full_name，清理 HTML、实体及连续空白；空标题失败 |
| `url` | string | 优先 html_url，其次 link/href/permalink/source_url/Url/url；必须是绝对 HTTP(S) 地址 |
| `content` | string | content/body/description/snippet/summary/Snippet 中首个非空值，清理文本；未取得则为空字符串 |
| `published` | 上游值/null | 从 published/publishedDate/published_at/publish_date/date 取值；不统一日期格式 |
| `thumbnail` | 上游值/null | thumbnail；不代表原图文件 |
| `sources` | array[object] | 原有来源数组或本地构造的 platform、engine、rank；rank 从 1 开始 |
| `id` | integer | 合并输出时按最终数组从 1 编号，属于结果集内编号 |

url 会移除片段、`www` 前缀及已知 utm_*、gclid、fbclid、msclkid、spm、pvid、scene、wfr、for 查询项。Yahoo 的 `RU` 与 Bing 的 `u` 跳转参数会先还原目标页面。显式 `link_type: redirect` 可传入 sources 的首个对象。每次联合搜索都去重：相同 url、相同标题，以及与当前保留标题相似度达到 0.9 的标题合并为一条，合并 sources，并保留更长 content。

## 渠道与信封字段

统一 CLI 顶层包含 schema_version、ok、type、data、meta，以及兼容字段。单渠道 `data.items` 与联合 `data.results.<渠道>.items` 保存渠道数组；联合 `data.channels` 保存 platform、status、count、duration_ms、error，`data.timing` 保存批次耗时与截止预算。这些状态字段属于项目生成信息。

全部联合搜索渠道都执行上述标准化，`final_items` 使用标准条目并增加 `id`。单渠道原始响应仍保留在各服务样例中；`id` 在合并阶段生成，渠道内条目不一定带 `id`。

## 常用参数与数量规则

| 参数 | 一般含义与默认行为 |
|---|---|
| `query` | 必填搜索词，发送到所选服务 |
| `--limit` | 统一 CLI 默认 0，表示不做本地条数截断；正整数限定每渠道保留数，不承诺上游返回足量结果 |
| `--preset` | 联合搜索的数量预设，small/medium/large/extra 分别为 3/5/10/20 |
| `--timeout` | 请求及编排超时预算，不能理解为搜索时间范围 |
| `--param page=N` | 单渠道透传页码，仅具体实现支持时有效；不会自动遍历全部页面 |
| `--param timelimit/region/country/safesearch/proxy=...` | 时间范围、地区、安全搜索及代理，支持集合由各服务决定；不支持时失败 |
| `--deduplicate` | 联合搜索按地址合并结果，合并后数量可能减少 |

公共模块没有独立的每次搜索条数上限。网页结果按当前一次响应解析，缺失、广告过滤、重复和页面结构均会影响实际数量。`--limit 0` 只保留本次取得的全部条目，不取消服务分页或单次请求限制。各服务的官方上限、请求数量与模块截断位置见其文档。

本节依据本项目 `union_search_cli.py search --help`、`platform --help` 与当前编排实现，核查日期为 2026-10-25。公共模块没有独立官方服务配额。

## 验证边界

`.work/output-analysis/no-api.json` 确认 Brave、Yahoo、搜狗、360、DuckDuckGo、夸克与 Yandex 网页返回标准条目。其他网页实现可能返回 title/href/body/engine，必须按各目录文档读取。成功零条无法证明页面真实无内容；HTTP 403、解析错误与验证码不能当作正常空集合。本文只描述格式，不规定评分、关键词或时间筛选规则。
