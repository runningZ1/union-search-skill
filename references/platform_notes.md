# 平台特定说明

本文档提供各平台的特殊说明、限制和注意事项。

## 目录

- [YouTube](#youtube)
- [GitHub](#github)
- [Reddit](#reddit)
- [知乎开放平台（Zhihu）](#知乎开放平台zhihu)
- [秘塔搜索（Metaso）](#秘塔搜索metaso)
- [图片搜索](#图片搜索)

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
python scripts/github_search/github_search.py rate-limit
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
python scripts/github_search/github_search.py repo "machine learning" --language python

# 按星标过滤
python scripts/github_search/github_search.py repo "web framework" --stars ">1000"

# 按主题过滤
python scripts/github_search/github_search.py repo "test" --topic "machine-learning"
```

#### 2. 代码搜索
```bash
# 按语言搜索
python scripts/github_search/github_search.py code "async def" --language python

# 在特定仓库搜索
python scripts/github_search/github_search.py code "OAuth2" --repo "flask"

# 按文件扩展名搜索
python scripts/github_search/github_search.py code "import" --extension py
```

#### 3. Issues 搜索
```bash
# 搜索开放的 issues
python scripts/github_search/github_search.py issue "bug" --state open

# 按标签过滤
python scripts/github_search/github_search.py issue "feature" --label "help wanted"

# 搜索 Pull Requests
python scripts/github_search/github_search.py issue "update" --is-pr
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
| YouTube | 是 | 10,000 单位/天 | 视频搜索 |
| 图片搜索 | 否 | 隐性限制 | 图片下载 |

---

## 知乎开放平台（Zhihu）

使用独立的 `zhihu_official` 渠道，需配置 `ZHIHU_ACCESS_SECRET`。旧的 TikHub 知乎搜索已移除，不再使用 Cookie 配置。参数见[知乎开放平台文档](../scripts/zhihu_official/ZHIHU_OFFICIAL_SEARCH_README.md)。

## 秘塔搜索（Metaso）

### 特点

- **AI 驱动**: 提供由 AI 生成的搜索结果摘要。
- **高相关性**: 搜索结果通常经过筛选，质量较高。

### 注意事项

1. **API 稳定性**: 偶尔会出现返回 0 条结果的情况，建议使用 `--preset large` 或多次重试。
2. **积分消耗**: 每次搜索会消耗一定的 API 积分。

---

## 总结

每个平台都有其特定的限制和最佳实践：

1. **了解限制**: 熟悉各平台的速率限制和配额
2. **选择合适的工具**: 根据需求选择合适的搜索平台
3. **合理配置**: 使用适当的参数和过滤条件
4. **监控使用**: 定期检查 API 使用情况
5. **保持更新**: 关注平台 API 的变化

更多详细信息，请参考：
- `api_credentials.md` - API 凭据获取
- `rate_limits.md` - 速率限制详情
- `troubleshooting.md` - 问题排查指南
