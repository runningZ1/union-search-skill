# 抖音搜索

使用 TikHub API 搜索抖音视频，支持全面的过滤选项。

## 功能特性

- ✅ 按关键词搜索抖音视频
- ✅ 按发布时间、时长、内容类型过滤
- ✅ 按互动指标排序
- ✅ 支持游标分页
- ✅ 提取话题标签
- ✅ 多种输出格式（文本、JSON）

## 安装

无需额外依赖，仅使用 Python 标准库。

## 配置

### 获取 TikHub API Token

1. 访问 [TikHub.io](https://tikhub.io) 注册账号
2. 获取 API Token
3. 在项目根目录的 `.env` 文件中添加：
   ```bash
   TIKHUB_TOKEN=your_token_here
   ```

## 使用示例

### 基础搜索

```bash
# 搜索视频
python scripts/douyin/tikhub_douyin_search.py "美食" --limit 10

# 使用游标分页
python scripts/douyin/tikhub_douyin_search.py "旅游" --cursor 10 --limit 20
```

### 过滤搜索

```bash
# 按发布时间过滤
python scripts/douyin/tikhub_douyin_search.py "音乐" --publish-time 1 --limit 10

# 按时长过滤
python scripts/douyin/tikhub_douyin_search.py "教程" --filter-duration 1 --limit 15
```

### 排序搜索

```bash
# 按排序类型
python scripts/douyin/tikhub_douyin_search.py "舞蹈" --sort-type 1 --limit 20
```

### 输出格式

```bash
# JSON 输出
python scripts/douyin/tikhub_douyin_search.py "搞笑" --pretty
```

## 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `keyword` | 搜索关键词（必需） | - |
| `--token` | TikHub API Token | 从 .env 读取 |
| `--cursor` | 游标位置（分页） | 0 |
| `--sort-type` | 排序类型（0=综合，1=最新，2=最热） | 0 |
| `--publish-time` | 发布时间（0=不限，1=一天内，7=一周内，182=半年内） | 0 |
| `--filter-duration` | 时长过滤（0=不限，1=1分钟内，2=1-5分钟，3=5分钟以上） | 0 |
| `--content-type` | 内容类型（0=综合，1=视频，2=图文） | 0 |
| `--search-id` | 搜索 ID（保持结果一致性） | - |
| `--backtrace` | 回溯参数 | - |
| `--limit` | 最大结果数 | 全部 |
| `--pretty` | 格式化 JSON 输出 | False |

## 输出信息

- 视频 ID、标题、描述
- 作者信息
- 视频时长、封面
- 互动指标：点赞数、评论数、分享数、播放量
- 话题标签（# 前缀）
- 发布时间

## 注意事项

1. **API 配额**：TikHub API 有请求限制，查看定价页面
2. **游标分页**：使用 `--cursor` 参数获取更多结果
3. **搜索 ID**：使用相同的 `search-id` 可保持搜索结果一致性
4. **标签提取**：自动提取视频描述中的话题标签

## 相关链接

- [TikHub API 文档](https://api.tikhub.io/docs)
