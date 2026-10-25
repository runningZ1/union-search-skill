# API 凭据获取指南

本文档提供搜索渠道的凭据配置说明。任务选择见[根技能任务入口](../SKILL.md#任务入口)，渠道与分组以 `python union_search_cli.py list --pretty` 为准。无需 API Key 仅说明不要求服务密钥；部分渠道仍需本机账号登录、OAuth 凭据或可选 Token。

希望由 Agent 协助操作平台并保存配置时，使用 [Agent 自动获取与配置 API Key 指南](agent_api_key_setup.md)。其中提供可直接复制的任务、授权和续接提示词；本文保留各平台的手动获取说明。

## GitHub Token

**获取地址**: https://github.com/settings/tokens

**步骤**:
1. 登录 GitHub 账号
2. 访问 Settings → Developer settings → Personal access tokens → Tokens (classic)
3. 点击 "Generate new token (classic)"
4. 选择权限（公共搜索无需特殊权限）
5. 生成并复制 token

**配置方式**:
```bash
# 方式 1: 使用配置命令（推荐）
python scripts/channels/github_search/github_search.py config --token YOUR_TOKEN

# 方式 2: 添加到 .env 文件
GITHUB_TOKEN=your_github_token_here
```

**权限说明**:
- 公共仓库搜索：无需特殊权限
- 私有仓库搜索：需要 `repo` 权限

---

## Google Custom Search API

**获取地址**:
- API Key: https://console.cloud.google.com/apis/credentials
- Search Engine ID: https://programmablesearchengine.google.com/

**步骤**:

### 1. 获取 API Key
1. 访问 Google Cloud Console
2. 创建或选择项目
3. 启用 "Custom Search API"
4. 创建凭据 → API 密钥
5. 复制 API Key

### 2. 创建搜索引擎
1. 访问 Programmable Search Engine
2. 点击 "添加" 或 "新增搜索引擎"
3. 选择 "搜索整个网络"
4. 创建后获取 Search Engine ID

**配置方式**:
```bash
# 添加到 .env 文件
GOOGLE_API_KEY=your_google_api_key_here
GOOGLE_SEARCH_ENGINE_ID=your_search_engine_id_here
```

**配额限制**:
- 免费套餐：100 次查询/天
- 付费套餐：$5/1000 次查询

---

## Tavily API Key

**获取地址**: https://tavily.com

**步骤**:
1. 访问 Tavily 官网注册账号
2. 进入 Dashboard
3. 复制 API Key

**配置方式**:
```bash
# 添加到 .env 文件
TAVILY_API_KEY=tvly-your_tavily_api_key_here
```

**免费额度**:
- 每月 1000 积分
- 基础搜索：1 积分/次
- 高级搜索：2 积分/次

---

## 百度千帆 API Key

**获取地址**: https://console.bce.baidu.com/ai-search/qianfan/ais/console/apiKey

**步骤**:
1. 登录百度智能云账号
2. 进入 AI Search 控制台
3. 创建应用或在已有应用中查看 API Key
4. 复制 `bce-v3/...` 格式的 API Key

**配置方式**:
```bash
# 推荐变量名（新）
BAIDU_API_KEY=your_baidu_api_key_here

# 兼容旧变量名（可选）
BAIDU_QIANFAN_API_KEY=your_baidu_api_key_here
```

**详细指引**:
- 参考 [baidu_apikey_fetch.md](baidu_apikey_fetch.md)

---

## YouTube Data API

**获取地址**: https://console.cloud.google.com/apis/credentials

**步骤**:
1. 访问 Google Cloud Console
2. 创建或选择项目
3. 启用 "YouTube Data API v3"
4. 创建凭据 → API 密钥
5. 复制 API Key

**配置方式**:
```bash
# 添加到 .env 文件
YOUTUBE_API_KEY=your_youtube_api_key_here
```

**配额说明**:
- 每日配额：10,000 单位（默认）
- 搜索请求：100 单位/次
- Videos.list：1 单位/次
- 可申请增加配额

---

## 无需 API 密钥的平台

`no_api_key` 按认证条件分组，成员及访问要求以 CLI 能力清单为准：

- **DuckDuckGo、Brave、Yahoo、Wikipedia**：不要求 API Key，可按渠道配置代理。
- **网页直连渠道**：`baidu_direct`、`bing_cn_direct`、`bing_int_direct`、`sogou_direct`、`so360_direct`、`quark_direct`、`yandex_direct` 等使用网页入口，可能受到验证码或限流限制。`bing` 与 `yandex` 的 SerpAPI 渠道接受任一非空的 `SERPAPI_API_KEY*` 变量，包括 `SERPAPI_API_KEY_1` 等编号名称；`doctor` 同样识别这些名称。
- **Reddit**：不要求 API Key，独立入口为 `scripts/channels/reddit/cli.py`，可能返回 403。
- **GitHub**：`GITHUB_TOKEN` 为可选凭据；访问私有资源需要相应权限。
- **本机账号搜索**：`claude_code`、`codex`、`grok_build` 需要对应工具的账号登录及额度，要求见[本机工具说明](../scripts/channels/ai_tools/README.md)。

图片搜索独立提供 **24 个平台（12 个原生平台、12 个 SDK 平台）**，默认选择 `baidu bing wikicommons`。凭据要求按平台确定，火山引擎需要 `VOLCENGINE_API_KEY`；不能将全部图片平台视为无需凭据。平台列表及参数见[图片说明](../scripts/union_image_search/README.md)。

**可选代理配置**：
```bash
DUCKDUCKGO_PROXY=http://127.0.0.1:7890
BRAVE_PROXY=http://127.0.0.1:7890
YAHOO_PROXY=http://127.0.0.1:7890
WIKIPEDIA_PROXY=http://127.0.0.1:7890
```

---

## Firecrawl API Key

**获取地址**: https://www.firecrawl.dev/app

**步骤**:
1. 登录 Firecrawl 控制台
2. 进入 API Keys 页面
3. 创建并复制 API Key（`fc-` 开头）

**配置方式**:
```bash
# 添加到 .env 文件
FIRECRAWL_API_KEY=fc-your_firecrawl_api_key_here

# 自建 Firecrawl 服务
FIRECRAWL_API_URL=https://your-firecrawl-instance
```

**计费**:
- 搜索：每 10 条结果 2 credits
- 抓取正文：1 credit/页

---

## DeepSeek API Key

**获取地址**: https://platform.deepseek.com/api_keys

**步骤**:
1. 登录 DeepSeek 开放平台
2. 进入 API keys 页面
3. 创建并复制 API Key（`sk-` 开头）

**配置方式**:
```bash
# 添加到 .env 文件
DEEPSEEK_API_KEY=sk-your_deepseek_api_key_here

# 代理或私有网关
DEEPSEEK_API_URL=https://api.deepseek.com
```

**计费**:
- 搜索：5 元/1000 次成功请求
- 账号级限速约 100 QPS

---

## 腾讯元宝搜索 API Key

**获取地址**: https://console.cloud.tencent.com/wsa

**步骤**:
1. 完成腾讯云实名认证
2. 在联网搜索控制台开通服务
3. 进入「概览 > 服务 API KEY 方式 > 创建 API KEY」
4. 复制 API Key，明文只在创建时展示一次

**配置方式**:
```bash
# 添加到 .env 文件
TENCENTCLOUD_WSA_APIKEY=sk-your_tencentcloud_wsa_api_key_here

# 默认接口地址
TENCENTCLOUD_WSA_ENDPOINT=https://api.wsa.cloud.tencent.com/SearchPro
```

**注意事项**:
- 每个子账号最多创建 3 个 Key
- 子账号需由主账号授予 WSA 全部读写权限
- 未开通服务时返回 `ResourceNotFound`

---

## TinyFish API Key

**获取地址**: https://www.tinyfish.ai

**步骤**:
1. 注册 TinyFish 账号（无需信用卡）
2. 进入控制台创建 API Key
3. 复制 Key

**配置方式**:
```bash
# 添加到 .env 文件
TINYFISH_API_KEY=your_tinyfish_api_key_here
```

**注意事项**:
- 默认限速 5 次/分钟，超限返回 429
- 请求头使用 `X-API-Key`，接口为 `GET https://api.search.tinyfish.ai`

---

## AnySearch API Key（必填）

**获取地址**: https://anysearch.com/console/api-keys

**步骤**:
1. 注册 AnySearch 账号
2. 进入 API Keys 页面创建 Key
3. 复制 Key

**配置方式**:
```bash
# 必填：添加到 .env 文件
ANYSEARCH_API_KEY=your_anysearch_api_key_here
```

**注意事项**:
- 使用 AnySearch 必须配置有效的 `ANYSEARCH_API_KEY`
- 鉴权方式为 `Authorization: Bearer <key>`

---

## 阿里云百炼 DashScope API Key

**获取地址**: https://bailian.console.aliyun.com

**步骤**:
1. 登录阿里云百炼控制台
2. 进入 API-KEY 管理页面
3. 创建并复制 API Key

**配置方式**:
```bash
# 添加到 .env 文件
DASHSCOPE_API_KEY=sk-your_dashscope_api_key_here

# 可选：更换模型，默认 qwen-plus
BAILIAN_SEARCH_MODEL=qwen-plus
```

**注意事项**:
- 联网搜索通过 `enable_search` 参数开启，返回 `search_info.search_results`
- `freshness`、`assigned_site_list` 仅 `turbo` 策略与 qwen-plus、qwen-flash 系列支持
- 搜索按次数计费，同时消耗模型 token

---

## 知乎开放平台 Access Secret

**获取地址**: https://developer.zhihu.com

**步骤**:
1. 登录知乎开放平台
2. 在控制台创建应用
3. 复制 Access Secret

**配置方式**:
```bash
# 添加到 .env 文件
ZHIHU_ACCESS_SECRET=your_access_secret_here
```

**能力范围**:
- 站内搜索 `/api/v1/content/zhihu_search`，最多 10 条
- 全网搜索 `/api/v1/content/global_search`，最多 20 条
- 热榜 `/api/v1/content/hot_list`，最多 30 条
- 直答 `/v1/chat/completions`，模型 `zhida-fast-1p5`、`zhida-thinking-1p5`、`zhida-agent`

---

## Parallel API Key

**获取地址**: https://platform.parallel.ai

**步骤**:
1. 登录 Parallel Platform
2. 创建 API Key
3. 复制 Key

**配置方式**:
```bash
# 添加到 .env 文件
PARALLEL_API_KEY=your_parallel_api_key_here

# 默认 fast，可选 turbo、basic、advanced
PARALLEL_SEARCH_MODE=fast
```

**注意事项**:
- 接口为 `POST https://api.parallel.ai/v1/search`，请求头 `x-api-key`
- 默认限速 600 次/分钟
- 欧盟节点 `https://eu.parallel.ai` 只接受 `basic` 模式

---

## Ollama API Key

**获取地址**: https://ollama.com/settings/keys

**步骤**:
1. 注册 Ollama 免费账号
2. 进入 Keys 页面创建 API Key
3. 复制 Key

**配置方式**:
```bash
# 添加到 .env 文件
OLLAMA_API_KEY=your_ollama_api_key_here
```

**注意事项**:
- 接口为 `POST https://ollama.com/api/web_search`，请求头 `Authorization: Bearer`
- 单次最多 10 条，默认 5 条
- 官方文档未公布速率限制与价格

---

## 智谱 API Key

**获取地址**: https://bigmodel.cn/apikey/platform

**步骤**:
1. 登录智谱开放平台
2. 进入 API Key 管理页面
3. 创建并复制 API Key

**配置方式**:
```bash
# 添加到 .env 文件
ZHIPU_API_KEY=your_zhipu_api_key_here

# 默认 search_std
ZHIPU_SEARCH_ENGINE=search_std
```

**注意事项**:
- 接口为 `POST https://open.bigmodel.cn/api/paas/v4/web_search`
- 关键词最长 70 个字符，结果数量 1-50
- `search_std` 0.01 元/次，`search_pro` 0.03 元/次，搜狗与夸克各 0.05 元/次

---

## Kimi API Key

**获取地址**: https://platform.kimi.com

**步骤**:
1. 登录 Kimi 开放平台
2. 创建 API Key
3. 复制 Key

**配置方式**:
```bash
# 添加到 .env 文件
MOONSHOT_API_KEY=your_moonshot_api_key_here

# 默认 search，可选 search_pro
KIMI_SEARCH_TIER=search
```

**注意事项**:
- 基础搜索 `POST /v1/tools/search`，0.01 元/次
- 专业搜索 `POST /v1/tools/search_pro`，0.015 元/次
- 结果数量 1-20，站点最多 5 个
- 对话补全内置的 `$web_search` 预计 2026 年 10 月 20 日下线，本渠道使用独立接口

---

## 配置优先级

配置来源与优先级取决于具体入口，使用前查看对应脚本 `--help` 和渠道 README：

- **命令行参数**：部分脚本支持 `--token` 或 `--api-key`，不能假定所有入口均支持。
- **环境变量**：按渠道要求配置变量；支持 `.env` 的入口从指定位置加载配置，是否覆盖进程变量由实现决定。
- **工具配置文件与登录状态**：GitHub 可使用 `~/.github-search.json`；本机账号渠道使用对应工具的认证配置。

---

## 安全建议

1. **不要提交凭据到 Git**
   - `.env` 文件已在 `.gitignore` 中
   - 使用 `.env.example` 作为模板

2. **定期轮换密钥**
   - API Key 建议每 3-6 个月更换
   - Cookie 过期后及时更新

3. **最小权限原则**
   - 只授予必要的权限
   - GitHub Token 公共搜索无需特殊权限

4. **监控使用量**
   - 定期检查 API 配额使用情况
   - 避免超出免费额度
