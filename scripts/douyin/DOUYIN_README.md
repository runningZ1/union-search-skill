# 抖音搜索 (TikHub V3 增强版)

使用 TikHub API 搜索抖音视频，支持全面的过滤选项，并提供生产级的自动化数据筛选功能。

## 功能特性

- ✅ **精准搜索**：按关键词搜索抖音视频，支持多种过滤条件。
- ✅ **自动双输出**：每次请求同时生成 **全量原始数据** 和 **精简精选数据**。
- ✅ **生产级提取**：
  - 自动将发布时间转换为易读的 `YYYY-MM-DD HH:MM:SS` 格式。
  - 自动提取并去重描述中的话题标签（#Tag）。
  - 支持提取普通视频 (`aweme_info`) 和卡片式内容 (`aweme_list`)。
- ✅ **媒体资源全覆盖**：包含无水印播放地址、静态封面、动态封面链接。
- ✅ **全面互动数据**：包含点赞、评论、分享、转发、播放、收藏全指标。
- ✅ **纯标准库实现**：无需安装第三方依赖，开箱即用。

## 配置

### 1. 获取 TikHub API Token

1. 访问 [TikHub.io](https://tikhub.io) 注册账号并获取 Token。
2. 在项目根目录的 `.env` 文件中配置：
   ```bash
   TIKHUB_TOKEN=your_token_here
   ```

## 使用示例

### 基础搜索
```bash
# 搜索并限制输出 10 条视频
python scripts/douyin/tikhub_douyin_search.py "AI绘画" --limit 10 --pretty
```

### 过滤与分页
```bash
# 搜索一周内 (7) 的视频，按最热排序 (2)
python scripts/douyin/tikhub_douyin_search.py "美食" --publish-time 7 --sort-type 2 --limit 5
```

## 输出文件说明

每次执行后，脚本会在 `scripts/douyin/responses/` 目录下生成两个文件：

1. **原始文件** (`{timestamp}_douyin_search_v3.json`)
   - 包含 API 返回的完整原始数据，适合需要二次深度挖掘的场景。
2. **精选文件** (`{timestamp}_douyin_search_v3_filtered.json`)
   - 经过生产级逻辑清洗后的精简数据，结构扁平，适合直播间分析、数据库导入或直接展示。

### 精选文件数据结构
```json
{
  "search_keyword": "AI",
  "video_info": {
    "aweme_id": "7605821825201271931",
    "title": "#AI抱得美人归 #抖音ai创作",
    "tags": ["#抖音ai创作", "#ai抱得美人归"],
    "publish_time": "2026-02-12 11:53:13"
  },
  "interaction_data": {
    "like_count": 22523,
    "comment_count": 117,
    "share_count": 1667,
    "play_count": 0,
    "collect_count": 5381
  },
  "author_info": {
    "author_id": "1121123349574782",
    "nickname": "作者名"
  },
  "media_info": {
    "play_urls": ["无水印链接1", "无水印链接2"],
    "cover_urls": ["封面链接"],
    "dynamic_cover_urls": ["动态封面链接"]
  }
}
```

## 参数对照表

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `keyword` | 定向搜索关键词 | - |
| `--token` | API Token | 优先从 .env 读取 |
| `--limit` | 结果条数限制（受 API 返回限制） | 10 |
| `--sort-type` | 排序：0-综合, 1-最新, 2-最热 | 0 |
| `--publish-time` | 时间：0-不限, 1-一天, 7-一周, 180-半年 | 0 |
| `--cursor` | 分页游标 | 0 |
| `--pretty` | 在终端控制台美化 JSON 输出 | False |

## 开发者提示

- **Token 保护**：切勿将包含 Token 的 `.env` 文件提交到公共版本库。
- **链接有效期**：`media_info` 中的链接通常具有时效性，建议即取即用。
- **扩展性**：如需增加字段，可直接修改 `tikhub_douyin_search.py` 中的 `parse_aweme` 函数。

## 相关链接
- [TikHub API 官方文档](https://api.tikhub.io/docs)
- [Discord 技术支持](https://discord.gg/aMEAS8Xsvz)
