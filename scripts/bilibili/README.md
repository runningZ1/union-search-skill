# B站搜索工具包

基于 `bilibili-api` 的 B站搜索工具集，支持视频搜索、用户搜索、热搜榜和搜索建议。

## 文件说明

| 文件 | 功能 |
|------|------|
| `video_search.py` | 视频搜索 - 支持多种排序、获取详情、导出结果 |
| `user_search.py` | 用户搜索 - 按粉丝数/等级排序 |
| `hot_search.py` | 热搜榜 - 获取B站热搜数据 |
| `suggest_search.py` | 搜索建议 - 获取关键词联想词 |
| `utils.py` | 公共工具函数 |

## 依赖

```
pip install bilibili-api
```

## 快速使用

### 视频搜索

```python
import asyncio
from video_search import VideoSearcher

async def main():
    searcher = VideoSearcher()

    # 搜索视频
    await searcher.search(
        keyword="Python教程",
        page_size=10,
        get_details=False  # 是否获取详细信息
    )

    # 打印结果
    searcher.print_results()

    # 导出
    searcher.save_json()
    searcher.save_markdown()

asyncio.run(main())
```

### 命令行运行

```bash
# 视频搜索
python video_search.py Python教程

# 用户搜索
python user_search.py 教程UP主

# 热搜榜
python hot_search.py

# 搜索建议
python suggest_search.py AI
```

## 搜索结果目录

搜索结果默认保存在 `./search_output/` 目录下。
