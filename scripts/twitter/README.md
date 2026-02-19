# Twitter 搜索模块

使用 TikHub API 搜索 Twitter 帖子。

## 快速开始

```bash
# 基础搜索
python scripts/twitter/tikhub_twitter_search.py "关键词" --search-type Top --pretty

# 搜索并保存双文件(完整+筛选)
python scripts/twitter/tikhub_twitter_search.py "关键词" --search-type Top --save --filter
```

## 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `keyword` | 搜索关键词(必需) | - |
| `--search-type` | Top/Latest/Media/People/Lists | Top |
| `--save` | 保存响应到文件 | - |
| `--filter` | 同时保存筛选后的核心信息 | - |
| `--output-dir` | 输出目录 | scripts/twitter/responses |
| `--pretty` | 格式化 JSON 输出 | - |

## 输出文件

使用 `--save --filter` 后生成两个文件:

```
scripts/twitter/responses/
├── twitter_search_关键词_Top_时间戳_full.json   # 完整响应(~100KB)
└── twitter_search_关键词_Top_时间戳_core.json   # 核心信息(~25-30KB)
```

**筛选响应包含**:
- 推文链接、内容、发布时间
- 作者信息(用户名、名称、认证状态、粉丝数)
- 互动数据(点赞、转发、回复、引用、书签、浏览量)
- 媒体信息(图片/视频 URL 和尺寸)
- 实体信息(话题标签、链接、提及用户)

文件大小减少约 **75%**。

## 使用示例

```bash
# 搜索热门推文
python scripts/twitter/tikhub_twitter_search.py "AI" --search-type Top --save --filter

# 搜索最新推文
python scripts/twitter/tikhub_twitter_search.py "Python" --search-type Latest --save --filter

# 搜索用户
python scripts/twitter/tikhub_twitter_search.py "Elon Musk" --search-type People --save --filter

# 指定输出目录
python scripts/twitter/tikhub_twitter_search.py "关键词" --save --filter --output-dir my_results
```

## 独立筛选工具

对已有完整响应文件进行筛选:

```bash
python scripts/twitter/filter_twitter_response.py <完整响应文件.json>
```

## 配置

在项目根目录的 `.env` 文件中添加 API Token:

```bash
TIKHUB_TOKEN=your_token_here
```

获取 Token: [TikHub.io](https://tikhub.io)

## 相关文件

- `scripts/twitter/tikhub_twitter_search.py` - 主搜索脚本
- `scripts/twitter/filter_twitter_response.py` - 独立筛选工具
- `scripts/twitter/responses/` - 默认输出目录

## API 文档

[TikHub API 文档](https://api.tikhub.io/docs)
