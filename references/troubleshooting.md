# 常见问题排查指南

本文档提供常见问题的诊断和解决方案。

## 目录

- [凭据相关问题](#凭据相关问题)
- [网络相关问题](#网络相关问题)
- [API 限制问题](#api-限制问题)
- [参数错误问题](#参数错误问题)
- [平台特定问题](#平台特定问题)

---

## 凭据相关问题

### 问题：缺少 API 凭据

**错误信息**:
```
Error: Missing API credentials
Error: GITHUB_TOKEN not found
Error: TIKHUB_TOKEN not found
```

**解决方案**:

1. **检查 .env 文件是否存在**
   ```bash
   cd C:\Users\zijie\.claude\skills\union-search-skill
   ls -la .env
   ```

2. **如果不存在，复制模板**
   ```bash
   cp .env.example .env
   ```

3. **编辑 .env 文件，填入有效凭据**
   ```bash
   # 使用文本编辑器打开
   notepad .env
   ```

4. **验证凭据格式**
   - GitHub Token: 以 `ghp_` 开头
   - TikHub Token: 长字符串
   - Google API Key: 以 `AIza` 开头

5. **使用命令行参数（临时方案）**
   ```bash
   python scripts/github/github_search.py repo "test" --token YOUR_TOKEN
   ```

**参考文档**: `references/api_credentials.md`

---

### 问题：凭据无效或过期

**错误信息**:
```
Error: 401 Unauthorized
Error: Invalid credentials
Error: Token expired
```

**解决方案**:

1. **GitHub Token**
   - 访问 https://github.com/settings/tokens
   - 检查 token 是否过期
   - 重新生成新的 token

2. **微博/知乎 Cookie**
   - Cookie 有效期约 3 个月
   - 重新登录获取新的 Cookie
   - 参考 `references/api_credentials.md`

3. **其他 API Key**
   - 检查 API Key 是否被撤销
   - 在平台控制台重新生成

---

## 网络相关问题

### 问题：网络超时

**错误信息**:
```
Error: Connection timeout
Error: Read timeout
requests.exceptions.Timeout
```

**解决方案**:

1. **检查网络连接**
   ```bash
   ping google.com
   ```

2. **增加超时时间（在 .env 中）**
   ```bash
   REQUEST_TIMEOUT=30
   ```

3. **使用代理**
   ```bash
   # 在 .env 中配置
   HTTP_PROXY=http://127.0.0.1:7890
   HTTPS_PROXY=http://127.0.0.1:7890

   # 或使用命令行参数
   python scripts/reddit/reddit_search.py search "test" --proxy http://127.0.0.1:7890
   ```

4. **检查防火墙设置**
   - 确保 Python 允许访问网络
   - 检查企业防火墙规则

---

### 问题：403 Forbidden

**错误信息**:
```
Error: 403 Forbidden
Access denied
```

**常见原因**:
- IP 被封禁
- 缺少认证信息
- 反爬虫机制触发

**解决方案**:

1. **Reddit 搜索**
   ```bash
   # 使用代理
   python scripts/reddit/reddit_search.py search "test" --proxy http://127.0.0.1:7890
   ```

2. **微博搜索**
   ```bash
   # 检查 Cookie 是否有效
   # 更新 .env 中的 WEIBO_COOKIE
   ```

3. **通用搜索引擎**
   ```bash
   # 使用代理避免 IP 限制
   DUCKDUCKGO_PROXY=http://127.0.0.1:7890
   BRAVE_PROXY=http://127.0.0.1:7890
   ```

4. **等待一段时间后重试**
   - IP 封禁通常是临时的
   - 建议等待 1-24 小时

---

### 问题：SSL 证书错误

**错误信息**:
```
Error: SSL certificate verification failed
requests.exceptions.SSLError
```

**解决方案**:

1. **更新 CA 证书**
   ```bash
   pip install --upgrade certifi
   ```

2. **临时禁用 SSL 验证（不推荐）**
   ```python
   # 仅用于调试
   import requests
   requests.get(url, verify=False)
   ```

3. **使用代理**
   - 某些代理会处理 SSL 证书

---

## API 限制问题

### 问题：速率限制（Rate Limit）

**错误信息**:
```
Error: 429 Too Many Requests
Rate limit exceeded
API rate limit exceeded
```

**解决方案**:

1. **GitHub API**
   ```bash
   # 检查剩余配额
   python scripts/github/github_search.py rate-limit

   # 等待速率限制重置
   # 已认证: 30 次/分钟
   # 未认证: 10 次/分钟
   ```

2. **YouTube API**
   ```bash
   # 检查每日配额使用情况
   # 默认: 10,000 单位/天
   # 搜索: 100 单位/次

   # 减少搜索次数
   python scripts/youtube/youtube_search.py "test" --limit 5
   ```

3. **通用策略**
   - 降低请求频率
   - 使用 `--limit` 限制结果数量
   - 实现请求间隔（1-2 秒）
   - 缓存搜索结果

**参考文档**: `references/rate_limits.md`

---

### 问题：配额用尽

**错误信息**:
```
Error: Quota exceeded
Daily quota exceeded
Monthly quota exceeded
```

**解决方案**:

1. **YouTube API**
   - 等待到第二天（太平洋时间午夜重置）
   - 或申请增加配额

2. **Google Custom Search**
   - 免费套餐: 100 次/天
   - 等待到第二天重置
   - 或升级到付费套餐

3. **Tavily Search**
   - 免费套餐: 1,000 积分/月
   - 等待到下个月重置
   - 或升级到付费套餐

4. **替代方案**
   - 使用无需 API 的平台（DuckDuckGo、Brave 等）
   - 切换到其他搜索引擎

---

## 参数错误问题

### 问题：无效参数

**错误信息**:
```
Error: Invalid argument
Error: Unrecognized arguments
Error: Missing required argument
```

**解决方案**:

1. **查看帮助信息**
   ```bash
   python scripts/github/github_search.py --help
   python scripts/reddit/reddit_search.py --help
   ```

2. **检查参数名称**
   ```bash
   # ❌ 错误
   python scripts/github/github_search.py repo "test" --star ">1000"

   # ✅ 正确
   python scripts/github/github_search.py repo "test" --stars ">1000"
   ```

3. **检查参数值格式**
   ```bash
   # ❌ 错误（缺少引号）
   python scripts/github/github_search.py repo "test" --stars >1000

   # ✅ 正确
   python scripts/github/github_search.py repo "test" --stars ">1000"
   ```

4. **查看模块文档**
   - 每个模块都有对应的 README
   - 例如: `scripts/github/GITHUB_README.md`

---

### 问题：参数冲突

**错误信息**:
```
Error: Conflicting arguments
Error: Cannot use both --json and --markdown
```

**解决方案**:

1. **检查互斥参数**
   ```bash
   # ❌ 错误（同时使用 --json 和 --markdown）
   python scripts/github/github_search.py repo "test" --json --markdown

   # ✅ 正确（只使用一个）
   python scripts/github/github_search.py repo "test" --json
   ```

2. **查看参数说明**
   - 阅读模块 README
   - 使用 `--help` 查看参数说明

---

## 平台特定问题

### GitHub 搜索

**问题：搜索结果为空**

**可能原因**:
- 搜索条件过于严格
- 仓库不存在或已删除
- 权限不足（私有仓库）

**解决方案**:
```bash
# 放宽搜索条件
python scripts/github/github_search.py repo "test" --stars ">100"  # 而不是 ">10000"

# 检查是否需要认证
python scripts/github/github_search.py config --token YOUR_TOKEN
```

---

### Reddit 搜索

**问题：403 Blocked**

**原因**: Reddit 有反爬虫机制

**解决方案**:
```bash
# 使用代理
python scripts/reddit/reddit_search.py search "test" --proxy http://127.0.0.1:7890

# 降低请求频率
python scripts/reddit/reddit_search.py search "test" --limit 10  # 而不是 100
```

---

### 小红书搜索

**问题：话题标签提取不完整**

**说明**: 仅提取带 `#` 前缀的话题标签

**示例**:
```
原文: "今天天气真好 #旅行 #美食"
提取: ["旅行", "美食"]
```

**解决方案**: 这是设计行为，无需修复

---

### 抖音搜索

**问题：搜索结果不准确**

**可能原因**:
- 关键词过于宽泛
- 内容类型过滤不当

**解决方案**:
```bash
# 使用更精确的关键词
python scripts/douyin/tikhub_douyin_search.py --keyword "Python教程" --limit 10

# 使用内容类型过滤
# content_type: 0=全部, 1=视频, 2=图文
python scripts/douyin/tikhub_douyin_search.py --keyword "美食" --content-type 1
```

---

### 微博搜索

**问题：无法爬取自己的微博**

**说明**: 这是微博平台的限制

**解决方案**: 使用其他账号的 Cookie

---

### YouTube 搜索

**问题：配额消耗过快**

**原因**: 搜索请求消耗 100 单位/次

**解决方案**:
```bash
# 限制搜索结果数量
python scripts/youtube/youtube_search.py "test" --limit 5

# 避免包含评论（额外消耗配额）
python scripts/youtube/youtube_search.py "test" --limit 5
# 而不是
python scripts/youtube/youtube_search.py "test" --limit 5 --include-comments
```

---

### 图片搜索

**问题：下载失败或速度慢**

**可能原因**:
- 网络问题
- 平台反爬虫
- 并发数过高

**解决方案**:
```bash
# 降低并发数
python scripts/union_image_search/multi_platform_image_search.py \
  --keyword "cats" \
  --num 50 \
  --threads 3 \
  --delay 2.0

# 指定特定平台
python scripts/union_image_search/multi_platform_image_search.py \
  --keyword "cats" \
  --platforms pixabay unsplash \
  --num 30
```

---

## 调试技巧

### 1. 启用详细日志

```bash
# 设置环境变量
export DEBUG=1

# 或在脚本中添加
import logging
logging.basicConfig(level=logging.DEBUG)
```

### 2. 保存原始响应

```bash
# 使用 --save-raw 参数
python scripts/github/github_search.py repo "test" --save-raw

# 响应保存在 responses/ 目录
ls responses/
```

### 3. 使用 curl 测试 API

```bash
# 测试 GitHub API
curl -H "Authorization: token YOUR_TOKEN" \
  https://api.github.com/search/repositories?q=test

# 测试 Google Custom Search
curl "https://www.googleapis.com/customsearch/v1?key=YOUR_KEY&cx=YOUR_CX&q=test"
```

### 4. 检查依赖版本

```bash
# 列出已安装的包
pip list | grep requests
pip list | grep python-dotenv

# 更新依赖
pip install --upgrade requests python-dotenv
```

---

## 获取帮助

### 1. 查看模块文档

每个模块都有详细的 README：
- `scripts/github/GITHUB_README.md`
- `scripts/reddit/REDDIT_README.md`
- `scripts/google_search/GOOGLE_SEARCH_README.md`
- 等等...

### 2. 查看参考文档

- `references/api_credentials.md` - API 凭据获取
- `references/rate_limits.md` - 速率限制说明
- `references/google_search_guide.md` - Google 搜索技巧

### 3. 使用 --help 参数

```bash
python scripts/github/github_search.py --help
python scripts/reddit/reddit_search.py --help
```

### 4. 检查日志文件

某些模块会生成日志文件：
- `scripts/reddit/reddit_search.log`
- `scripts/reddit/YARS.log`

---

## 常见错误速查表

| 错误信息 | 可能原因 | 解决方案 |
|---------|---------|---------|
| Missing API credentials | 缺少凭据 | 检查 .env 文件 |
| 401 Unauthorized | 凭据无效 | 重新生成 token/cookie |
| 403 Forbidden | IP 被封禁 | 使用代理 |
| 429 Too Many Requests | 速率限制 | 降低请求频率 |
| Connection timeout | 网络超时 | 增加超时时间或使用代理 |
| SSL certificate error | 证书问题 | 更新 certifi |
| Invalid argument | 参数错误 | 查看 --help |
| Quota exceeded | 配额用尽 | 等待重置或升级套餐 |

---

## 预防措施

### 1. 合理使用 API

- 使用 `--limit` 控制结果数量
- 避免频繁请求相同内容
- 实现本地缓存机制

### 2. 监控配额使用

- 定期检查 API 配额
- 设置告警阈值
- 记录每次请求的消耗

### 3. 实现错误处理

- 捕获异常并记录日志
- 实现自动重试机制
- 使用指数退避策略

### 4. 保持凭据安全

- 不要提交 .env 到 Git
- 定期轮换 API Key
- 使用最小权限原则

---

## 总结

大多数问题可以通过以下步骤解决：

1. **检查凭据**: 确保 .env 文件配置正确
2. **查看文档**: 阅读模块 README 和参考文档
3. **使用 --help**: 查看参数说明
4. **降低频率**: 避免触发速率限制
5. **使用代理**: 解决网络和 IP 限制问题
6. **保存响应**: 使用 --save-raw 调试 API 问题
7. **查看日志**: 检查错误日志文件

如果问题仍未解决，请查看具体模块的 README 或提交 Issue。
