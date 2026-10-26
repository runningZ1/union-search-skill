# 项目规则

## 项目职责

`union-search-skill` 提供一个根技能，通过 `union_search_cli.py` 统一调用搜索渠道、正文提取、图片下载和 yt-dlp 媒体下载。渠道目录是执行模块。`SKILL.md` 负责触发、任务选择和结果契约，详细步骤放入 `references/` 和对应模块 README。

## 开发入口

- Python 依赖：`python -m pip install -r requirements.txt`。
- Node.js 依赖：`npm ci`；Defuddle 的准备步骤见 `scripts/url_to_markdown/README.md`。
- 能力清单：`python union_search_cli.py list --pretty`。
- 参数与结构：`python union_search_cli.py schema --pretty` 和子命令 `--help`。
- 环境检查：`python union_search_cli.py doctor --platforms <渠道>`。

## 文件职责

- `scripts/cli/`：参数、能力注册、输出信封、适配器和错误码。
- `scripts/union_search/`：并发搜索、分组和凭据元数据。
- `scripts/channels/`：每个服务一个目录，API 与无需 API Key 的版本共用服务目录。
- `scripts/url_to_markdown/`、`scripts/union_image_search/`、`scripts/downloader/`：正文、图片与媒体能力。
- `references/`：按任务阅读的操作说明，第三方说明位于 `references/third_party.md`。
- `scripts/evals/`：技能路由评估和验证说明。
- `scripts/tests/`：已有回归用例；执行前确认符合当前测试约束。

## 实现约束

遵循所在模块的命名与结构。需要的依赖直接导入，不为缺失依赖编写替代实现。错误在发生位置明确失败，不增加隐藏异常或替代执行路径。不用程序批量改写代码，使用文件编辑工具修改。

能力名称、数量、默认参数和输出行为以真实 CLI 与注册表为准。修改渠道或分组时，同时检查根技能、中文与英文 README、CLI README 和编排 README。修改图片、正文或媒体接口时，同时更新任务导航与对应模块文档。

保留现有 `.env`，不要在命令、日志、评估或报告中输出凭据。任务中间结果放入已忽略的 `.work/`。不要读写 `/tmp`。不要覆盖用户的未跟踪文件，不执行 Git 回滚，不擅自提交或推送。

## 验证要求

每次功能变更运行真实入口并检查结果；文档命令通过 `--help`、`list` 或实际调用验证。禁止使用 mock、伪造响应或仅为通过测试的特殊处理。现有使用 mock 的测试不能作为本任务的验证证据。

搜索验证应检查实际来源与 `ok`，正文验证应检查实际提取内容，下载验证应检查真实文件。`doctor` 通过仅说明本地环境检查通过。需要外部凭据、网络或额度的能力，应如实记录已验证范围与未验证范围。

技能修改时运行 Yao Meta Skill 的结构、资源边界与触发检查，步骤见 `scripts/evals/README.md`。启发式触发评估不能证明模型的实际激活率。不要为了消除评分警告添加未经证实的维护信息或发布证据。

## 协作规则

全部项目规则维护在本文件。根目录 `CLAUDE.md` 仅包含 `@AGENTS.md`。修改前读取目标，发现用户已更改内容时按当前状态继续。
