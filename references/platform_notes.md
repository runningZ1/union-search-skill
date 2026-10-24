# 平台特定说明

任务选择见[根技能任务入口](../SKILL.md#任务入口)，通用参数见[CLI 文档](../scripts/cli/README.md)。渠道与分组通过 `python union_search_cli.py list --pretty` 查看。

## YouTube

YouTube Data API 默认每日配额为 10,000 单位，每天太平洋时间午夜重置。搜索请求消耗 100 单位；`videos.list` 和 `commentThreads.list` 通常各消耗 1 单位。配额按实际请求次数计算，批量获取视频详情时不能按视频数量直接计算请求次数。

```bash
python scripts/channels/youtube/youtube_search.py --help
python union_search_cli.py platform youtube "Python tutorial" --limit 5 --pretty
```

限制结果数量可以减少后续详情和评论请求，但搜索请求本身仍消耗配额。需要评论时先查看独立脚本帮助。保存结果后复用已有数据，避免重复查询。凭据为 `YOUTUBE_API_KEY`，更多说明见[YouTube 文档](../scripts/channels/youtube/README.md)。

## GitHub

| 认证状态 | 搜索限制 | 核心 API 限制 |
|---------|---------|--------------|
| 已认证 | 通常 30 次/分钟 | 通常 5,000 次/小时 |
| 未认证 | 通常 10 次/分钟 | 通常 60 次/小时 |

不同接口和账号可能有额外限制，以响应头和账号额度为准。`GITHUB_TOKEN` 是可选配置，私有资源需要相应访问权限。

```bash
python scripts/channels/github_search/github_search.py rate-limit
python scripts/channels/github_search/github_search.py repo "machine learning" --language python
python scripts/channels/github_search/github_search.py repo "web framework" --stars ">1000"
python scripts/channels/github_search/github_search.py code "async def" --language python
python scripts/channels/github_search/github_search.py issue "bug" --state open
```

参数与认证方式见[GitHub 文档](../scripts/channels/github_search/README.md)。

## Reddit

Reddit 使用无需 API Key 的公开 JSON 入口，可能受到 403、429 或其他访问限制。独立命令入口为 `scripts/channels/reddit/cli.py`。

```bash
python scripts/channels/reddit/cli.py --help
python scripts/channels/reddit/cli.py search --help
python scripts/channels/reddit/cli.py post --help
python scripts/channels/reddit/cli.py search "python tutorial" --limit 10 --format json
python scripts/channels/reddit/cli.py subreddit-search python "async await" --limit 10
python scripts/channels/reddit/cli.py post "<帖子 permalink>" --format json
python scripts/channels/reddit/cli.py search "test" --limit 5 --proxy http://127.0.0.1:7890
```

`post` 接收 `/r/.../comments/.../` 形式的 permalink。帖子详情包含该入口返回的评论数据。公共选项包含 `--proxy`、`--timeout`、`--output` 和 `--format`；`--format` 可选 `json`、`csv`、`display`，CSV 输出需要 `--output`。

底层对 429 和部分服务器错误配置重试；403 不在该重试列表中。建议请求间隔至少 2–3 秒，收到限制响应时检查访问条件并停止密集请求。代理不能保证请求成功。空结果需要结合终端错误判断。更多说明见[Reddit 文档](../scripts/channels/reddit/README.md)。

## 图片搜索

支持 **24 个图片平台：12 个原生平台、12 个 SDK 平台**。

| 实现 | 平台 |
|------|------|
| 原生 | `baidu`、`bing`、`sogou`、`quark`、`pixabay`、`flickr`、`pinterest`、`500px`、`wikicommons`、`naver`、`artstation`、`findthatmeme` |
| SDK | `google`、`i360`、`yandex`、`yahoo`、`unsplash`、`gelbooru`、`safebooru`、`danbooru`、`pexels`、`huaban`、`foodiesfeed`、`volcengine` |

默认平台为 `baidu bing wikicommons`。原生平台支持 `--search-only`，只返回图片地址与元数据；SDK 平台需要执行下载。凭据要求取决于平台，火山引擎需要 `VOLCENGINE_API_KEY`。无需 API Key 不代表全部平台无需凭据、免费或没有访问限制。

```bash
python union_search_cli.py list --type images --pretty
python union_search_cli.py image --help
python union_search_cli.py image "sunset" --platforms baidu bing wikicommons --search-only --limit 5 --pretty
python union_search_cli.py image "flowers" --platforms bing --limit 5 --threads 3 --delay 2.0 --output-dir .work/images -o .work/images.json
```

`--threads` 控制下载线程数，默认 5；`--delay` 为平台之间的延迟，默认 1.0 秒，不控制全部 HTTP 请求的间隔。统一 CLI 使用 `--limit` 和 `--output-dir`；独立脚本使用 `--num` 和 `--output`。平台失败会明确报告，不自动切换来源。

下载结果需检查 `ok`、平台状态、单张图片的 `download_status` 和实际文件。下载文件经过 Pillow 校验，并记录文件大小与 SHA-256。作者和许可信息缺失时不能推断图片可自由使用。完整参数与结果结构见[图片说明](../scripts/union_image_search/README.md)。

## 知乎开放平台（Zhihu）

`zhihu_official` 渠道需要 `ZHIHU_ACCESS_SECRET`。支持站内搜索、全网搜索、热榜与直答，数量限制和参数见[知乎开放平台文档](../scripts/channels/zhihu_official/README.md)。

## 秘塔搜索（Metaso）

秘塔搜索需要 `METASO_API_KEY`，搜索会消耗账号积分。返回摘要用于定位资料，核实细节时读取来源正文。零条结果需检查请求状态、关键词、过滤条件和额度；`--preset large` 只设置结果数量，不保证返回内容。参数见[秘塔文档](../scripts/channels/metaso/README.md)。

## 凭据与错误检查

`no_api_key` 按认证条件分组。本机账号搜索仍需要对应工具登录、OAuth 凭据及账号额度，见[本机工具说明](../scripts/channels/ai_tools/README.md)。AnySearch 必须配置有效的 `ANYSEARCH_API_KEY`。

- [凭据指南](api_credentials.md)：服务密钥、可选 Token 与本机账号要求。
- [限流说明](rate_limits.md)：请求频率、配额与图片并发参数。
- [排查指南](troubleshooting.md)：凭据、网络、参数和结果检查。
