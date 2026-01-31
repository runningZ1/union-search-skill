# Bilibili 搜索工具

本目录包含两个 Bilibili 搜索脚本，分别使用不同的 API：

## 1. TikHub API 搜索 (`tikhub_bili_search.py`)

基于 TikHub API 的简单搜索工具。

**特点**:
- 使用 TikHub API
- 需要 API Token
- 返回原始 JSON 数据
- 轻量级，无额外依赖

**安装**:
```bash
# 无需额外依赖，使用标准库
```

**使用**:
```bash
# 基础搜索
python tikhub_bili_search.py "原神" --page 1 --page-size 20

# 使用环境变量
export TIKHUB_TOKEN="your_token"
python tikhub_bili_search.py --keyword "Python教程"
```

---

## 2. Bilibili API 高级搜索 (`bilibili_api_search.py`)

基于官方 bilibili-api 库的高级搜索工具，功能更强大。

**特点**:
- 使用官方 bilibili-api 库
- 无需 API Token
- 获取详细视频信息（互动数据、UP主信息、标签等）
- 支持多种输出格式（文本、JSON、Markdown）
- 自动按播放量排序
- 支持多种排序方式

**安装**:
```bash
pip install bilibili-api-python aiohttp
```

**使用示例**:

```bash
# 基础搜索（默认返回10个结果）
python bilibili_api_search.py "Python教程"

# 指定结果数量
python bilibili_api_search.py "原神" --limit 5

# 按播放量排序
python bilibili_api_search.py "机器学习" --order click --limit 10

# 按发布时间排序
python bilibili_api_search.py "AI" --order pubdate --limit 10

# JSON 格式输出
python bilibili_api_search.py "编程" --json --pretty

# Markdown 格式输出并保存
python bilibili_api_search.py "教程" --markdown -o results.md

# 只获取基础信息（不获取详细数据，更快）
python bilibili_api_search.py "游戏" --no-details --limit 20

# 保存原始响应
python bilibili_api_search.py "音乐" --save-raw
```

**排序方式**:
- `totalrank` - 综合排序（默认）
- `click` - 按播放量
- `pubdate` - 按发布时间
- `dm` - 按弹幕数
- `stow` - 按收藏数

**输出信息**:

基础信息：
- 标题、BVID、作者、UP主ID
- 时长、发布时间、视频链接

详细信息（使用 `--no-details` 可跳过）：
- 互动数据：播放量、弹幕、点赞、投币、收藏、转发、评论
- 视频信息：AV号、分区、版权、简介
- UP主信息：昵称、UID、头像
- 视频标签

**测试**:
```bash
# 运行测试脚本
python test_bilibili_api.py
```

---

## 选择建议

- **需要简单快速的搜索** → 使用 `tikhub_bili_search.py`
- **需要详细的视频信息和互动数据** → 使用 `bilibili_api_search.py`
- **需要生成报告或分析数据** → 使用 `bilibili_api_search.py`

---

## 目录结构

```
bilibili/
├── tikhub_bili_search.py      # TikHub API 搜索
├── bilibili_api_search.py     # Bilibili API 高级搜索
├── test_bilibili_api.py       # 测试脚本
├── README.md                  # 本文件
└── responses/                 # 原始响应保存目录
```

---

## 注意事项

1. **请求频率**: 避免高频请求，建议添加延迟
2. **合法使用**: 仅用于学习和研究目的
3. **数据时效**: 播放量等数据为实时获取
4. **错误处理**: 脚本已内置完善的错误处理

---

## 相关链接

- [bilibili-api 官方文档](https://nemo2011.github.io/bilibili-api)
- [bilibili-api GitHub](https://github.com/Nemo2011/bilibili-api)
- [TikHub API 文档](https://api.tikhub.io)
