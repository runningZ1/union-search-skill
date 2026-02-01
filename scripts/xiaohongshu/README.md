# 小红书搜索

使用 TikHub API 搜索小红书笔记，支持过滤和排序功能。

## 功能特性

- ✅ 按关键词搜索小红书笔记
- ✅ 按时间范围、内容类型（图片/视频）过滤
- ✅ 按点赞、评论、收藏排序
- ✅ 提取话题标签（# 前缀标签）
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
# 搜索笔记
python scripts/xiaohongshu/tikhub_xhs_search.py "美食" --limit 10

# 按点赞排序
python scripts/xiaohongshu/tikhub_xhs_search.py "旅游" --sort-by liked_count --sort-order desc --limit 20
```

### 过滤搜索

```bash
# 按内容类型过滤
python scripts/xiaohongshu/tikhub_xhs_search.py "穿搭" --filter-note-type 视频 --limit 10

# 按时间过滤
python scripts/xiaohongshu/tikhub_xhs_search.py "美妆" --filter-note-time 一周内 --limit 15
```

### 输出格式

```bash
# JSON 输出
python scripts/xiaohongshu/tikhub_xhs_search.py "健身" --pretty
```

## 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `keyword` | 搜索关键词（必需） | - |
| `--token` | TikHub API Token | 从 .env 读取 |
| `--page` | 页码 | 1 |
| `--sort-type` | 排序类型 | general |
| `--filter-note-type` | 笔记类型（不限/视频/图片） | 不限 |
| `--filter-note-time` | 时间范围（不限/一天内/一周内/半年内） | 不限 |
| `--limit` | 最大结果数 | 全部 |
| `--sort-by` | 排序字段（liked_count/collected_count/comments_count） | - |
| `--sort-order` | 排序顺序（asc/desc） | desc |
| `--pretty` | 格式化 JSON 输出 | False |

## 输出信息

- 笔记 ID、标题、内容
- 作者信息
- 笔记类型（图片/视频）
- 互动指标：点赞数、评论数、收藏数、分享数
- 话题标签（# 前缀）

## 注意事项

1. **API 配额**：TikHub API 有请求限制，查看定价页面
2. **标签提取**：仅提取带 `#` 前缀的话题标签
3. **内容类型**：视频笔记可能包含封面图片

## 相关链接

- [TikHub API 文档](https://api.tikhub.io/docs)
