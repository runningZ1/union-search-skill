# Anna's Archive 书籍搜索模块

使用 Anna's Archive 搜索电子书资源。

## 特点

- 无需 API 密钥
- 海量电子书资源
- 支持分页
- 提供书籍详细信息
- 包含封面图片

## 使用方法

### 基本搜索

```bash
python scripts/annasarchive/annasarchive_search.py "Python programming"
```

### 高级选项

```bash
# 指定页码和结果数
python scripts/annasarchive/annasarchive_search.py "machine learning" -p 2 -m 20

# JSON 输出
python scripts/annasarchive/annasarchive_search.py "data science" --json --pretty

# 使用代理
python scripts/annasarchive/annasarchive_search.py "search query" --proxy http://127.0.0.1:7890
```

## 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `query` | 搜索关键词（必需） | - |
| `-p, --page` | 页码 | 1 |
| `-m, --max-results` | 最大结果数 | 10 |
| `--proxy` | 代理地址 | 无 |
| `--json` | JSON 格式输出 | False |
| `--pretty` | 格式化 JSON | False |

## 环境变量

```bash
# .env 文件（可选）
ANNASARCHIVE_PROXY=http://127.0.0.1:7890
```

## 返回信息

每本书包含以下信息：
- **标题** (title) - 书名
- **作者** (author) - 作者名
- **出版社** (publisher) - 出版社名称
- **信息** (info) - 格式、大小、语言等
- **URL** (url) - 书籍详情页链接
- **封面** (thumbnail) - 封面图片链接

## 搜索技巧

1. **精确搜索**：使用引号包裹关键词
   ```bash
   python scripts/annasarchive/annasarchive_search.py '"Clean Code"'
   ```

2. **作者搜索**：直接输入作者名
   ```bash
   python scripts/annasarchive/annasarchive_search.py "Robert C. Martin"
   ```

3. **ISBN 搜索**：使用 ISBN 号
   ```bash
   python scripts/annasarchive/annasarchive_search.py "978-0132350884"
   ```

## 技术细节

- 自动移除 HTML 注释
- 自动补全相对 URL 为绝对 URL
- 支持多种电子书格式（PDF、EPUB、MOBI 等）

## 依赖

```bash
pip install requests lxml python-dotenv
```

## 注意事项

- Anna's Archive 是一个电子书档案网站
- 请遵守当地法律法规
- 仅用于学习和研究目的
