# 摘要显示与隐藏验证 — 2026-11-05

按用户要求移除摘要截断：删除 `preview` 模式、`--content-max-chars` 和截断元数据。当前默认 `--view compact --content full`，完整显示渠道返回的规范化摘要，默认不限结果条数。`--content none` 显式隐藏摘要，完整归档保持可用；`read --from-file <搜索结果> --ids 1 2` 按需读取，不调用 API。

## 真实验证

```powershell
python union_search_cli.py search "服装设计 再生面料 廓形" --platforms tavily exa -o .work/content-toggle-upgrade/shown.json
python union_search_cli.py platform tavily "服装设计 再生面料" --content none -o .work/content-toggle-upgrade/hidden.json
python union_search_cli.py read --from-file .work/content-toggle-upgrade/hidden.json --ids 1 2 -o .work/content-toggle-upgrade/read.json
```

- 联合调用 2/2 成功、20 条结果，`limit_per_platform=null`。展示的每条摘要与完整归档逐字相等，最长 1,485 字符，未截断。
- 隐藏调用成功、10 条，所有展示条目均没有 `content`，完整归档仍有摘要。本地读取两条成功，内容与归档逐字一致。
- 以真实联合结果核对两种布局和两种摘要模式共四种组合：条目数量保持一致，隐藏时所有条目集合均无 `content`，完整显示时不修改摘要，不输出截断元数据。
- 已移除的 `--content preview` 和 `--content-max-chars 400` 均在参数解析阶段返回结构化错误、退出 2，无渠道调用。`search --help` 和 `schema` 已核对，默认内容模式为 `full`，仅列出 `full`、`none`。
- Python 编译检查和 `git diff --check` 通过。断言脚本和原始运行输出保存在已忽略的 `.work/content-toggle-upgrade/`。
- Yao 结构、lint、治理与资源边界检查通过，保留既有 manifest 缺失及延迟资源体积警告；启发式触发检查 19/19，不代表实际模型激活率。

本次未重复调用全部 23 家，展示变更使用真实 Tavily、Exa 数据验证；历史全渠道结果见前一验证记录。完整搜索摘要不承诺是网页全文。
