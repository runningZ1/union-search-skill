# 搜索预览与完整内容读取验证 — 2026-11-05

历史记录：本文中的 400 字符预览已按用户要求移除。当前默认完整显示摘要，只保留 `--content full|none`；按需读取继续使用 `read`。下文保留当时的验证事实，不代表当前参数。当前验证见 [摘要显示与隐藏验证](content-toggle-20261105.md)。

默认搜索保持不限条数；统一 CLI 默认使用 `--view compact --content preview --content-max-chars 400`。精简视图保留全部去重条目和渠道状态，省去逐渠道条目与下载候选的重复展示。完整规范化信封独立存入 `.work/search-results/<unique-id>/full.json`，通过 `meta.full_result_file` 定位；不是原始 HTTP 响应。`-o` 保存所选视图。

## 真实入口验证

在项目根目录执行，使用现有 `.env`，不打印密钥；没有 mock 或伪造服务响应。

```powershell
python union_search_cli.py search "服装设计 再生面料 廓形 工艺" --group api -o .work/cli-preview-upgrade/search.json
python union_search_cli.py platform tavily "服装设计 再生面料" --content none -o .work/cli-preview-upgrade/none.json
python union_search_cli.py keenable "服装设计 面料 廓形" --limit 0 --view full --content full -o .work/cli-preview-upgrade/full.json
python union_search_cli.py read --from-file .work/cli-preview-upgrade/search.json --ids 1 2 -o .work/cli-preview-upgrade/read.json
```

- 联合搜索 `ok=true`，23/23 API 渠道成功，原始 225 条，URL 去重后 175 条，`limit_per_platform=null`。CLI 没有施加每渠道条数截断；上游容量仍有效，没有自动无限分页。
- 默认文件 184,133 字节，完整归档 915,095 字节；相同查询输出字节量降低约 79.9%。未使用 tokenizer 测量，不能视为精确 Token 节省量。
- 对照归档逐条验证 175 个 ID、URL 和来源一致；所有预览等于完整文本前 400 字符，原长度与截断标记正确。完整归档保留 23 个逐渠道对象。
- 本地 `read` 返回前两条完整内容，并按最长条目的 ID 恢复 23,384 字符，逐字匹配归档；未知 ID 返回 `INVALID_ARGUMENT`、退出 2，没有网络调用。
- Tavily 隐藏内容模式成功返回 10 条，展示条目均无 `content`，归档仍保留完整内容。Keenable 直接渠道命令成功返回 50 条，`--limit 0`、完整布局与完整文本正常。
- 负数 `--content-max-chars` 在渠道调用之前返回 `INVALID_ARGUMENT`、退出 2。
- `search --help`、`platform --help`、`read --help` 和 `schema` 检查成功。Python 编译检查与 `git diff --check` 通过。

本地断言脚本与运行结果保存在已忽略的 `.work/cli-preview-upgrade/`。结果量和可用性只代表本次实时调用，不证明长期稳定性。原网页正文真实性未逐篇核查。

## 技能检查

Yao `validate` 的结构、lint、治理和资源边界检查均 `ok=true`。保留缺少 manifest 元数据、延迟资源体积较大的既有警告；没有补造维护或发布证据。启发式触发检查 19/19，通过不代表模型实际激活率。
