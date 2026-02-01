# Bilibili 搜索

提供两种 Bilibili 搜索方式

## 方式 1: TikHub API 搜索（简单快速）

```bash
python scripts/bilibili/tikhub_bili_search.py "原神" --page 1 --page-size 20
```

需要在根目录 `.env` 中配置 `TIKHUB_TOKEN`

## 方式 2: Bilibili API 高级搜索（推荐）

### 安装
```bash
pip install bilibili-api-python aiohttp
```

### 使用示例

#### 基础搜索
```bash
python scripts/bilibili/bilibili_api_search.py "Python教程" --limit 10
```

#### 按播放量排序
```bash
python scripts/bilibili/bilibili_api_search.py "机器学习" --order click --limit 10
```

#### 按发布时间排序
```bash
python scripts/bilibili/bilibili_api_search.py "AI" --order pubdate --limit 10
```

#### 输出格式
```bash
python scripts/bilibili/bilibili_api_search.py "编程" --json --pretty
python scripts/bilibili/bilibili_api_search.py "教程" --markdown -o results.md
```

### 主要参数

- `--limit`: 结果数量（默认 10）
- `--order`: 排序方式
  - `totalrank` - 综合排序（默认）
  - `click` - 按播放量
  - `pubdate` - 按发布时间
  - `dm` - 按弹幕数
  - `stow` - 按收藏数
- `--json`, `--markdown`: 输出格式
- `--no-details`: 只获取基础信息（更快）
- `--save-raw`: 保存原始响应

### 输出信息

**基础信息**: 标题、BVID、作者、UP主ID、时长、发布时间、视频链接

**详细信息**（默认获取）: 播放量、弹幕、点赞、投币、收藏、转发、评论、AV号、分区、版权、简介、UP主信息、视频标签

## 选择建议

- 需要简单快速的搜索 → 使用 `tikhub_bili_search.py`
- 需要详细的视频信息和互动数据 → 使用 `bilibili_api_search.py`
