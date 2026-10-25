# GitHub Search 输出结果分析

## 容量表与结果留样

| 官方单次上限 | 模块默认 | 分页 | `limit` 作用 |
| --- | --- | --- | --- |
| 每请求最多 100，每个查询最多开放 1000；API `per_page` 默认 30 | 独立 `limit=None` 将累计目标设为 1000，分页请求实际使用 `min(100, 剩余目标数)` | 自动请求第 1–10 页，短页、达到 total_count 或累计目标时停止 | 统一正数传给模块累计目标并再次本地截取；大于 1000 按 1000 处理；统一 `0` 采用模块默认目标 |

真实仓库结果见 [搜索结果样例](examples/search-result.json)。文件保存统一 CLI 的 `data.results.github` 渠道对象，属于 CLI 渠道对象证据层；仓库条目保留远端字段，模块已移除远端顶层 `total_count/incomplete_results`，未保存原始 HTTP 响应及响应头。容量依据下文已有资料，3 条仓库样例不验证代码、Issue 或 PR 输出。

## 常用参数与返回数量

资料整理日期：2026-10-25。依据本目录源码与官方 REST Search 文档；此次未重新执行搜索。

| 参数 | 含义 | 默认值或未指定行为 | 范围与实际约束 |
| --- | --- | --- | --- |
| `repo/code/issue` 与 `query` | 资源类型、关键词及 GitHub 查询限定符 | 子命令和查询必填；统一渠道固定使用 `repo` | 查询语法由对应官方 Search 接口验证 |
| `--limit` | 独立 CLI 的累计目标数量 | `None`，实现将目标设为 `1000` | 大于 `1000` 按 `1000` 处理；没有正数校验，零或负数使循环不执行 |
| 统一 `--limit` | 每渠道输出上限，同时传给独立 CLI | 未指定或 `0` 解析为 `None` | 正整数向上游传递并在返回后再次切片；不指定仍受 1000 条开放范围限制 |
| 客户端 `per_page` | 方法签名中的每页数量 | `30` | 分页循环会覆盖此值为 `min(100, 剩余目标数)`；实际通常为 `100`，最后一页可能减少；独立 CLI 没有此选项 |
| `--sort` / `--order` | 排序字段与方向 | sort 不发送，使用服务相关性排序；order 为 `desc` | repo：`stars/forks/help-wanted-issues/updated`；issue：`comments/reactions/interactions/created/updated`；code 的本地选项为 `indexed`，远端是否接受由对应 API 决定；方向为 `asc/desc` |
| `--language/--user/--repo` 等 | 添加资源查询限定符 | 均不指定 | 参数按子命令提供；如仓库 stars、topic，代码 path、extension，Issue state、author、label |
| `--is-pr/--is-issue` | Issue 子命令的资源类型 | 均不指定也添加 `type:issue` | `--is-pr` 添加 `type:pr`，同时指定时优先 PR |
| `--token` | GitHub 认证 | 读取已有 `GITHUB_TOKEN` | code 搜索需要认证；可见范围由权限决定 |
| `--format` / `--output` | 展示与输出位置 | `text`、stdout | `text/json/markdown`；JSON 保留原生条目 |

**官方每请求最多 100 条，每个搜索查询最多开放 1000 条。** 官方 `per_page` 默认 `30`，当前模块主动覆盖为最多 `100`。客户端自动请求 `page=1..10`，每页按剩余目标数取值，短页或达到远端 `total_count` 时停止；未指定 limit 最多请求十页。统一 limit 同时影响请求目标与返回后本地切片，无法突破官方开放范围，也不保证实际返回足额。

`total_count` 可以大于 1000；`incomplete_results=true` 表示搜索覆盖不完整。权限、索引范围、搜索超时、动态内容和频率限制均可能减少结果或使请求失败，多页结果没有固定快照承诺。页数上限与请求频率限制属于不同维度；代码搜索的认证及专用频率约束也不能用普通仓库搜索额度替代。

官方来源（资料整理日期：2026-10-25）：[REST Search：仓库、代码、Issue 参数与搜索限制](https://docs.github.com/en/rest/search/search?apiVersion=2022-11-28)。

## 依据与验证范围

依据 `github_search.py`、`scripts/union_search/union_search.py`、`scripts/cli/adapters.py` 和 `scripts/cli/output.py` 当前实现。分析限于字段、类型、可空性、来源映射和 CLI 保留。

真实样本为根目录 `.work/output-analysis/no-api.json`，查询为 `sustainable apparel textile industry`。其中 `data.results.github.success=true`、`total=3`、`status="success"`，三个条目均为仓库对象。首条为 `ruhianjum0425-code/apparel-textiles-data-integration`。联合搜索顶层 `ok=false` 来自同次调用的其他渠道失败，不影响 GitHub 独立成功结果。代码、Issue 和 PR 没有本次真实样本，相关字段只依据实现访问点说明；实现没有定义完整远端 schema，不能据此认定其他字段一定存在。

## 实际支持的资源类型与容器

| 独立 CLI 命令 | 客户端方法 | 远端资源及输出 |
| --- | --- | --- |
| `repo` | `search_repositories` | `/search/repositories`，仓库对象数组 |
| `code` | `search_code` | `/search/code`，代码文件对象数组 |
| `issue` | `search_issues` | `/search/issues`，Issue 或 PR 对象数组；格式化器以条目是否包含 `pull_request` 区分 |
| `rate-limit` | `get_rate_limit` | 额度状态，独立于搜索结果结构 |

代码文件搜索返回文件元数据，当前实现没有读取文件正文。PR 复用 Issue 搜索方法，没有独立 `pr` 命令。用户、提交、讨论等资源没有对应搜索方法和输出分支。

三个搜索方法的 JSON 返回均为：

| 字段 | 类型、默认值与来源 |
| --- | --- |
| `total_count` | 预期 `integer`，来自远端同名字段，缺失默认 `0`；是远端匹配数量，不等于本地 `items` 长度 |
| `incomplete_results` | 预期 `boolean`，来自远端同名字段，缺失默认 `false` |
| `items` | `array<object>`，累积远端各页 `items`；条目内部字段原样保留 |

该容器由客户端重新构造，仅保留这三个顶层字段。多页情况下 `total_count/incomplete_results` 使用最后一次响应的值。没有新增 `resource_type` 字段，也没有把远端其他顶层元数据、HTTP 响应头或分页链接写入 JSON。原生条目没有本地 schema 校验，字段缺失与显式 `null` 都可能保留；下面的类型是已观察类型或格式化器预期类型。

## 仓库条目：真实样本的完整字段分组

| 字段 | 样本类型与含义 |
| --- | --- |
| `id` | `integer`，仓库标识 |
| `node_id`、`name`、`full_name` | `string`，GraphQL 标识、仓库名、所有者/仓库名 |
| `private`、`fork`、`archived`、`disabled`、`allow_forking`、`is_template`、`web_commit_signoff_required` | `boolean`，可见性与仓库状态 |
| `has_issues`、`has_projects`、`has_downloads`、`has_wiki`、`has_pages`、`has_discussions`、`has_pull_requests` | `boolean`，远端仓库能力字段 |
| `description`、`language` | 本次均为 `string`；JSON 路径没有非空保证，格式化器明确处理空值 |
| `homepage` | 前两条为 `null`，第三条为 `string` |
| `mirror_url`、`license` | 本次均为 `null`；有值时形态未由本样本验证，JSON 输出直接保留 |
| `created_at`、`updated_at`、`pushed_at` | `string`，远端日期时间文本，未经本地转换 |
| `size`、`stargazers_count`、`watchers_count`、`forks_count`、`open_issues_count`、`forks`、`open_issues`、`watchers` | `integer`，规模及计数，全部原样保留 |
| `topics` | `array`，本次三条均为空数组，无法从样本确认元素类型 |
| `visibility`、`default_branch`、`pull_request_creation_policy` | `string`，可见性、默认分支和 PR 创建策略 |
| `permissions` | `object`，保留远端权限元数据；具体键依服务响应 |
| `score` | `number`，本次为 `1.0`；GitHub 搜索相关性分数 |
| `owner` | `object`，嵌套所有者信息，详见下文 |

样本中的地址字段均为 `string`，完整字段集合为：`html_url`、`url`、`forks_url`、`keys_url`、`collaborators_url`、`teams_url`、`hooks_url`、`issue_events_url`、`events_url`、`assignees_url`、`branches_url`、`tags_url`、`blobs_url`、`git_tags_url`、`git_refs_url`、`trees_url`、`statuses_url`、`languages_url`、`stargazers_url`、`contributors_url`、`subscribers_url`、`subscription_url`、`commits_url`、`git_commits_url`、`comments_url`、`issue_comment_url`、`contents_url`、`compare_url`、`merges_url`、`archive_url`、`downloads_url`、`issues_url`、`pulls_url`、`milestones_url`、`notifications_url`、`labels_url`、`releases_url`、`deployments_url`、`git_url`、`ssh_url`、`clone_url`、`svn_url`。`html_url` 为浏览器仓库页面，`url` 为 API 资源地址；若地址带 `{...}`，它是服务端 URL 模板，输出保留原文字。

样本 `owner` 包含 `login:string`、`id:integer`、`node_id:string`、`type:string`、`user_view_type:string`、`site_admin:boolean`、`gravatar_id:string`，以及字符串地址 `avatar_url/url/html_url/followers_url/following_url/gists_url/starred_url/subscriptions_url/organizations_url/repos_url/events_url/received_events_url`。嵌套 `owner.type="User"` 表示所有者种类，不表示搜索资源类型。

上述字段来自 GitHub 原生条目，适配器没有生成 `title`、`snippet` 或 `content`。字段集合可以随远端响应变化；样本中的 `null` 不会替换为空字符串。

## 代码文件与 Issue/PR：实现访问的字段

当前 JSON 输出对这些资源同样直接保留完整原生条目。以下字段由代码格式化器实际读取；本次没有成功样本验证其值及完整字段集合。

| 资源 | 字段路径 | 预期类型、空值处理与含义 |
| --- | --- | --- |
| 代码文件 | `repository` | `object`，格式化器缺失默认 `{}`；显式 `null` 会导致后续 `.get` 调用失败 |
| 代码文件 | `repository.full_name` | 预期 `string`，缺失显示 `N/A`；仓库名 |
| 代码文件 | `path` | 预期 `string`，缺失显示 `N/A`；仓库内文件路径 |
| 代码文件 | `html_url` | 预期 `string`，缺失显示空字符串；文件网页链接 |
| Issue/PR | `number` | 预期 `integer`，缺失显示 `N/A`；仓库内编号 |
| Issue/PR | `title`、`state` | 预期 `string`，缺失显示 `N/A` |
| Issue/PR | `comments` | 预期 `integer`，缺失显示 `0`；评论数量，未取得评论正文数组 |
| Issue/PR | `user`、`user.login` | 预期 `object` 与 `string`，缺失分别使用 `{}` 与 `N/A`；作者信息；显式 `user=null` 会导致格式化失败 |
| Issue/PR | `html_url` | 预期 `string`，缺失显示空字符串 |
| PR | `pull_request` | 判断依据为键是否存在，格式化器不读取其子字段，也不验证其值类型；存在该键即显示 PR/Pull Request |

`name/sha/url/repository` 的其他子字段、`body/labels/assignees/milestone/closed_at` 等可能由远端返回，当前实现会原样传递，但没有足够实现约束或本次样本来确认它们始终存在、可空性或完整形状。JSON 输出也没有自动添加 Issue/PR 的 `type` 字段；展示文字中的类型名称由格式化器即时生成。

## 独立 CLI 格式与统一 CLI 保留范围

独立 CLI 的 `--format json` 输出搜索容器与全部原生条目。text/Markdown 只展示有限字段：仓库展示 `full_name/stargazers_count/forks_count/language/description/html_url`；代码展示 `repository.full_name/path/html_url`；Issue/PR 展示 `number/title/user.login/comments/html_url` 及由 `state`、`pull_request` 派生的状态和类型文字。仓库的 `language/description` 为缺失、`null` 或空字符串时，会替换为展示占位文字；JSON 中原值保留。Markdown 的 Issue/PR 标题通过状态标记表达开闭状态。

统一 CLI 的 `_search_github` 固定调用 `github_search.py repo ... --format json`，只取容器的 `items`。因此：

- `data.results.github.items` 保留完整仓库对象及嵌套字段，`total_count` 和 `incomplete_results` 没有进入统一输出。
- `data.results.github.total` 为实际返回条目数；真实样本为 `3`，不能替代远端匹配总数。
- `data.final_items` 中复制仓库对象并增加 `_source_platform="github"`；没有补充通用 `title/url/snippet` 映射，原生 API `url` 与网页 `html_url` 并存。
- 统一 CLI 的 `search --platforms github` 和 `platform github` 均走仓库搜索路径；独立模块的 `code/issue` 输出没有通过这两个入口接入。

渠道容器另有 `platform/keyword/timestamp/status:string`、`success:boolean`、`error:string|null`、`timing_ms:integer`、`items:array<object>`、`total:integer`。成功执行有 `has_results:boolean`；空结果增加 `warning`；失败可增加 `error_details`，并且可能没有 `has_results`。

联合结果另外包含 `summary`、`channels`、`timing`、`download_candidates` 和 `adapter_timing_ms`；下载候选视图不替代完整条目。顶层信封含 `schema_version/ok/type/success/command/query/timestamp/duration_ms/errors/meta/data`，失败增加 `error`。统一 CLI 的搜索 JSON、text 和 Markdown 都保留信封及全部字段，Markdown 用 JSON 代码块承载。该保留行为与独立 GitHub 模块的有限字段展示不同。

## 额度状态输出

`get_rate_limit` 返回 `search/core` 两个对象，每个包含 `limit/remaining/used`（预期 `integer`）和 `reset`（Python `datetime`，从远端 Unix 秒数转换）。独立 `rate-limit` 命令将它们格式化为文本，`reset` 显示为本地时间字符串；没有返回搜索 `items`，也没有接入统一搜索条目。本次未执行额度查询。
