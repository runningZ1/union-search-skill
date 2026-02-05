# Twitter 搜索

使用 TikHub API 搜索 Twitter 帖子和时间线。

## 功能特性

- ✅ 按关键词搜索 Twitter 帖子
- ✅ 多种搜索类型（Top、Latest、Media、People、Lists）
- ✅ 支持游标分页
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
# 搜索热门推文
python scripts/twitter/tikhub_twitter_search.py "Elon Musk" --search-type Top

# 搜索最新推文
python scripts/twitter/tikhub_twitter_search.py "OpenAI" --search-type Latest
```

### 分页搜索

```bash
# 使用游标分页
python scripts/twitter/tikhub_twitter_search.py "AI" --search-type Top --cursor "<cursor_from_previous_response>"
```

### 其他搜索类型

```bash
# 搜索媒体推文
python scripts/twitter/tikhub_twitter_search.py "technology" --search-type Media

# 搜索用户
python scripts/twitter/tikhub_twitter_search.py "developer" --search-type People
```

### 输出格式

```bash
# JSON 输出
python scripts/twitter/tikhub_twitter_search.py "Python" --search-type Top --pretty
```

## 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `keyword` | 搜索关键词（必需） | - |
| `--token` | TikHub API Token | 从 .env 读取 |
| `--search-type` | 搜索类型（Top/Latest/Media/People/Lists） | Top |
| `--cursor` | 游标位置（分页） | None |
| `--pretty` | 格式化 JSON 输出 | False |

## 搜索类型说明

- **Top**：热门推文（按互动量排序）
- **Latest**：最新推文（按时间排序）
- **Media**：包含媒体（图片/视频）的推文
- **People**：搜索用户账号
- **Lists**：搜索 Twitter 列表

## 输出信息

- 推文 ID、内容、发布时间
- 作者信息（用户名、显示名称）
- 互动指标：点赞数、转发数、回复数
- 媒体内容（如果有）
- 游标信息（用于分页）

## 注意事项

1. **API 配额**：TikHub API 有请求限制，查看定价页面
2. **游标分页**：使用响应中的 `cursor` 字段获取下一页结果
3. **搜索限制**：某些搜索可能受 Twitter API 限制

## 相关链接

- [TikHub API 文档](https://api.tikhub.io/docs)
