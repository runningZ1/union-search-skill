# 平台特定说明

本文档提供各平台的特殊说明、限制和注意事项。

## 目录

- [小红书（Xiaohongshu）](#小红书xiaohongshu)
- [抖音（Douyin）](#抖音douyin)
- [Bilibili](#bilibili)
- [微博（Weibo）](#微博weibo)
- [YouTube](#youtube)
- [GitHub](#github)
- [Reddit](#reddit)
- [图片搜索](#图片搜索)

---

## 小红书（Xiaohongshu）

### 话题标签提取规则

**仅提取带 `#` 前缀的话题标签**

示例：
```
原文: "今天天气真好 #旅行 #美食 分享一下"
提取结果: ["旅行", "美食"]

原文: "Python 编程 机器学习"
提取结果: []（无 # 前缀）
```

### 内容类型过滤

使用 `--content-type` 参数：
- `0`: 全部内容
- `1`: 仅视频
- `2`: 仅图片

示例：
```bash
# 仅搜索视频
python scripts/xiaohongshu/tikhub_xhs_search.py --keyword "美食" --content-type 1

# 仅搜索图片
python scripts/xiaohongshu/tikhub_xhs_search.py --keyword "旅行" --content-type 2
```

### 排序选项

支持按以下字段排序：
- `likes`: 点赞数
- `comments`: 评论数
- `shares`: 分享数
- `time`: 发布时间

示例：
```bash
# 按点赞数降序
python scripts/xiaohongshu/tikhub_xhs_search.py \
  --keyword "美食" \
  --sort-field likes \
  --sort-order desc
```

### 注意事项

1. **API 限制**: 使用 TikHub API，需要有效的 token
2. **搜索精度**: 关键词越精确，结果越准确
3. **时间过滤**: 支持按发布时间过滤（如果 API 支持）

---

## 抖音（Douyin）

### 高级过滤选项

#### 视频时长过滤
- `0`: 全部时长
- `1`: 0-1 分钟
- `2`: 1-5 分钟
- `3`: 5 分钟以上

#### 内容类型过滤
- `0`: 全部类型
- `1`: 视频
- `2`: 图文

示例：
```bash
# 搜索 1-5 分钟的视频
python scripts/douyin/tikhub_douyin_search.py \
  --keyword "Python教程" \
  --duration 2

# 搜索图文内容
python scripts/douyin/tikhub_douyin_search.py \
  --keyword "美食" \
  --content-type 2
```

### 分页机制

抖音使用游标（cursor）分页：
```bash
# 第一页
python scripts/douyin/tikhub_douyin_search.py --keyword "test" --page 1

# 第二页（使用返回的 cursor）
python scripts/douyin/tikhub_douyin_search.py --keyword "test" --cursor "xxx"
```

### 注意事项

1. **API 限制**: 使用 TikHub API，需要有效的 token
2. **搜索结果**: 结果数量受平台限制
3. **内容审核**: 某些敏感内容可能无法搜索

---

## Bilibili

### 双 API 支持

Bilibili 提供两种搜索方式：

#### 1. TikHub API（简单快速）
```bash
python scripts/bilibili/tikhub_bili_search.py "原神" --page 1 --page-size 20
```

**优点**:
- 简单易用
- 统一的 TikHub token

**缺点**:
- 功能相对有限
- 依赖第三方 API

#### 2. 官方 API（功能更全）
```bash
python scripts/bilibili/bilibili_api_search.py "Python教程" --limit 5
```

**优点**:
- 官方支持
- 功能更丰富
- 支持更多排序选项

**缺点**:
- 需要配置 Bilibili 账号
- 可能需要处理验证码

### 排序选项（官方 API）

- `totalrank`: 综合排序（默认）
- `click`: 播放量
- `pubdate`: 发布时间
- `dm`: 弹幕数
- `stow`: 收藏数

示例：
```bash
# 按播放量排序
python scripts/bilibili/bilibili_api_search.py "机器学习" --order click --limit 10
```

### 注意事项

1. **选择合适的 API**: 简单搜索用 TikHub，高级功能用官方 API
2. **配置要求**: 官方 API 需要配置 `config.py`
3. **速率限制**: 注意不要过于频繁请求

---

## 微博（Weibo）

### Cookie 认证

微博搜索基于 Cookie 认证，不使用官方 API。

#### 获取 Cookie

1. 登录微博网页版
2. 打开浏览器开发者工具（F12）
3. 切换到 Network 标签
4. 刷新页面，找到任意请求
5. 复制 Request Headers 中的 Cookie 值

参考: https://github.com/dataabc/weiboSpider/blob/master/docs/cookie.md

#### 配置 Cookie

```bash
# 在 .env 文件中
WEIBO_COOKIE=your_weibo_cookie_here
```

### 过滤选项

使用 `--filter` 参数：
- `0`: 全部微博
- `1`: 原创微博
- `2`: 图片微博
- `3`: 视频微博
- `4`: 音乐微博

示例：
```bash
# 仅搜索原创微博
python scripts/weibo/weibo_search.py --user-id 1669879400 --filter 1 --limit 20
```

### 时间范围

支持按时间范围过滤：
```bash
python scripts/weibo/weibo_search.py \
  --user-id 1669879400 \
  --since-date 2025-01-01 \
  --end-date 2025-12-31
```

### 注意事项

1. **Cookie 有效期**: 约 3 个月，过期后需要重新获取
2. **无法爬取自己的微博**: 这是微博平台的限制
3. **速率限制**: 建议请求间隔 1-2 秒
4. **账号安全**: 过于频繁的请求可能导致账号被限制

---

## YouTube

### 配额系统

YouTube Data API 使用配额系统：

| 操作 | 消耗配额 |
|------|----------|
| 搜索 | 100 单位 |
| Videos.list | 1 单位 |
| CommentThreads.list | 1 单位 |

**每日配额**: 10,000 单位（默认）

### 配额计算示例

```bash
# 搜索 10 个视频
python scripts/youtube/youtube_search.py "test" --limit 10
# 消耗: 100 单位（搜索）+ 10 单位（视频详情）= 110 单位

# 包含评论
python scripts/youtube/youtube_search.py "test" --limit 10 --include-comments --max-comments 5
# 消耗: 100 + 10 + 10 = 120 单位
```

### 节省配额技巧

1. **限制搜索结果数量**
   ```bash
   python scripts/youtube/youtube_search.py "test" --limit 5
   ```

2. **避免包含评论**
   ```bash
   # 不使用 --include-comments
   python scripts/youtube/youtube_search.py "test" --limit 10
   ```

3. **缓存搜索结果**
   - 使用 `--save-raw` 保存原始响应
   - 避免重复搜索相同内容

### 注意事项

1. **配额重置**: 每天太平洋时间午夜重置
2. **申请增加配额**: 可在 Google Cloud Console 申请
3. **监控使用量**: 定期检查配额使用情况

---

## GitHub

### 速率限制

| 认证状态 | 搜索限制 | 核心 API 限制 |
|---------|---------|--------------|
| 已认证 | 30 次/分钟 | 5,000 次/小时 |
| 未认证 | 10 次/分钟 | 60 次/小时 |

### 检查速率限制

```bash
python scripts/github/github_search.py rate-limit
```

输出示例：
```
Search API:
  Limit: 30
  Remaining: 28
  Reset: 2025-02-16 14:30:00

Core API:
  Limit: 5000
  Remaining: 4998
  Reset: 2025-02-16 15:00:00
```

### 搜索技巧

#### 1. 仓库搜索
```bash
# 按语言过滤
python scripts/github/github_search.py repo "machine learning" --language python

# 按星标过滤
python scripts/github/github_search.py repo "web framework" --stars ">1000"

# 按主题过滤
python scripts/github/github_search.py repo "test" --topic "machine-learning"
```

#### 2. 代码搜索
```bash
# 按语言搜索
python scripts/github/github_search.py code "async def" --language python

# 在特定仓库搜索
python scripts/github/github_search.py code "OAuth2" --repo "flask"

# 按文件扩展名搜索
python scripts/github/github_search.py code "import" --extension py
```

#### 3. Issues 搜索
```bash
# 搜索开放的 issues
python scripts/github/github_search.py issue "bug" --state open

# 按标签过滤
python scripts/github/github_search.py issue "feature" --label "help wanted"

# 搜索 Pull Requests
python scripts/github/github_search.py issue "update" --is-pr
```

### 注意事项

1. **认证推荐**: 使用 token 认证提高速率限制
2. **搜索精度**: 使用精确的关键词和过滤条件
3. **缓存结果**: 避免重复搜索相同内容

---

## Reddit

### 无需 API Key

Reddit 搜索不需要 API Key，基于网页爬虫。

### 反爬虫机制

Reddit 有反爬虫机制，可能遇到 403 错误。

**解决方案**:
```bash
# 使用代理
python scripts/reddit/reddit_search.py search "test" --proxy http://127.0.0.1:7890
```

### 搜索类型

#### 1. 全站搜索
```bash
python scripts/reddit/reddit_search.py search "python tutorial" --limit 10
```

#### 2. 子版块搜索
```bash
python scripts/reddit/reddit_search.py subreddit-search python "async await" --limit 10
```

#### 3. 获取帖子详情
```bash
python scripts/reddit/reddit_search.py post /r/python/comments/abc123/title/ --include-comments
```

### 自动保护机制

- 内置自动重试
- 指数退避策略
- 限流保护

### 注意事项

1. **使用代理**: 避免 IP 被封禁
2. **请求间隔**: 建议 2-3 秒
3. **限制结果数量**: 使用 `--limit` 控制

---

## 图片搜索

### 支持的 17 个平台

#### 搜索引擎
- 百度、Bing、Google、360、搜狗、DuckDuckGo、Yandex、Yahoo

#### 图库网站
- Pixabay、Pexels、Unsplash、Foodiesfeed

#### 动漫图片
- Danbooru、Gelbooru、Safebooru

#### 其他
- 花瓣网、次元小镇

### 完全独立

- **无需 API 密钥**: 完全免费
- **基于 pyimagedl**: 使用 `pyimagedl` 库
- **自动元数据**: 保存图片元数据

### 配置选项

```bash
# 基础搜索
python scripts/union_image_search/multi_platform_image_search.py \
  --keyword "cute cats" \
  --num 50

# 指定平台
python scripts/union_image_search/multi_platform_image_search.py \
  --keyword "sunset" \
  --platforms baidu google pixabay \
  --num 30

# 自定义输出目录
python scripts/union_image_search/multi_platform_image_search.py \
  --keyword "flowers" \
  --output ./my_images \
  --num 100

# 调整并发和延迟
python scripts/union_image_search/multi_platform_image_search.py \
  --keyword "cats" \
  --num 50 \
  --threads 3 \
  --delay 2.0
```

### 性能优化

#### 保守配置（避免被封）
```bash
--threads 3 --delay 2.0
```

#### 激进配置（速度优先）
```bash
--threads 10 --delay 0.5
```

### 注意事项

1. **反爬虫机制**: 各平台有不同的反爬虫机制
2. **并发控制**: 使用 `--threads` 控制并发数
3. **请求间隔**: 使用 `--delay` 设置间隔
4. **分批下载**: 避免单次下载过多图片

---

## 通用最佳实践

### 1. 合理使用参数

- 使用 `--limit` 控制结果数量
- 使用精确的搜索关键词
- 应用适当的过滤条件

### 2. 监控 API 使用

- 定期检查配额使用情况
- 记录每次请求的消耗
- 设置告警阈值

### 3. 实现缓存机制

- 使用 `--save-raw` 保存原始响应
- 避免重复请求相同内容
- 实现本地缓存

### 4. 错误处理

- 捕获异常并记录日志
- 实现自动重试机制
- 使用指数退避策略

### 5. 保持凭据安全

- 不要提交 .env 到 Git
- 定期轮换 API Key
- 使用最小权限原则

---

## 平台对比

| 平台 | 需要 API | 速率限制 | 主要用途 |
|------|---------|---------|---------|
| GitHub | 推荐 | 30 次/分钟 | 代码搜索 |
| Reddit | 否 | 隐性限制 | 社区讨论 |
| 小红书 | 是 | TikHub 限制 | 生活分享 |
| 抖音 | 是 | TikHub 限制 | 短视频 |
| Bilibili | 可选 | 视情况而定 | 视频内容 |
| 微博 | Cookie | 隐性限制 | 社交媒体 |
| YouTube | 是 | 10,000 单位/天 | 视频搜索 |
| 图片搜索 | 否 | 隐性限制 | 图片下载 |

---

## 总结

每个平台都有其特定的限制和最佳实践：

1. **了解限制**: 熟悉各平台的速率限制和配额
2. **选择合适的工具**: 根据需求选择合适的搜索平台
3. **合理配置**: 使用适当的参数和过滤条件
4. **监控使用**: 定期检查 API 使用情况
5. **保持更新**: 关注平台 API 的变化

更多详细信息，请参考：
- `references/api_credentials.md` - API 凭据获取
- `references/rate_limits.md` - 速率限制详情
- `references/troubleshooting.md` - 问题排查指南
