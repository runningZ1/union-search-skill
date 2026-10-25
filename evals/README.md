# 技能评估与验证

## 评估范围

本目录评估根技能 `union-search-skill` 的任务边界。`trigger_cases.json` 包含 13 条应触发、3 条不应触发和 5 条相邻任务用例，覆盖搜索、搜索历史、正文、图片、媒体、本地资料和代码任务。

这些用例是用于检查说明边界的请求文本，不包含伪造的渠道响应。`semantic_config.json` 为 Yao 的启发式评估器提供中英文关键词和排除条件。评估器没有调用模型，结果不能证明客户端的实际激活率，也不能证明未覆盖任务的执行质量。

## 运行方法

将 `<YAO_ROOT>` 替换为实际的 Yao Meta Skill 目录，在当前技能根目录执行：

```bash
python <YAO_ROOT>/scripts/yao.py validate .
python <YAO_ROOT>/scripts/trigger_eval.py --description-file SKILL.md --cases evals/trigger_cases.json --semantic-config evals/semantic_config.json
```

Yao 2.1.0 的统一 CLI 使用 `fcntl`，Windows Python 无法导入该模块。Windows 上通过 WSL 的 Linux Python 执行 `yao.py`，并使用 `/mnt/c/...` 形式的绝对目标路径；Git Bash 调用 WSL 时设置 `MSYS_NO_PATHCONV=1`。`trigger_eval.py` 可直接使用 Windows Python。

修改描述后同时检查应触发和排除用例。修改命令说明后运行对应的真实 `--help`，对涉及的执行路径进行实际调用。不要为提高评估分数调整错误的排除条件。

## 已完成的真实验证

2026-10-22 在当前 Windows 环境完成以下调用，输出保存在已忽略的 `.work/skill-design/`：

| 路径 | 实际结果 |
|------|----------|
| `list` / `schema` | 成功生成真实能力信息 |
| `doctor --platforms github wikipedia` | 12 项环境检查通过，两个渠道本地状态就绪 |
| GitHub 单渠道搜索 | 返回两条真实结果，`ok=true` |
| GitHub 与 Wikipedia 联合搜索 | 两个渠道分别返回两条结果，`ok=true` |
| Defuddle 提取 `https://example.com` | 返回 `Example Domain` 标题及正文，`ok=true` |
| Bing 图片搜索与下载 | 实际保存一张 JPEG，3,512,465 字节，`ok=true` |
| yt-dlp 下载公开示例 MP4 | 实际保存媒体文件，788,493 字节，`ok=true` |
| Yao `validate` | 结构、lint、治理检查和资源边界检查均返回成功 |
| Yao 启发式触发评估 | 19 条通过，误触发和漏触发均为零 |
| 文档链接及差异格式 | 根技能、执行指南与评估说明的本地链接有效，`git diff --check` 通过 |

正文提取的 JSON 调用成功；随后两次 `defuddle https://example.com --format markdown` 调用遇到 TLS 连接中断，返回退出码 `4` 和 `PLATFORM_FAILURE`，写出的 Markdown 是错误报告。Markdown 参数已经通过真实帮助和输出渲染代码核对，本次没有取得该格式的成功远程结果。

该记录只证明所列路径在执行时的结果。其他付费渠道、本机账号渠道、全部图片平台、音频转换及全部平台专用参数没有在本次验证中逐一调用。已有测试中使用 mock 的用例未执行。

## 检查提示

Yao 报告当前没有 `manifest.json`，治理元数据不可用。项目没有在本次维护中声明发布等级、维护周期或审核人。

资源检查的递归扫描将本地依赖计入 `scripts/`，报告约 475 万估算 token 的延迟资源。本次结构检查时根技能的估算初始加载量约为 750 token，正文约为 620 token；具体数值以重新执行检查的结果为准。根技能只要求按任务读取所需文档，日常使用无需加载全部脚本和本地依赖。

发布制品、安装兼容性、全部渠道可用性与模型实际路由需要各自的执行证据，不能由上述结构检查或关键词评估代替。
