# B 站搜索工具包

基于 `bilibili-api` 的 B 站数据获取工具集。

## 功能特性

| 模块 | 功能 | 登录要求 |
|------|------|----------|
| **视频搜索** | 搜索视频，支持多种排序、获取详情 | 否 |
| **用户搜索** | 搜索 UP 主，按粉丝数/等级排序 | 否 |
| **热搜榜** | 获取 B 站实时热搜 | 否 |
| **搜索建议** | 获取关键词联想词 | 否 |
| **视频数据** | 获取视频完整数据（统计/分 P/标签/弹幕等） | 否 |
| **视频评论** | 获取视频评论（含二级评论） | 是 |

## 快速开始

### 安装依赖

```bash
pip install bilibili-api
```

### 命令行使用

```bash
# 视频搜索
python search.py video Python 教程

# 用户搜索
python search.py user 教程 UP 主

# 热搜榜
python search.py hot

# 搜索建议
python search.py suggest AI

# 获取视频数据
python get_video_full_data.py BV1xx411c7mD

# 获取视频评论（需配置凭证）
python get_video_comments.py BV1xx411c7mD
```

### Python 导入使用

```python
import asyncio
from bilibili import VideoSearcher, UserSearcher, HotSearcher, SuggestSearcher
from bilibili import get_all_video_data, CommentFetcher

async def main():
    # 视频搜索
    searcher = VideoSearcher()
    await searcher.search("Python 教程", page_size=10)
    searcher.print_results()
    searcher.export()  # 导出 JSON 和 Markdown

    # 用户搜索
    user_searcher = UserSearcher()
    await user_searcher.search("教程 UP 主")
    user_searcher.print_results()

    # 热搜榜
    hot_searcher = HotSearcher()
    await hot_searcher.fetch(limit=30)
    hot_searcher.print_results()

    # 搜索建议
    suggest_searcher = SuggestSearcher()
    await suggest_searcher.fetch("AI")
    suggest_searcher.print_results()

    # 获取视频数据
    data = await get_all_video_data("BV1xx411c7mD")
    print(data['basic_info']['title'])

    # 获取视频评论（需要配置凭证）
    fetcher = CommentFetcher()
    await fetcher.fetch_video_comments("BV1xx411c7mD")
    fetcher.save_json()

asyncio.run(main())
```

## 配置凭证（评论功能需要）

复制 `config.py.example` 为 `config.py` 并填入 SESSDATA：

```bash
cp config.py.example config.py
```

编辑 `config.py`：

```python
SESSDATA = "你的 SESSDATA"  # 必填
```

### 如何获取 SESSDATA

1. 登录 B 站网页版 (https://www.bilibili.com)
2. 按 F12 打开开发者工具
3. 切换到 **Application** 标签
4. 找到 **Cookies** → **https://www.bilibili.com**
5. 复制 **SESSDATA** 的值

## 输出目录

- 搜索结果：`./search_output/`
- 视频数据/评论：`./output/`

## 文件结构

```
bilibili/
├── __init__.py              # 包入口
├── search.py                # 统一搜索模块（视频/用户/热搜/建议）
├── get_video_full_data.py   # 视频完整数据获取
├── get_video_comments.py    # 视频评论获取（需登录）
├── utils.py                 # 工具函数
├── config.py                # 凭证配置（忽略提交）
├── config.py.example        # 配置示例
├── requirements.txt         # 依赖列表
├── .gitignore              # Git 忽略规则
├── README.md               # 本文档
├── output/                 # 视频数据/评论输出
└── search_output/          # 搜索结果输出
```

## API 参考

### VideoSearcher

```python
searcher = VideoSearcher(output_dir="./search_output")

# 搜索视频
await searcher.search(
    keyword="Python 教程",
    order_type=search.OrderVideo.TOTALRANK,  # 排序方式
    page=1,
    page_size=20,
    get_details=False  # 是否获取详细信息
)

# 打印结果
searcher.print_results(limit=5)

# 导出
searcher.export(fmt="both")  # "json" | "md" | "both"
```

### UserSearcher

```python
searcher = UserSearcher()

await searcher.search(
    keyword="教程 UP 主",
    order_type=search.OrderUser.FANS,  # FANS=粉丝数，LEVEL=等级
    page=1,
    page_size=20
)
```

### HotSearcher

```python
searcher = HotSearcher()
await searcher.fetch(limit=30)  # 获取热搜榜
searcher.print_results()
searcher.export()
```

### SuggestSearcher

```python
searcher = SuggestSearcher()
await searcher.fetch(keyword="AI")  # 获取搜索建议
searcher.print_results()
```

### 视频数据获取

```python
from bilibili import get_all_video_data

data = await get_all_video_data("BV1xx411c7mD")
# data 包含:
# - basic_info: 基本信息
# - statistics: 统计数据
# - pages: 分 P 信息
# - tags: 标签
# - subtitles: 字幕
# - related_videos: 相关推荐
# - danmakus_sample: 弹幕样本
```

### 评论获取

```python
from bilibili import CommentFetcher

fetcher = CommentFetcher()
await fetcher.fetch_video_comments(
    bvid="BV1xx411c7mD",
    order_type=comment.OrderType.HOT,  # TIME/LIKE/HOT
    max_pages=5  # 限制页数
)
fetcher.save_json()
fetcher.save_markdown()
```

## 工具函数

```python
from bilibili.utils import clean_title, format_number, format_timestamp, print_header

clean_title("<b>标题</b>")      # "标题"
format_number(15000)           # "1.5 万"
format_number(250000000)       # "2.5 亿"
format_timestamp(1707024000)   # "2024-02-04 12:00:00"
print_header("标题")            # 打印带边框的标题
```

## 注意事项

1. **凭证安全**: 不要将 `config.py` 提交到版本控制
2. **请求频率**: API 有速率限制，建议在批量请求时添加延迟
3. **凭证过期**: SESSDATA 有过期时间，过期后需重新获取
4. **Python 版本**: 需要 Python 3.9+

## 许可证

MIT
