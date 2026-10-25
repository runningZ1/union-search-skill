# 技能评估目录

`scripts/evals/` 存放根技能 `union-search-skill` 的任务触发案例、启发式触发评估配置及执行说明。本目录中的文件随项目提交。

## 文件范围

| 文件 | 内容 |
| --- | --- |
| `trigger_cases.json` | 应触发、不应触发和相邻任务的请求文本及预期分类，覆盖搜索、搜索历史、正文、图片、媒体、本地资料和代码任务 |
| `semantic_config.json` | Yao 启发式评估器使用的中英文关键词、权重与排除条件 |
| `README.md` | 本目录职责、评估命令、工具路径要求和结果解释 |

新增评估文件必须直接服务于技能任务选择、描述边界或资源组织的检查。代码行为回归测试保存在 [scripts/tests/](../tests/README.md)。评估输出、运行日志和临时文件保存在根目录 `.work/`；渠道真实响应样例保存在对应渠道的 `examples/`。不得在本目录存放凭据、下载文件、伪造的渠道响应或生产代码。

案例中的请求文本用于描述评估任务，不代表外部服务响应。启发式评估器没有调用模型，评估结果不能证明客户端的实际激活率或任务执行质量。

## 执行方法

将 `<YAO_ROOT>` 替换为实际的 Yao Meta Skill 目录。以下命令在技能根目录执行：

```bash
python <YAO_ROOT>/scripts/validate_skill.py .
python <YAO_ROOT>/scripts/lint_skill.py .
python <YAO_ROOT>/scripts/governance_check.py .
python <YAO_ROOT>/scripts/resource_boundary_check.py .
python <YAO_ROOT>/scripts/trigger_eval.py --description-file SKILL.md --cases scripts/evals/trigger_cases.json --semantic-config scripts/evals/semantic_config.json
```

上述四项结构检查对应 Yao `yao.py validate` 的检查步骤，可以直接使用 Windows Python 运行。Yao 2.1.0 的统一 CLI 依赖 `fcntl`；需要使用统一 CLI 时，通过 WSL Linux Python 执行，并传入 `/mnt/c/...` 形式的目标绝对路径。Git Bash 调用 WSL 时设置 `MSYS_NO_PATHCONV=1`。

评估目标始终是技能根目录。触发评估必须显式提供 `--cases` 和 `--semantic-config`，从其他工作目录执行时同时将目标与输入文件改为绝对路径。

## 工具路径要求

Yao 的 `export_skill_ir.py` 自动收集逻辑读取技能根目录下的 `evals/trigger_cases.json`，不会自动发现本目录。使用该自动导出功能前，需要确认导出工具支持 `scripts/evals/`，并检查导出结果实际包含本目录案例与配置。上述显式触发评估命令可以直接读取本目录。

`agents/_meta.json` 保存发布来源信息。使用要求根目录 `_meta.json` 的外部安装器或发布器时，需要由其打包配置提供对应路径映射；当前仓库没有验证这些外部工具的兼容性。

## 验证要求

修改技能描述后，同时检查应触发和排除用例。修改命令说明后执行对应真实入口；统一入口为 `python scripts/union_search_cli.py`。不要为提高评估分数修改任务真实边界或排除条件。

结构与资源检查通过只说明对应工具的检查条件得到满足。治理检查可能报告缺少 `manifest.json`；不得为消除警告填写未经证实的维护信息。资源检查可能把本地安装的依赖计入 `scripts/` 的估算资源量，结果需要结合实际按需读取方式解释。

发布制品、安装兼容性、远程渠道可用性和模型实际任务选择需要分别取得执行证据。
