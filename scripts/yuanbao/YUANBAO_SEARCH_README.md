# 腾讯元宝搜索

腾讯云联网搜索 Web Search API（WSA），底层结合互联网公开资源、腾讯内容生态与元宝 App 的联网搜索实践。

## 功能特性

- 服务 API KEY 方式调用，`Authorization: Bearer` 鉴权
- 结果类型可选公开网页、权威垂直信源或混合
- 支持垂直领域（政府、新闻、学术、金融）
- 支持时间范围过滤与域名限定
- 每条结果带相关度 `score`，旗舰版带权威度与子链接

## 配置

在项目根目录的 `.env` 文件中添加：

```bash
TENCENTCLOUD_WSA_APIKEY=sk-your_api_key
# 默认 https://api.wsa.cloud.tencent.com/SearchPro
TENCENTCLOUD_WSA_ENDPOINT=
```

API Key 在腾讯云联网搜索控制台的「概览 > 服务 API KEY 方式 > 创建 API KEY」创建，明文只在创建时展示一次。每个子账号最多 3 个 Key，子账号需由主账号授予 WSA 全部读写权限。

调用前需要在控制台开通联网搜索服务。

## 使用示例

```bash
# 基础搜索
python scripts/yuanbao/yuanbao_search.py "三星堆的由来" -m 10

# 只看权威垂直信源
python scripts/yuanbao/yuanbao_search.py "人工智能政策" --mode 1 --industry gov

# 限定时间与域名
python scripts/yuanbao/yuanbao_search.py "大模型" --freshness d3 --site zhihu.com

# 返回子链接（旗舰版）
python scripts/yuanbao/yuanbao_search.py "腾讯财报" --deeplinks

# JSON 输出
python scripts/yuanbao/yuanbao_search.py "AI agent" --json
```

## 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `query` | 搜索关键词（必需） | - |
| `-m, --max-results` | 结果数量，接口按 10 条取整，最多 50 | 10 |
| `--mode` | 0 公开网页、1 权威垂直信源、2 混合 | 接口默认 |
| `--site` | 限定域名；排除用 `exclude:qq.com\|sohu.com` | - |
| `--industry` | `gov`、`news`、`acad`、`finance` | - |
| `--freshness` | `d3`、`m1`、`y1`、`2026-01-01,2026-02-01` | - |
| `--deeplinks` | 返回子链接（旗舰版） | False |
| `--api-key` | API Key（优先于环境变量） | - |
| `--endpoint` | 接口地址 | https://api.wsa.cloud.tencent.com/SearchPro |
| `--timeout` | 请求超时秒数 | 30 |
| `--json` | JSON 输出 | False |

极速版不支持 `Mode`、`Cnt`、`Industry`、`Deeplinks` 参数。

## 输出字段

每条结果包含 `title`、`href`、`body`、`engine`、`content`、`site`、`date`、`score`、`authority_level`、`favicon`、`images`、`deeplinks`。

## 错误码

| 错误码 | 含义 |
|--------|------|
| `InternalError` | 服务内部错误 |
| `InvalidParameter` | 参数错误 |
| `RequestLimitExceeded` | 请求频率超限 |
| `ResourceNotFound` | 服务未开通 |
| `ResourceUnavailable` | 服务不可用，常见于账号欠费 |
| `UnauthorizedOperation` | API Key 不正确或无权限 |

## 相关链接

- [SearchPro 接口文档](https://cloud.tencent.com/document/api/1806/121811)
- [服务 API KEY 方式](https://cloud.tencent.com/document/product/1806/130615)
