# Bing 搜索模块

使用 Bing Search 进行网络搜索。

## 特点

- 无需 API 密钥
- 支持分页
- 支持时间过滤
- 支持多语言和地区
- 自动解码 URL

## 使用方法

### 基本搜索

```bash
python scripts/bing/bing_search.py "deep learning"
```

### 高级选项

```bash
# 指定页码和结果数
python scripts/bing/bing_search.py "neural networks" -p 2 -m 15

# 时间过滤
python scripts/bing/bing_search.py "latest news" -t d  # 最近一天

# 语言和地区
python scripts/bing/bing_search.py "local search" -l zh -c cn

# JSON 输出
python scripts/bing/bing_search.py "data analysis" --json --pretty

# 使用代理
python scripts/bing/bing_search.py "search query" --proxy http://127.0.0.1:7890
```

## 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `query` | 搜索关键词（必需） | - |
| `-p, --page` | 页码 | 1 |
| `-m, --max-results` | 最大结果数 | 10 |
| `-l, --lang` | 语言代码 | en |
| `-c, --country` | 国家代码 | us |
| `-t, --timelimit` | 时间限制 (d/w/m/y) | 无 |
| `--proxy` | 代理地址 | 无 |
| `--json` | JSON 格式输出 | False |
| `--pretty` | 格式化 JSON | False |

## 环境变量

```bash
# .env 文件（可选）
BING_PROXY=http://127.0.0.1:7890
```

## 语言和国家代码

### 常用语言
- `en` - 英语
- `zh` - 中文
- `es` - 西班牙语
- `fr` - 法语
- `de` - 德语
- `ja` - 日语

### 常用国家
- `us` - 美国
- `cn` - 中国
- `uk` - 英国
- `ca` - 加拿大
- `au` - 澳大利亚
- `de` - 德国
- `fr` - 法国
- `jp` - 日本

## 时间限制

- `d` - 最近一天
- `w` - 最近一周
- `m` - 最近一月
- `y` - 最近一年

## 技术细节

- 自动解码 Bing 的 Base64 编码 URL
- 使用 Cookie 设置语言和地区偏好
- 每页返回约 10 条结果

## 依赖

```bash
pip install requests lxml python-dotenv
```
