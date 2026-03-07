# URL to Markdown

将网页URL转换为LLM友好的Markdown内容。基于 [Jina AI Reader API](https://jina.ai/reader) 实现。

## 功能特性

- 将任意URL转换为Markdown格式
- 支持图片alt文本自动生成
- 支持CSS选择器提取特定内容
- 支持等待JavaScript渲染
- 支持批量处理
- 免费的HTTP API，无需API Key

## 安装依赖

```bash
pip install requests python-dotenv
```

## 使用方法

### 命令行

```bash
# 基本用法
python -m scripts.url_to_markdown "https://example.com"

# JSON格式输出
python -m scripts.url_to_markdown "https://example.com" --json

# 包含图片摘要
python -m scripts.url_to_markdown "https://example.com" --with-images

# 生成图片alt文本 (较慢)
python -m scripts.url_to_markdown "https://example.com" --with-generated-alt

# 指定CSS选择器提取内容
python -m scripts.url_to_markdown "https://example.com" --target-selector "article"

# 保存响应到文件
python -m scripts.url_to_markdown "https://example.com" --save-response

# 完整参数示例
python -m scripts.url_to_markdown "https://github.com" \
    --with-images \
    --with-links \
    --timeout 60 \
    --save-response \
    --verbose
```

### Python API

```python
from scripts.url_to_markdown import UrlToMarkdown, fetch_url_as_markdown

# 简单调用
result = fetch_url_as_markdown("https://example.com")
print(result)

# 高级用法
client = UrlToMarkdown()
result = client.fetch(
    url="https://example.com",
    with_images=True,
    with_generated_alt=False,
    timeout=30,
)
print(result["content"])
```

## API参数

| 参数 | 说明 |
|------|------|
| `url` | 要抓取的URL |
| `with_images` | 是否包含图片摘要 |
| `with_links` | 是否包含链接摘要 |
| `with_generated_alt` | 是否生成图片alt文本 (需要VLM，较慢) |
| `target_selector` | CSS选择器，指定要提取的内容区域 |
| `wait_for_selector` | 等待指定元素渲染完成 |
| `timeout` | 请求超时时间(秒) |
| `no_cache` | 是否绕过缓存 |

## 直接调用API

无需API Key，直接HTTP调用：

```bash
# 简单调用
curl https://r.jina.ai/https://example.com

# 生成图片alt
curl -H "X-With-Generated-Alt: true" https://r.jina.ai/https://example.com

# 指定提取区域
curl -H "X-Target-Selector: article" https://r.jina.ai/https://example.com
```

## 响应格式

```json
{
  "url": "https://example.com",
  "title": "Example Domain",
  "content": "# Example Domain\n\nThis domain is for use...",
  "markdown": "# Example Domain\n\nThis domain is for use..."
}
```

## 注意事项

### 速率限制

Jina Reader API 的使用限制如下：

| 使用方式 | 速率限制 | 说明 |
|---------|---------|------|
| 无需API Key | **20 RPM** | 每分钟20次请求，适合个人使用 |
| 免费API Key | 500 RPM | 注册账号后可获取 |
| 付费API Key | 500 RPM | 付费版本 |
| 高级API Key | 5000 RPM | 企业版本 |

**关于免费使用的说明**：
- 完全免费，无需注册即可使用
- 每分钟最多 20 次请求（每3秒1次）
- 按输出token数计费（免费版有额度）
- 超过限制会返回429错误，代码已内置重试机制

### 其他注意事项

1. 部分JavaScript渲染的页面可能需要更长处理时间
2. 建议设置合理的超时时间
3. 大规模使用建议注册获取API Key提升限额

## 相关链接

- [Jina AI Reader](https://jina.ai/reader)
- [Reader API 文档](https://jina.ai/reader#apiform)
- [union-search-skill 主项目](../union_search/)
