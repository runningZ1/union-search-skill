# 智谱网络搜索

智谱 GLM 的独立网络搜索接口，返回标题、链接、摘要、站点名与发布日期。

## 功能特性

- 四个引擎：基础、高级、搜狗、夸克
- 可按域名与时间范围过滤
- 摘要长度可选 `medium`、`high`
- 可选意图识别，无搜索意图时不发起检索

## 配置

在项目根目录的 `.env` 文件中添加：

```bash
ZHIPU_API_KEY=your_zhipu_api_key_here
# 默认 search_std，可选 search_pro、search_pro_sogou、search_pro_quark
ZHIPU_SEARCH_ENGINE=search_std
# 默认 https://open.bigmodel.cn/api/paas/v4/web_search
ZHIPU_WEB_SEARCH_ENDPOINT=
```

API Key 在 [智谱开放平台](https://bigmodel.cn/apikey/platform) 创建。

## 使用示例

```bash
# 基础搜索
python scripts/channels/zhipu/zhipu_search.py "人工智能最新进展" -m 10

# 高级引擎，限定最近一周
python scripts/channels/zhipu/zhipu_search.py "人工智能最新进展" --engine search_pro --recency oneWeek --content-size high

# JSON 输出
python scripts/channels/zhipu/zhipu_search.py "人工智能最新进展" --json
```

## 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `query` | 搜索关键词（必需），最长 70 个字符 | - |
| `-m, --max-results` | 返回数量，1-50 | 10 |
| `--engine` | `search_std`、`search_pro`、`search_pro_sogou`、`search_pro_quark` | search_std |
| `--domain` | 域名白名单 | - |
| `--recency` | `oneDay`、`oneWeek`、`oneMonth`、`oneYear`、`noLimit` | noLimit |
| `--content-size` | `medium`、`high` | medium |
| `--search-intent` | 开启意图识别 | 关闭 |
| `--api-key` | API Key（优先于环境变量） | - |
| `--endpoint` | 接口地址 | https://open.bigmodel.cn/api/paas/v4/web_search |
| `--timeout` | 请求超时秒数 | 30 |
| `--json` | JSON 输出 | False |

搜狗引擎的结果数量只接受 10、20、30、40、50，传入其他数值时取最接近的一档。

## 输出字段

`title`、`href`、`body`、`engine`、`media`、`publish_date`、`refer`、`keywords`、`request_id`。

## 计费

| 引擎 | 单价 |
|------|------|
| `search_std` | 0.01 元/次 |
| `search_pro` | 0.03 元/次 |
| `search_pro_sogou` | 0.05 元/次 |
| `search_pro_quark` | 0.05 元/次 |

错误码 `1701` 表示并发超限，`1702` 表示引擎不可用，`1703` 表示引擎没有可用结果。

## 相关链接

- [联网搜索指南](https://docs.bigmodel.cn/cn/guide/tools/web-search)
- [网络搜索 API](https://docs.bigmodel.cn/api-reference/工具-api/网络搜索)
