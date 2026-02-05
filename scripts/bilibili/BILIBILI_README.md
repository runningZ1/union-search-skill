# B站工具集

基于 `bilibili-api` 的B站数据获取工具包。

## 核心脚本

### 搜索模块

| 脚本 | 功能 | 方法 |
|------|------|------|
| `video_search.py` | 视频搜索 | `search(keyword, page_size, get_details)` |
| `user_search.py` | 用户搜索 | `search(keyword, page_size)` |
| `hot_search.py` | 热搜榜 | `fetch(limit)` |
| `suggest_search.py` | 搜索建议 | `fetch(keyword)` |

### 内容获取模块

| 脚本 | 功能 | 需登录 |
|------|------|--------|
| `get_video_full_data.py` | 视频完整数据 | 否 |
| `get_video_comments.py` | 视频评论 | 是 |

## 快速使用

```bash
# 视频搜索
python video_search.py Python教程

# 获取视频数据
python get_video_full_data.py BV1xx411c7mD

# 获取视频评论（需配置 config.py）
python get_video_comments.py BV1xx411c7mD
```

## 依赖

```bash
pip install bilibili-api
```

## 配置

评论获取需要登录凭证，复制 `config.py.example` 为 `config.py` 并填入 SESSDATA。

## 目录结构

```
bilibili/
├── video_search.py       # 视频搜索
├── user_search.py        # 用户搜索
├── hot_search.py         # 热搜榜
├── suggest_search.py     # 搜索建议
├── get_video_full_data.py  # 视频数据
├── get_video_comments.py   # 视频评论
├── utils.py              # 工具函数
├── config.py             # 凭证配置
├── config.py.example     # 配置示例
├── requirements.txt      # 依赖
├── docs/                 # 文档归档
├── output/               # 输出目录
└── search_output/        # 搜索结果
```
