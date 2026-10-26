# 第三方项目与依赖说明

本项目现阶段暂定采用 [MIT 协议](../LICENSE)。该协议适用于本仓库原创代码与文档，第三方组件保留各自的版权与许可声明。

本清单按仓库中的依赖声明、模块文档及本地包元数据整理。它列出直接依赖和主要集成来源，不是完整的传递依赖清单或许可证审计报告。具体安装版本应结合锁文件、安装环境和对应发行包确认；第三方许可文本以所用版本附带的文件为准。

## Python 直接依赖

声明文件为 [requirements.txt](../requirements.txt)。下表中的包均在该文件中列出；功能是否实际使用该包，以对应模块代码为准。

| 安装包 / 上游项目 | 在本项目中的用途 |
| --- | --- |
| [requests](https://github.com/psf/requests) | 调用搜索 API、获取网页与下载内容 |
| [python-dotenv](https://github.com/theskumar/python-dotenv) | 加载本地 `.env` 配置 |
| [lxml](https://github.com/lxml/lxml) | HTML / XML 解析与页面内容提取 |
| [curl_cffi](https://github.com/lexiforest/curl_cffi) | 网页搜索的 HTTP 会话与浏览器请求兼容；声明范围 `>=0.16.0,<0.17` |
| [pyimagedl / imagedl](https://github.com/CharlesPikachu/imagedl) | 保留的 SDK 图片平台搜索与下载；原生图片平台独立实现 |
| [Pillow](https://github.com/python-pillow/Pillow) | 实际下载图片的 `Image.verify()` 校验与图片信息读取，声明要求 `>=12` |
| [chompjs](https://github.com/Nykakin/chompjs) | 解析图片平台页面中的 JavaScript 数据，声明要求 `>=1.2` |
| [yt-dlp](https://github.com/yt-dlp/yt-dlp) | 媒体下载及站点适配 |
| [tavily-python](https://github.com/tavily-ai/tavily-python) | Tavily Python SDK |
| [loguru](https://github.com/Delgan/loguru) | 日志输出 |
| [pydantic](https://github.com/pydantic/pydantic) | 结构化模型与数据校验，声明要求为 `>=2.0.0` |
| [firecrawl-py](https://pypi.org/project/firecrawl-py/) | Firecrawl Python SDK；部分入口也直接请求 HTTP API |

## Node.js 直接依赖

根目录声明文件为 [package.json](../package.json)，版本解析记录见 [package-lock.json](../package-lock.json)。

| 上游项目 | 声明范围 | 用途 |
| --- | --- | --- |
| [Cheerio](https://github.com/cheeriojs/cheerio) | `^1.2.0` | 服务端 HTML 解析与选择器处理 |
| [Commander.js](https://github.com/tj/commander.js) | `^12.1.0` | Node.js 命令行参数处理 |
| [jsdom](https://github.com/jsdom/jsdom) | `^24.0.0` | DOM 环境与网页内容处理 |

## 内置与可选组件

| 项目 | 集成方式与用途 | 来源和许可说明 |
| --- | --- | --- |
| [Defuddle](https://github.com/kepano/defuddle) | 在 `scripts/url_to_markdown/engines/defuddle-node/` 通过 `npm ci` 安装正式 npm 包，固定版本 `0.10.0` | 作者 `kepano`、许可证 `MIT`；安装包保留第三方版权和许可声明 |
| [Commander.js](https://github.com/tj/commander.js) | Defuddle 的传递依赖 | 与根目录依赖分别安装，版本以各自锁文件为准 |
| [jsdom](https://github.com/jsdom/jsdom) | Defuddle 安装目录显式固定版本 `24.1.3` | 提供正文提取所需 DOM 环境 |
| [mathml-to-latex](https://www.npmjs.com/package/mathml-to-latex) | Defuddle 子包的可选依赖 `^1.5.0` | 处理数学公式转换，是否安装取决于环境 |
| [Temml](https://www.npmjs.com/package/temml) | Defuddle 子包的可选依赖 `^0.13.1` | 数学公式处理，是否安装取决于环境 |
| [Turndown](https://www.npmjs.com/package/turndown) | Defuddle 子包的可选依赖 `^7.2.0` | HTML 转 Markdown，是否安装取决于环境 |
| [FFmpeg](https://ffmpeg.org/) | 由用户按需在系统安装，配合 yt-dlp 使用 | 用于音视频合并和音频提取，不由根目录 pip / npm 声明安装；具体构建的许可与启用组件有关 |

Defuddle 子包的声明见 [package.json](../scripts/url_to_markdown/engines/defuddle-node/package.json)。Python、Node.js 与 npm 是运行和安装工具，不属于本仓库原创代码。

## AI 工具搜索实现的来源

[AI 工具模块说明](../scripts/channels/ai_tools/README.md)记录，`scripts/channels/ai_tools/native_search/` 的实现以本地 `agent-search-extraction` 项目已有代码为基础迁入，并调整包路径、统一入口适配与执行控制。当前运行不依赖原项目目录。

该来源尚未在本仓库文档中提供可核验的公开仓库地址与独立许可证记录，因此此处仅记录实际来源，不推定原项目的授权。维护时应补齐原作者、来源版本及适用许可信息；本次新增项目 MIT 文件不代替对迁入代码权属的核对。

三个渠道依赖用户安装或登录的 Claude Code、Codex、Grok Build。它们是外部客户端或账号服务，本项目的 MIT 协议不改变其使用条款。具体接入方式、账号要求与端点边界见模块说明。

## 原生图片平台实现

`scripts/union_image_search/` 内的原生图片平台由本项目独立实现，通过各平台的网页或公开接口解析图片地址、来源页面和元数据，运行时不依赖外部图片协议项目。保留的 SDK 图片平台继续使用 `pyimagedl`，通过 `--platforms` 显式选择。默认图片平台为 `baidu bing wikicommons`，不因平台失败自动切换实现或来源。

Pillow 用于校验实际图片内容；SHA-256 摘要由 Python 标准库计算。解析得到的图片地址、作者和许可信息仍受来源平台与内容权利人的要求约束，获取到图片不代表取得再分发或商用授权。

## 外部 API 与平台服务

项目适配 Google、YouTube、Tavily、Exa、Firecrawl、SerpAPI、Serper、Jina、秘塔、百度千帆、火山引擎、阿里云百炼、腾讯云联网搜索、智谱、Moonshot、DeepSeek 兼容服务、TinyFish、Parallel、Querit、Ollama、知乎开放平台、Cloudflare、GitHub、AnySearch 等服务。

这些名称表示接口适配或服务接入，不表示相应服务是本项目的开源依赖，也不表示官方合作或背书。具体可用渠道通过 `python union_search_cli.py list --pretty` 查看。接口资格、计费、额度、账号和平台内容的使用要求仍由对应服务决定。

API Key 获取与配置见 [凭据指南](api_credentials.md) 和 [Agent 自动配置指南](agent_api_key_setup.md)。Computer Use 使用当前 Agent 自带的工具，本仓库不附带通用桌面控制引擎，也不提供共享账号或密钥。

## README 与文档参考

| 参考项目 | 参考范围 |
| --- | --- |
| [standard-readme](https://github.com/RichardLitt/standard-readme) | README 信息组织与基础章节 |
| [Best-README-Template](https://github.com/othneildrew/Best-README-Template) | 项目介绍、安装和参与维护等内容组织 |
| [beautify-github-readme](https://github.com/oil-oil/beautify-github-readme) | README 视觉呈现与阅读导航 |

这些项目是文档参考，不属于运行时依赖。README 的具体内容和流程示意图按本仓库功能整理。

## 更新清单

增加依赖、迁入代码或升级内置组件时，同步维护本清单和相关依赖声明，保留原有版权、许可证与 NOTICE 文件。新增第三方组件仍按其自身许可处理，不能统一改写为 MIT。
