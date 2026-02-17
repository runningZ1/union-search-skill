# 小宇宙FM播客搜索

通过秘塔AI搜索API搜索小宇宙FM的播客内容。

## 功能特性

- ✅ 关键词搜索小宇宙FM播客
- ✅ 获取播客标题、摘要、主播、时长等元数据
- ✅ 支持AI生成摘要
- ✅ 多种输出格式（文本/JSON）
- ✅ 相关度评分

## 安装依赖

```bash
pip install python-dotenv
```

## 配置

在项目根目录的 `.env` 文件中添加秘塔搜索API密钥：

```bash
METASO_API_KEY=your_metaso_api_key_here
```

获取API密钥：https://metaso.cn

## 使用方法

### 基础搜索

```bash
python scripts/xiaoyuzhoufm/xiaoyuzhou_search.py "人工智能"
```

### 限制结果数量

```bash
python scripts/xiaoyuzhoufm/xiaoyuzhou_search.py "创业故事" --size 5
```

### JSON格式输出

```bash
python scripts/xiaoyuzhoufm/xiaoyuzhou_search.py "心理学" --json
```

### 包含AI摘要

```bash
python scripts/xiaoyuzhoufm/xiaoyuzhou_search.py "投资理财" --summary
```

### 简洁摘要

```bash
python scripts/xiaoyuzhoufm/xiaoyuzhou_search.py "科技" --concise
```

## 命令行参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `query` | 搜索关键词（必需） | - |
| `--size`, `-s` | 返回结果数量 | 10 |
| `--json`, `-j` | JSON格式输出 | False |
| `--summary` | 包含AI摘要 | False |
| `--concise`, `-c` | 使用简洁摘要 | False |

## 搜索结果说明

每个播客结果包含：

- **title**: 单集标题
- **link**: 小宇宙FM链接
- **snippet**: AI生成的内容摘要
- **authors**: 主播列表
- **date**: 发布日期
- **duration**: 时长（秒）
- **score**: 相关度评分（high/medium/low）

## 在代码中调用

```python
from scripts.xiaoyuzhoufm.xiaoyuzhou_search import search_and_format

# 文本格式输出
result = search_and_format("人工智能", size=5)
print(result)

# JSON格式输出
result = search_and_format("创业故事", output_format="json")
```

## 注意事项

1. **API配额**: 秘塔AI搜索API按次计费，请注意使用量
2. **速率限制**: 建议控制请求频率，避免过于频繁的调用
3. **密钥安全**: 不要在代码中硬编码API密钥，使用环境变量

## 示例输出

```
# 搜索结果: "人工智能"
共找到 42 个相关播客
本次搜索消耗积分: 1

==================================================

## AI时代的机遇与挑战
- **主播**: 张三, 李四
- **发布日期**: 2024-02-15
- **时长**: 45分30秒
- **相关度**: high
- **链接**: https://www.xiaoyuzhoufm.com/episode/xxx

本期节目探讨了人工智能技术的最新发展...
---
```
