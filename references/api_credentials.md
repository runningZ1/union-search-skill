# API 凭据获取指南

本文档提供所有支持平台的 API 凭据获取方法。

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
python scripts/github/github_search.py config --token YOUR_TOKEN

# 方式 2: 添加到 .env 文件
GITHUB_TOKEN=your_github_token_here
```

**权限说明**:
- 公共仓库搜索：无需特殊权限
- 私有仓库搜索：需要 `repo` 权限

---

## TikHub Token

**获取地址**: https://tikhub.io

**支持平台**: 小红书、抖音、Bilibili、Twitter

**步骤**:
1. 访问 TikHub 官网注册账号
2. 进入控制台获取 API Token
3. 查看配额和使用限制

**配置方式**:
```bash
# 添加到 .env 文件
TIKHUB_TOKEN=your_tikhub_token_here
```

**注意事项**:
- TikHub 提供免费试用额度
- 不同平台消耗不同的配额
- 建议查看官方文档了解最新定价

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

## 微博 Cookie

**获取方法**: 参考 [如何获取 cookie](https://github.com/dataabc/weiboSpider/blob/master/docs/cookie.md)

**步骤**:
1. 登录微博网页版
2. 打开浏览器开发者工具（F12）
3. 切换到 Network 标签
4. 刷新页面，找到任意请求
5. 复制 Request Headers 中的 Cookie 值

**配置方式**:
```bash
# 添加到 .env 文件
WEIBO_COOKIE=your_weibo_cookie_here
```

**注意事项**:
- Cookie 有效期约 3 个月
- 过期后需要重新获取
- 无法爬取自己的微博

---

## 知乎 Cookie

**获取方法**: 与微博类似

**步骤**:
1. 登录知乎网页版
2. 打开浏览器开发者工具（F12）
3. 切换到 Network 标签
4. 刷新页面，找到任意请求
5. 复制 Request Headers 中的 Cookie 值

**配置方式**:
```bash
# 添加到 .env 文件
ZHIHU_COOKIE=your_zhihu_cookie_here
```

---

## 无需 API 密钥的平台

以下平台无需 API 密钥即可使用：

- **DuckDuckGo** - 隐私友好搜索引擎
- **Brave** - 隐私保护搜索
- **Yahoo** - 传统搜索引擎
- **Bing** - 微软搜索引擎
- **Wikipedia** - 维基百科
- **Anna's Archive** - 电子书搜索
- **Reddit** - 社区讨论（无需 API）
- **图片搜索** - 17 个平台批量下载

**可选配置**:
```bash
# 可选：配置代理（如果需要）
DUCKDUCKGO_PROXY=http://127.0.0.1:7890
BRAVE_PROXY=http://127.0.0.1:7890
YAHOO_PROXY=http://127.0.0.1:7890
BING_PROXY=http://127.0.0.1:7890
WIKIPEDIA_PROXY=http://127.0.0.1:7890
ANNASARCHIVE_PROXY=http://127.0.0.1:7890
```

---

## 配置优先级

所有工具支持三种配置方式（优先级从高到低）：

1. **命令行参数**: `--token YOUR_TOKEN` 或 `--api-key YOUR_KEY`
2. **环境变量**: 在项目根目录的 `.env` 文件中配置
3. **配置文件**: 工具特定的配置文件（如 GitHub 的 `~/.github-search.json`）

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
