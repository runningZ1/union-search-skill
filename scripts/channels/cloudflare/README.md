# Cloudflare Web Search

通过 Cloudflare AI Gateway 调用 Ceramic.ai、Exa、Linkup 三个搜索提供商，返回统一的标题、链接与描述。

## 功能特性

- 一次请求切换三个提供商，结果字段相同
- 单次最多 10 条结果
- 可用网关额度计费，也可使用网关上已保存的提供商密钥
- 搜索记录进入 AI Gateway 的日志与统计

## 配置

在项目根目录的 `.env` 文件中添加：

```bash
CLOUDFLARE_API_TOKEN=your_cloudflare_api_token_here
CLOUDFLARE_ACCOUNT_ID=your_cloudflare_account_id_here
# 默认 ceramic，可选 exa、linkup
CLOUDFLARE_WEBSEARCH_PROVIDER=ceramic
# 默认 default
CLOUDFLARE_GATEWAY_ID=
# 使用自己的提供商密钥时填写别名
CLOUDFLARE_BYOK_ALIAS=
```

API Token 需要账号级 Workers AI Read 与 AI Gateway Read 权限。Account ID 在 Cloudflare 控制台右侧栏查看。账号自带名为 `default` 的 AI Gateway。

## 使用示例

```bash
# 基础搜索，默认 ceramic
python scripts/channels/cloudflare/cloudflare_search.py "AI agent" -m 5

# 切换提供商
python scripts/channels/cloudflare/cloudflare_search.py "AI agent" --provider exa

# 使用网关上保存的密钥
python scripts/channels/cloudflare/cloudflare_search.py "AI agent" --provider exa --byok-alias default

# JSON 输出
python scripts/channels/cloudflare/cloudflare_search.py "AI agent" --json
```

## 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `query` | 搜索关键词（必需），最长 1024 字符 | - |
| `-m, --max-results` | 返回数量，1-10 | 10 |
| `--provider` | `ceramic`、`exa`、`linkup` | ceramic |
| `--gateway-id` | AI Gateway ID | default |
| `--byok-alias` | 网关上已保存的提供商密钥别名 | 空 |
| `--api-token` | API Token（优先于环境变量） | - |
| `--account-id` | Account ID（优先于环境变量） | - |
| `--base-url` | 接口根地址 | https://api.cloudflare.com/client/v4 |
| `--timeout` | 请求超时秒数 | 30 |
| `--json` | JSON 输出 | False |

## 输出字段

`title`、`href`、`body`、`engine`、`provider`、`request_id`、`latency_ms`。

## 计费

| 提供商 | 每 1000 次请求 |
|--------|----------------|
| ceramic | 0.25 美元 |
| linkup | 5.00 美元 |
| exa | 7.00 美元 |

填写 `byok_alias` 后由提供商直接计费。别名不存在时返回 HTTP 400，不会扣网关额度。

## 相关链接

- [Web Search 概览](https://developers.cloudflare.com/web-search/)
- [调用方式](https://developers.cloudflare.com/web-search/how-to-use/)
- [提供商](https://developers.cloudflare.com/web-search/providers/)
