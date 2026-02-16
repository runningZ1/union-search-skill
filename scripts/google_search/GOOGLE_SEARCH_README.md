# Google Custom Search

使用 Google Custom Search API 进行网络搜索和图片搜索。

## 功能特性

- ✅ 网络搜索，支持自定义结果数量
- ✅ 图片搜索，支持尺寸过滤
- ✅ 语言特定搜索
- ✅ 多种输出格式（文本、JSON）
- ✅ 清晰的终端格式化输出

## 安装

```bash
pip install requests python-dotenv
```

## 配置

### 获取 API 凭据

1. 访问 [Google Cloud Console](https://console.cloud.google.com/apis/credentials) 获取 API Key
2. 访问 [Programmable Search Engine](https://programmablesearchengine.google.com/) 创建自定义搜索引擎
3. 在项目根目录的 `.env` 文件中添加：
   ```bash
   GOOGLE_API_KEY=your_api_key
   GOOGLE_SEARCH_ENGINE_ID=your_search_engine_id
   ```

## 使用示例

### 基础搜索

```bash
# 网络搜索
python scripts/google_search/google_search.py "Python tutorial" -n 5

# 中文搜索
python scripts/google_search/google_search.py "人工智能" --lang zh-CN -n 10
```

### 图片搜索

```bash
# 基础图片搜索
python scripts/google_search/google_search.py "sunset" --image -n 10

# 带尺寸过滤
python scripts/google_search/google_search.py "wallpaper" --image --img-size large
```

### 输出格式

```bash
# JSON 输出
python scripts/google_search/google_search.py "Claude AI" --json --pretty
```

## 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `query` | 搜索关键词（必需） | - |
| `-n, --num` | 结果数量（1-10） | 10 |
| `--lang` | 语言代码（如 zh-CN, en） | - |
| `--image` | 启用图片搜索 | False |
| `--img-size` | 图片尺寸（icon/small/medium/large/xlarge/xxlarge/huge） | - |
| `--json` | JSON 格式输出 | False |
| `--pretty` | 格式化 JSON 输出 | False |

## 输出信息

- 结果总数和搜索时间
- 每个结果的标题、链接和摘要
- 图片搜索：图片尺寸和缩略图链接

## 注意事项

1. **API 配额限制**：免费套餐每天 100 次查询
2. **结果数量**：单次查询最多返回 10 个结果
3. **自定义搜索引擎**：需要配置搜索范围（整个网络或特定网站）

## 高级搜索技巧

查看 [Google 搜索高级指令速查](./GOOGLE_SEARCH_GUIDE.md) 了解如何使用高级搜索运算符提升搜索效率。

## 相关链接

- [Google Custom Search API 文档](https://developers.google.com/custom-search/v1/overview)
- [API 配额说明](https://developers.google.com/custom-search/v1/overview#pricing)
