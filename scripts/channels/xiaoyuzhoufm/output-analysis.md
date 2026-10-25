# 小宇宙 FM 输出结果分析

## 容量表与结果留样

| 官方单次上限 | 模块默认 | 分页 | `limit` 作用 |
| --- | --- | --- | --- |
| 秘塔 podcast scope 的官方数量范围与最大条数未确认 | 独立 `size=10`，请求体发送字符串 `"10"`；本地没有数字上限 | 每次请求一次，不传 page 或游标，不自动翻页 | 统一正数传为 size 并对 podcasts 本地截取；统一 `0` 仍使用默认 size=10，不能据此扩大响应 |

真实播客结果见 [搜索结果样例](examples/search-result.json)。文件保存统一 CLI 的 `data.results.xiaoyuzhoufm` 渠道对象，属于 CLI 渠道对象证据层；仅保留服务 podcasts 数组及本地状态，未保存完整 HTTP 响应或服务顶层积分、查询参数。容量依据下文已有资料，3 条样例不代表 podcast 上限。

## 常用参数与返回数量

资料整理日期：2026-10-25。依据 `xiaoyuzhou_search.py`、统一编排与秘塔官方 API 页面；此次未重新执行搜索。

| 参数 | 含义 | 默认值或未指定行为 | 范围与实际约束 |
| --- | --- | --- | --- |
| `query` | 播客查询关键词 | 必填 | 原样发送为 `q`，scope 固定为 `podcast` |
| `--size/-s` | 请求返回的播客数量 | `10`，请求体发送字符串 `"10"` | argparse 接受整数；本地未校验正数，也未设置数字上限；官方 podcast 有效范围未确认 |
| 统一 `--limit` | 每渠道输出数量上限 | 未指定或 `0` 解析为 `None`，独立模块继续使用 size=10 | 正整数传为 `--size N`，随后对 podcasts 本地切片；不增加分页 |
| `--summary` / `include_summary` | 请求 AI 摘要 | `false` | 布尔值，发给 `includeSummary`；统一编排默认未启用 |
| `--concise/-c` / `concise_snippet` | 请求简洁片段 | `false` | 布尔值，发给 `conciseSnippet` |
| `--json/-j` | 输出完整服务 JSON | `false`，默认文本格式 | 开启后保留服务顶层；统一渠道只保留 podcasts 数组 |
| 函数 `base_url` | 实际搜索服务主机 | `metaso.cn` | 目标为 `/api/v1/search`，没有独立 CLI 选项 |
| 函数 `timeout` | HTTPS 请求超时 | `30` 秒 | 没有独立 CLI 选项；统一编排的子进程等待期限为 60 秒 |

**官方 podcast 每请求数量上限未确认。** 此模块调用秘塔搜索服务，不能引用小宇宙网站自身的搜索上限。秘塔公开 Playground 能确认 `POST /api/v1/search` 以及 size/page 参数入口，但可读取页面未列出 podcast scope 的 size 最小值、最大值或专属承诺，不能把网页搜索的范围直接用于播客。

本实现只发送一次请求，没有 page、游标或自动翻页；独立模块也没有对服务返回数组再次切片。因此本地请求参数没有固定数字上限，实际响应数量由服务决定；默认仅请求 10 条，不表示保证返回 10 条。统一 limit 额外截断已经取得的 podcasts，无法扩大服务响应；不指定统一 limit 仍使用模块默认 size=10。索引覆盖、相关性、账号权限、积分额度及服务端动态限制可能使结果减少或请求失败。

官方来源（资料整理日期：2026-10-25）：[秘塔搜索 API Playground](https://metaso.cn/search-api/playground)。已核对公开入口；podcast 专属最大条数及有效范围未取得可确认的官方说明。

## 来源与输出层次

覆盖统一渠道 `xiaoyuzhoufm`。本目录通过秘塔 `/api/v1/search` 的 `scope: podcast` 检索播客，模块直接返回服务 JSON，没有自行抓取音频或小宇宙详情页。独立脚本 `--json` 输出完整响应；统一编排仅取 `podcasts` 数组，保存在单渠道 `data.items` 或联合 `data.results.xiaoyuzhoufm.items`。

顶层格式化器读取 `podcasts`、`total`、`credits`、`searchParameters`。这些是源码已使用的响应位置；本轮联合结果没有保存完整服务顶层，不能据此断言每次都具备这些字段。`searchParameters.q` 是回显查询，`credits` 是服务积分计数，`total` 与本地截断后的条数可能不同。

## 播客条目字段

条目原样保留，以下字段由实现消费且在本轮真实结果中出现。

| 字段 | 本轮类型 | 语义与缺失行为 |
|---|---|---|
| `title` | string | 播客单集标题；模块不保证非空 |
| `link` | string | 来源页面链接，使用此名称；没有自动增加 `href` 或 `url` |
| `snippet` | string | 搜索摘要/片段，不是音频全文转写 |
| `authors` | array | 作者或主播列表；不能将整组数组作为单一作者字符串 |
| `date` | string | 服务返回的日期文本；模块不统一格式或时区 |
| `duration` | string | 原始时长；文本显示逻辑尝试按秒转成分秒，但 JSON 不做该转换 |
| `score` | string | 服务相关性值；没有跨渠道统一标尺 |
| `position` | integer | 服务提供的位置，保持原值 |

接口结果没有被模块重建，因此服务新增字段也可能保留；未返回的字段不会补齐。JSON 中字段缺失、`null`、空字符串需要分别处理，文本显示时的“无摘要”“佚名”“未知”不代表原始 JSON 存在这些值。

## 条件字段与 CLI 边界

`--summary` 请求 AI 摘要，`--concise` 改变摘要长度；本轮均未启用，无法由本轮样本确认新增摘要的实际位置。统一 CLI 只传数量与关键词，不把顶层 `credits`、`searchParameters` 复制到每条结果。联合输出增加的 `_source_platform` 属于本地来源标记。

没有确定的商品价格、面料成分、品牌、播放数、点赞数或音频下载 URL。`link` 可定位单集页面，不能直接作为媒体文件地址。

## 验证范围

关键词 `sustainable apparel textile industry` 返回 3 条播客，字段列表已与 `.work/output-analysis/api.json` 的 `data.results.xiaoyuzhoufm.items` 核对。实现依据 `xiaoyuzhou_search.py` 的 `search_podcasts()`、`format_result()` 与编排器 `_search_xiaoyuzhoufm()`。完整服务顶层及可选摘要结构未单独采样。
