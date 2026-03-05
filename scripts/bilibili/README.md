# Bilibili 搜索模块 (TikHub API)

## 概述

本模块使用 TikHub API 进行 Bilibili 视频搜索，是 Bilibili 搜索的唯一官方接口。

## 依赖

- Python 3.8+
- 标准库（无需额外安装包）

## 配置

### 1. 获取 API Token

访问 [TikHub](https://www.tikhub.io/) 注册账号并获取 API Token。

### 2. 配置环境变量

在项目根目录的 `.env` 文件中添加：

```bash
TIKHUB_TOKEN=your_token_here
```

或者直接在命令行中设置：

```bash
export TIKHUB_TOKEN="your_token_here"
```

## 使用方法

### 命令行调用

```bash
# 基本搜索
python scripts/bilibili/tikhub_search.py "Python教程"

# 指定返回数量
python scripts/bilibili/tikhub_search.py "Python教程" --limit 5

# 指定排序方式 (totalrank, click, pubdate, danmaku)
python scripts/bilibili/tikhub_search.py "Python教程" --order pubdate

# JSON 输出
python scripts/bilibili/tikhub_search.py "Python教程" --json

# 美化 JSON 输出
python scripts/bilibili/tikhub_search.py "Python教程" --json --pretty

# 保存到文件
python scripts/bilibili/tikhub_search.py "Python教程" -o results.json

# 组合使用
python scripts/bilibili/tikhub_search.py "Python教程" -l 10 --json --pretty -o results.json
```

### 参数说明

| 参数 | 简写 | 默认值 | 说明 |
|------|------|--------|------|
| keyword | - | (必填) | 搜索关键词 |
| --limit | -l | 10 | 返回结果数量 |
| --order | -o | totalrank | 排序方式 |
| --json | - | false | JSON 格式输出 |
| --pretty | - | false | 美化 JSON 格式 |
| --output | -f | - | 保存到文件 |

### 排序方式

- `totalrank`: 综合排序（默认）
- `click`: 点击量排序
- `pubdate`: 发布日期排序
- `danmaku`: 弹幕数排序

### Python 代码调用

```python
import sys
from pathlib import Path

# 添加路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from bilibili.tikhub_search import search_bilibili

# 搜索视频
results = search_bilibili("Python教程", limit=10)

# 遍历结果
for video in results:
    print(f"标题: {video['title']}")
    print(f"作者: {video['author']}")
    print(f"播放: {video['play']}")
    print(f"链接: {video['arcurl']}")
    print("---")
```

## 输出格式

### JSON 格式

```json
[
  {
    "bvid": "BV1rpWjevEip",
    "title": "视频标题",
    "author": "UP主",
    "mid": 123456789,
    "aid": 113006243481679,
    "arcurl": "https://www.bilibili.com/video/BV1rpWjevEip",
    "description": "视频简介",
    "pic": "//i2.hdslb.com/bfs/...",
    "play": 14781161,
    "duration": "2398:14",
    "favorites": 576612,
    "like": 354513,
    "pubdate": 1724338758,
    "tag": "标签1,标签2,标签3"
  }
]
```

### 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| bvid | string | B站视频BV号 |
| title | string | 视频标题 |
| author | string | UP主名称 |
| mid | int | UP主MID |
| aid | int | 视频AV号 |
| arcurl | string | 视频链接 |
| description | string | 视频简介 |
| pic | string | 封面图片URL |
| play | int | 播放量 |
| duration | string | 时长 (格式: HH:MM:SS) |
| favorites | int | 收藏数 |
| like | int | 点赞数 |
| pubdate | int | 发布时间 (Unix时间戳) |
| tag | string | 标签 (逗号分隔) |

## 在 Union Search 中使用

```bash
# 在统一搜索中使用 Bilibili
python scripts/union_search/union_search.py "Python教程" --platforms bilibili volcengine google
```

## 故障排除

### 错误: 未找到 TIKHUB_TOKEN

解决方法：确保 `.env` 文件中已配置 `TIKHUB_TOKEN`，或者在运行前设置环境变量。

### HTTP 412 错误

这是 Bilibili API 的限流/封禁措施，属于正常现象。建议：
1. 降低请求频率
2. 更换 TikHub 账号
3. 等待一段时间后重试

### 网络连接问题

如果在中国大陆访问 `api.tikhub.io` 失败，脚本会自动切换到 `api.tikhub.dev`。

## API 文档

- [TikHub 官网](https://www.tikhub.io/)
- [TikHub API 文档](https://docs.tikhub.io/)
- [TikHub Swagger UI](https://api.tikhub.io/)
