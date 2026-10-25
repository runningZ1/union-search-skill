# Union Image Search - 多平台图片搜索

支持 24 个图片平台，提供图片搜索、来源与元数据解析，以及下载和文件校验。12 个原生平台由本项目独立实现；保留 12 个 SDK 平台，可通过 `--platforms` 显式指定。

## 安装

从仓库根目录执行：

```bash
python -m pip install -r requirements.txt
```

原生实现使用 HTTP 与页面解析依赖；`chompjs>=1.2` 解析页面中的 JavaScript 数据，`Pillow>=12` 校验图片文件。SDK 平台使用 `pyimagedl`。部分平台需要各自的 API Key，火山引擎使用 `VOLCENGINE_API_KEY`。

## 支持的平台

原生平台：`baidu`、`bing`、`sogou`、`quark`、`pixabay`、`flickr`、`pinterest`、`500px`、`wikicommons`、`naver`、`artstation`、`findthatmeme`。

保留的 SDK 平台：`google`、`i360`、`yandex`、`yahoo`、`unsplash`、`gelbooru`、`safebooru`、`danbooru`、`pexels`、`huaban`、`foodiesfeed`、`volcengine`。

`baidu`、`bing`、`sogou`、`pixabay` 使用本项目实现，分别解析图片地址、来源页面与元数据。默认平台为 `baidu bing wikicommons`。平台失败时直接报告错误，不自动切换到 SDK 或其他来源。实际可选平台通过 `list --type images` 查看。

## 统一 CLI

以下命令均从仓库根目录执行：

```bash
python scripts/union_search_cli.py image "sunset" --limit 5 --pretty
python scripts/union_search_cli.py image "mountain landscape" --platforms baidu bing wikicommons --search-only --limit 5 --pretty
python scripts/union_search_cli.py image "flowers" --platforms bing --output-dir ./my_images --limit 5 -o ./out/images.json --pretty
python scripts/union_search_cli.py image "sunset" --platforms google --limit 5 --pretty
python scripts/union_search_cli.py list --type images --pretty
python scripts/union_search_cli.py image --help
```

关键词使用位置参数或 `--query`，显式 `--query` 优先。每平台数量使用 `--limit/-l`，默认 `0` 表示保留本次取得的全部结果，负数返回参数错误。原生搜索只获取本次单页的有限结果，不自动遍历全部分页。

默认搜索后下载图片；`--search-only` 只返回图片结果与元数据，不下载文件，仅支持原生平台。显式选择不支持纯搜索的 SDK 平台时返回错误。

`--output-dir` 设置图片目录，默认 `image_downloads`；`-o/--output` 保存 CLI 结果信封，与图片目录独立。默认输出 JSON，`--pretty` 添加缩进。`--threads` 默认 `5`，`--delay` 默认 `1.0` 秒，`--timeout` 默认 `1800` 秒，`--env-file` 默认 `.env`。`--no-metadata` 关闭平台目录中的元数据文件。统一 CLI 没有 `--keyword`、`--num` 或 `--json` 参数。

## 独立脚本

```bash
python scripts/union_image_search/multi_platform_image_search.py "cute cats"
python scripts/union_image_search/multi_platform_image_search.py --keyword "sunset" --platforms baidu bing --search-only --num 5
python scripts/union_image_search/multi_platform_image_search.py --keyword "风景" --platforms volcengine --num 5
python scripts/union_image_search/multi_platform_image_search.py --keyword "flowers" --output ./my_images --num 5
python scripts/union_image_search/multi_platform_image_search.py --help
python scripts/union_image_search/multi_platform_image_search.py --list-platforms
```

| 参数 | 行为 |
| --- | --- |
| 位置参数 `keyword`、`--keyword` | 关键词；显式 `--keyword` 优先，也可读取 `IMAGE_SEARCH_KEYWORD` |
| `--platforms` | 平台列表；默认 `baidu bing wikicommons` |
| `--search-only` | 仅搜索原生平台，不下载；不支持的平台明确报错 |
| `--num` | 每平台数量；默认 `0`，小于或等于 `0` 不做本地截断，正整数设置上限 |
| `--output` | 图片输出目录，默认 `image_downloads` |
| `--threads` | 下载线程数，默认 `5` |
| `--no-metadata` | 不保存平台目录中的 `metadata.json`，仍保存汇总报告 |
| `--delay` | 平台间延迟秒数，默认 `1.0` |
| `--env-file` | 环境变量文件，默认 `.env` |
| `--pretty` | 为末尾 JSON 添加缩进，进度文本仍会输出 |
| `--list-platforms` | 列出支持的平台后退出，无需关键词 |

独立脚本未注册 `-k`、`-p`、`-n`、`-o`、`-t` 短参数。未显式传入相关长参数时，可读取 `IMAGE_SEARCH_PLATFORMS`（逗号分隔）、`IMAGE_SEARCH_NUM`、`IMAGE_SEARCH_OUTPUT`、`IMAGE_SEARCH_THREADS` 和 `IMAGE_SEARCH_DELAY`。环境变量文件只补充当前进程中不存在的变量。

两个入口均受上游请求容量限制。SDK 平台不限条数时请求数量为 `10000`，火山引擎每次最多 `5` 张；这些参数不保证获得相应数量，也不自动穷尽分页。

## 图片字段与文件校验

每张图片的 `metadata` 为字典，统一保留以下字段；来源未提供的字段为 Python `None`，JSON 输出为 `null`：

| 字段 | 含义 |
| --- | --- |
| `title` | 图片标题 |
| `image_url` | 用于下载的图片地址 |
| `source_url` | 图片所属的来源页面 |
| `thumbnail` | 缩略图地址 |
| `width`、`height` | 图片尺寸 |
| `author`、`license` | 来源提供的作者与许可信息 |
| `image_variant` | 来源原始图片或最大可用版本的标记 |
| `provider`、`id` | 图片提供方与来源标识 |
| `file_path` | 实际下载文件位置；纯搜索时为空 |
| `download_status` | 单张图片的下载状态 |

`image_url` 与 `thumbnail` 独立保留。`image_variant` 说明实际取得的版本，不能把全部结果视为来源原文件。作者或许可为空时，不推断图片可自由使用。

下载后使用 Pillow 的 `Image.verify()` 检查实际图片内容，并记录文件 `sha256` 与 `bytes`。只有通过校验的实际文件才能作为成功下载返回。单张图片下载失败时保留该图片的来源、元数据、下载状态及错误，其他图片的结果继续保留。

## 输出位置

图片目录默认为当前工作目录下的 `image_downloads`，自定义相对路径也以当前工作目录为基准。下载结果保存在各平台的时间戳子目录；启用元数据保存时同时保存 `metadata.json`。`--search-only` 不生成图片文件。

两个入口的汇总报告保存在：

```text
scripts/union_image_search/responses/
└── YYYYMMDD_HHMMSS_image_search_results.json
```

报告路径通过 `saved_to` 返回，不受图片目录参数影响。当前脚本不生成 Markdown 汇总报告。

## 结果与错误规则

独立脚本输出进度文本及末尾 JSON，顶层包含 `saved_to`、`summary`、`platforms`、`items`。`items` 为各平台图片元数据合并后的字典列表。`summary` 包含 `keyword`、`total_platforms`、`successful`、`failed`、`total_found`、`total_images`、`search_only`；各平台记录包含 `success`、`found`、`downloaded`、`output_dir`，以及图片元数据和错误。`total_found` 记录找到的图片数量，`total_images` 记录下载数量；纯搜索的 `downloaded` 为 `0`，应结合 `total_found` 与状态判断搜索结果。

独立脚本完成汇总后退出 `0`，即使部分或全部平台失败；缺少关键词退出 `2`。程序化读取结果时检查 `summary.failed`、各平台状态与单张图片的 `download_status`。

统一 CLI 在全部平台及图片下载成功时返回 `ok: true`。平台或单张图片部分失败时，顶层 `ok` 为 `false`、`type` 为 `error`、错误码为 `PARTIAL_FAILURE`，信封保留 `data`，其中包括成功结果与单张图片的失败记录。收到失败汇总时 CLI 仍退出 `0`，没有 `--fail-on-platform-error` 选项。底层子进程非零退出或输出解析失败归为 `INTERNAL_ERROR`，退出 `1`；参数校验失败退出 `2`。

## 火山引擎

- 每次最多请求 `5` 张图片；不限条数时也请求 `5` 张。
- 适配器支持尺寸与形状过滤，两个图片 CLI 未暴露对应过滤参数。
- 在 `.env` 中设置 `VOLCENGINE_API_KEY`；获取方式见[凭据指南](../../references/api_credentials.md)。

统一 CLI 的机器信封、输出格式和退出码见[统一 CLI 文档](../cli/README.md)。
