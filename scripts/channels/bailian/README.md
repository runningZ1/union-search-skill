# 阿里云百炼联网搜索

通过 DashScope 调用通义千问并开启联网搜索，返回模型回答与检索来源。

## 功能特性

- 强制联网搜索，返回来源列表与模型回答
- 四种检索策略：`turbo`、`max`、`agent`、`agent_max`
- 支持时间范围、限定站点、垂直领域搜索
- 来源包含站点名与图标

## 配置

在项目根目录的 `.env` 文件中添加：

```bash
DASHSCOPE_API_KEY=sk-your_dashscope_api_key
# 默认 https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation
DASHSCOPE_ENDPOINT=
# 默认 qwen-plus
BAILIAN_SEARCH_MODEL=
```

API Key 在 [百炼控制台](https://bailian.console.aliyun.com) 的 API-KEY 管理页面创建。

## 使用示例

```bash
# 基础搜索
python scripts/channels/bailian/bailian_search.py "Claude Code 最新功能" -m 5

# 深度检索
python scripts/channels/bailian/bailian_search.py "大模型价格战" --strategy max

# 限定最近 7 天与站点
python scripts/channels/bailian/bailian_search.py "AI 芯片" --freshness 7 --sites 36kr.com caixin.com

# 垂直领域（股票、天气、汇率等）
python scripts/channels/bailian/bailian_search.py "贵州茅台股价" --vertical

# JSON 输出，含模型回答
python scripts/channels/bailian/bailian_search.py "AI agent" --json
```

## 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `query` | 搜索关键词（必需） | - |
| `-m, --max-results` | 来源数量 | 10 |
| `--model` | 模型名称 | qwen-plus |
| `--strategy` | `turbo`、`max`、`agent`、`agent_max` | turbo |
| `--freshness` | 时间范围天数：7、30、180、365，仅 turbo | - |
| `--sites` | 限定站点域名，最多 25 个，仅 turbo | - |
| `--vertical` | 启用垂直领域搜索 | False |
| `--api-key` | DashScope API Key | - |
| `--endpoint` | 接口地址 | DashScope 文本生成接口 |
| `--timeout` | 请求超时秒数 | 60 |
| `--json` | JSON 输出 | False |

## 输出字段

来源列表 `title`、`href`、`engine`、`site_name`、`icon`、`index`；JSON 输出额外包含 `answer`（模型回答）、`usage`（含 `plugins.search.count`）、`extra_tool_info`（垂直领域附加数据）。

## 限制

- `agent`、`agent_max` 策略额外按次计费
- `freshness`、`assigned_site_list` 仅 qwen-plus、qwen-flash 与角色扮演模型支持
- qwen3.8 系列不支持 `agent` 策略

## 相关链接

- [百炼联网搜索文档](https://help.aliyun.com/zh/model-studio/web-search)
- [DashScope API 参考](https://help.aliyun.com/zh/model-studio/qwen-api-via-dashscope)
