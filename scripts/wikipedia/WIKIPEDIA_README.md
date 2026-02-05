# Wikipedia 搜索模块

使用 Wikipedia API 进行搜索和内容提取。

## 特点

- 无需 API 密钥
- 支持多语言
- 自动获取文章摘要
- 过滤消歧义页面

## 使用方法

### 基本搜索

```bash
python scripts/wikipedia/wikipedia_search.py "Albert Einstein"
```

### 高级选项

```bash
# 中文搜索
python scripts/wikipedia/wikipedia_search.py "人工智能" -l zh

# 指定结果数
python scripts/wikipedia/wikipedia_search.py "Python programming" -m 5

# JSON 输出
python scripts/wikipedia/wikipedia_search.py "Machine learning" --json --pretty

# 使用代理
python scripts/wikipedia/wikipedia_search.py "search query" --proxy http://127.0.0.1:7890
```

## 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `query` | 搜索关键词（必需） | - |
| `-l, --lang` | 语言代码 | en |
| `-m, --max-results` | 最大结果数 | 10 |
| `--proxy` | 代理地址 | 无 |
| `--json` | JSON 格式输出 | False |
| `--pretty` | 格式化 JSON | False |

## 环境变量

```bash
# .env 文件（可选）
WIKIPEDIA_PROXY=http://127.0.0.1:7890
```

## 语言代码

- `en` - 英语
- `zh` - 中文
- `es` - 西班牙语
- `fr` - 法语
- `de` - 德语
- `ja` - 日语
- `ru` - 俄语
- `ar` - 阿拉伯语

## 技术细节

- 使用 Wikipedia OpenSearch API
- 自动获取文章详细摘要
- 过滤 "may refer to:" 消歧义页面
- 摘要限制在 500 字符以内

## 依赖

```bash
pip install requests python-dotenv
```
