# Bilibili API 搜索 - 快速入门

## 安装

```bash
pip install bilibili-api-python aiohttp
```

## 基础使用

### 1. 简单搜索

```bash
python scripts/bilibili/bilibili_api_search.py "Python教程"
```

输出示例：
```
================================================================================
🔍 搜索关键词: Python教程
📊 结果数量: 10
================================================================================

================================================================================
📹 视频 #1
================================================================================

【基础信息】
标题: Python入门教程完整版
BVID: BV1xxxxxxxxx
作者: 某UP主
UP主ID: 123456
时长: 1:23:45
发布时间: 2024-01-01
视频链接: https://www.bilibili.com/video/BV1xxxxxxxxx

【互动数据】
▶️  播放量: 1,234,567
💬 弹幕数: 12,345
💖 点赞数: 98,765
🪙 投币数: 12,345
⭐ 收藏数: 45,678
🔄 转发数: 1,234
💭 评论数: 5,678

【视频信息】
AV号: av123456789
分区: 科技
版权: 原创
简介: 这是一个Python入门教程...

【视频标签】
标签: Python, 编程, 教程, 入门
```

### 2. 指定结果数量

```bash
python scripts/bilibili/bilibili_api_search.py "原神" --limit 5
```

### 3. 按播放量排序

```bash
python scripts/bilibili/bilibili_api_search.py "机器学习" --order click --limit 10
```

### 4. JSON 输出

```bash
python scripts/bilibili/bilibili_api_search.py "编程" --json --pretty
```

### 5. Markdown 输出

```bash
python scripts/bilibili/bilibili_api_search.py "教程" --markdown -o results.md
```

### 6. 快速搜索（不获取详细信息）

```bash
python scripts/bilibili/bilibili_api_search.py "游戏" --no-details --limit 20
```

## 排序选项

| 选项 | 说明 |
|------|------|
| `totalrank` | 综合排序（默认） |
| `click` | 按播放量 |
| `pubdate` | 按发布时间 |
| `dm` | 按弹幕数 |
| `stow` | 按收藏数 |

## 输出格式

| 格式 | 参数 | 说明 |
|------|------|------|
| 文本 | 默认 | 格式化的终端输出 |
| JSON | `--json` | JSON 格式，可用 `--pretty` 格式化 |
| Markdown | `--markdown` | Markdown 格式，适合生成报告 |

## 常见用例

### 查找热门教程

```bash
python scripts/bilibili/bilibili_api_search.py "Python教程" --order click --limit 10
```

### 查找最新视频

```bash
python scripts/bilibili/bilibili_api_search.py "AI新闻" --order pubdate --limit 10
```

### 生成分析报告

```bash
python scripts/bilibili/bilibili_api_search.py "机器学习" --markdown -o ml_report.md
```

### 批量数据收集

```bash
python scripts/bilibili/bilibili_api_search.py "编程" --json --save-raw -o data.json
```

## 测试

运行测试脚本验证安装：

```bash
python scripts/bilibili/test_bilibili_api.py
```

## 注意事项

1. **请求频率**: 脚本已内置延迟（0.3秒），避免请求过快
2. **合法使用**: 仅用于学习和研究目的
3. **数据时效**: 播放量等数据为实时获取
4. **详细信息**: 获取详细信息会增加请求时间，可使用 `--no-details` 跳过

## 故障排除

### 问题：未安装 bilibili-api 库

```bash
pip install bilibili-api-python aiohttp
```

### 问题：请求过快被限制

使用 `--no-details` 参数或减少 `--limit` 数量。

### 问题：搜索无结果

尝试更换关键词或排序方式。

## 更多信息

- [bilibili-api 官方文档](https://nemo2011.github.io/bilibili-api)
- [完整 README](README.md)
