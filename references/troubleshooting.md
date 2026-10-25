# 常见问题排查指南

任务选择见[根技能任务入口](../SKILL.md#任务入口)。以下命令从技能根目录执行。先检查实际命令帮助与返回的 `ok`、`error`，再按凭据、网络、参数和平台状态定位问题。

## 凭据相关问题

### 缺少 API 凭据

通过能力清单确认渠道需要的变量，通过环境检查确认本地配置状态：

```bash
python scripts/union_search_cli.py list --pretty
python scripts/union_search_cli.py doctor --help
python scripts/union_search_cli.py doctor --platforms github wikipedia
```

环境检查通过只说明本地条件满足，不证明远程请求可用。需要配置凭据时，使用项目根目录的 `.env.example` 作为变量模板，在本地编辑器中填写对应服务生成的有效凭据。保留已有 `.env`，不要用模板覆盖它，不要把凭据打印到终端或写入结果文件。

- Google 需要 `GOOGLE_API_KEY` 和 `GOOGLE_SEARCH_ENGINE_ID`。
- AnySearch 必须配置有效的 `ANYSEARCH_API_KEY`。
- 知乎开放平台使用 `ZHIHU_ACCESS_SECRET`。
- `bing` 和 `yandex` 的 SerpAPI 渠道需要 `SERPAPI_API_KEY`，网页直连渠道的要求见能力清单。
- `no_api_key` 只表示不要求 API Key。本机账号搜索仍需要工具登录、OAuth 凭据与账号额度，见[本机工具说明](../scripts/channels/ai_tools/README.md)。

获取方式见[凭据指南](api_credentials.md)。

### 凭据无效或过期

收到 401、`Invalid credentials` 或 `Token expired` 时，在对应控制台检查凭据是否过期、撤销或属于其他项目，同时确认服务开通状态与权限。GitHub Token 的权限须覆盖请求资源；知乎开放平台检查 `ZHIHU_ACCESS_SECRET`。本机账号渠道按对应工具的登录流程更新认证。

## 网络相关问题

### 网络超时

检查网络、DNS、代理和防火墙。超时参数以当前入口的 `--help` 为准；Reddit 独立入口支持 `--timeout` 与 `--proxy`：

```bash
python scripts/channels/reddit/cli.py search --help
python scripts/channels/reddit/cli.py search "python tutorial" --limit 5 --timeout 30 --proxy http://127.0.0.1:7890
```

通用 `HTTP_PROXY`、`HTTPS_PROXY` 与渠道专用代理变量的支持情况取决于对应实现。代理必须实际可用，并允许访问目标站点。

### 403 Forbidden

403 可能来自权限不足、IP 访问限制或验证码。检查响应内容与渠道要求，不根据状态码直接推断原因。

- Reddit 的公开 JSON 入口可能受到访问限制。降低频率并检查代理与目标站点访问状态，代理不能保证请求成功。
- 网页直连搜索遇到验证码时，检查渠道错误并停止密集请求。
- API 渠道检查凭据权限、服务开通状态和账号额度。

### SSL 证书错误

检查系统时间、证书信任链及代理证书配置。Python HTTP 客户端使用的证书依赖可通过以下命令更新：

```bash
python -m pip install --upgrade certifi
```

企业代理需要配置受信任的 CA 证书。保持 TLS 证书验证开启。

## API 限制问题

429 或 `Rate limit exceeded` 表示需要降低请求频率；检查 `Retry-After`、配额重置时间与服务控制台。额度用尽时等待重置或调整账号套餐。平台可能同时限制请求次数、并发数和搜索结果数量。

```bash
python scripts/channels/github_search/github_search.py rate-limit
```

YouTube 搜索请求消耗 100 单位，减少结果数量不会降低该次搜索本身的消耗；详情和评论按实际请求次数累计。Google 和 Tavily 的额度由账号套餐决定。其他服务与图片平台的限制见[限流说明](rate_limits.md)。

## 参数错误问题

使用当前入口及子命令的帮助确认参数，统一 CLI 和平台独立脚本的参数名称可能不同：

```bash
python scripts/union_search_cli.py --help
python scripts/union_search_cli.py image --help
python scripts/channels/github_search/github_search.py --help
python scripts/channels/reddit/cli.py --help
python scripts/channels/reddit/cli.py search --help
python scripts/channels/reddit/cli.py subreddit-search --help
python scripts/channels/reddit/cli.py post --help
```

- GitHub 星标条件使用 `--stars ">1000"`，包含 shell 特殊字符的值需要引号。
- Reddit 输出格式使用 `--format json` 或 `--format csv`；CSV 需要 `--output`。
- Reddit `post` 接收 `/r/.../comments/.../` 形式的 permalink，详情包含该入口返回的评论数据。
- 统一图片入口使用 `--limit`、`--output-dir`；独立图片脚本使用 `--num`、`--output`。

## 平台特定问题

### GitHub 搜索结果为空

检查关键词、过滤条件、仓库是否存在及访问权限。代码搜索与私有资源可能有额外认证要求。参数见[GitHub 文档](../scripts/channels/github_search/README.md)。

### Reddit 搜索失败

独立入口为 `scripts/channels/reddit/cli.py`。遇到空结果时同时检查终端错误，不能仅凭空列表认定没有相关内容。底层重试包含 429 和部分服务器错误，403 不在重试列表中。请求间隔建议至少 2–3 秒。命令说明见[平台说明](platform_notes.md#reddit)和[Reddit 文档](../scripts/channels/reddit/README.md)。

### 图片搜索或下载失败

图片能力支持 **24 个平台（12 个原生平台、12 个 SDK 平台）**。默认选择 `baidu bing wikicommons`；原生平台支持 `--search-only`，SDK 平台需要执行下载。凭据要求按平台确定，火山引擎需要 `VOLCENGINE_API_KEY`。

```bash
python scripts/union_search_cli.py list --type images --pretty
python scripts/union_search_cli.py image "cats" --platforms bing --search-only --limit 5 --pretty
python scripts/union_search_cli.py image "cats" --platforms bing --limit 5 --threads 3 --delay 2.0 --output-dir .work/images -o .work/images.json
```

检查 `ok`、各平台状态、单张图片的 `download_status` 和实际文件。搜索成功不保证图片地址能够下载。下载文件需通过 Pillow 校验；失败记录会保留图片来源与错误。

`--threads` 默认 5，控制下载线程数；`--delay` 默认 1.0 秒，控制平台之间的延迟，不控制每次 HTTP 请求的间隔。明确指定的平台失败会报告错误，不自动切换来源。更多参数见[图片说明](../scripts/union_image_search/README.md)。

## 结果与诊断信息

统一 CLI 默认输出 JSON 信封，先检查 `ok`。部分失败时也可能保留成功结果的 `data`；退出码为零不保证所有渠道成功。搜索可用 `--fail-on-platform-error`，图片需检查结果状态。输出契约见[CLI 文档](../scripts/cli/README.md)。

使用 `-o` 保存统一 CLI 结果到当前任务的 `.work/` 目录。独立脚本是否支持 `--save-raw`、输出位置和日志行为以对应帮助及 README 为准。Reddit 模块的 `YARS.log` 相对于执行时的工作目录生成。分享诊断信息前移除密钥、Token、Cookie 和其他认证内容。

## 常见错误速查

| 错误 | 检查内容 |
|------|----------|
| Missing API credentials | 渠道要求的变量与本地配置 |
| 401 Unauthorized | 凭据有效期、项目与权限 |
| 403 Forbidden | 响应内容、权限、验证码与访问限制 |
| 429 Too Many Requests | 请求频率、并发与配额重置时间 |
| Connection timeout | 网络、代理与入口的超时参数 |
| SSL certificate error | 时间、CA 证书与代理信任链 |
| Invalid argument | 当前入口与子命令的 `--help` |
| Quota exceeded | 服务控制台与套餐额度 |

相关资料：[凭据指南](api_credentials.md)、[限流说明](rate_limits.md)、[平台说明](platform_notes.md)、[Google 搜索技巧](google_search_guide.md)。
