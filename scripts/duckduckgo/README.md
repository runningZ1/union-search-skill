# DuckDuckGo 搜索模块

使用 DuckDuckGo HTML 版本进行网络搜索。

## 特点

- 无需 API 密钥
- 支持分页
- 支持时间过滤
- 支持地区设置
- 隐私友好

## 使用方法

### 基本搜索

```bash
python scripts/duckduckgo/duckduckgo_search.py "Python programming"
```

### 高级选项

```bash
# 指定页码和结果数
python scripts/duckduckgo/duckduckgo_search.py "AI research" -p 2 -m 20

# 时间过滤
python scripts/duckduckgo/duckduckgo_search.py "news" -t d  # 最近一天

# 地区设置
python scripts/duckduckgo/duckduckgo_search.py "restaurants" -r us-en

# JSON 输出
python scripts/duckduckgo/duckduckgo_search.py "data science" --json --pretty

# 使用代理
python scripts/duckduckgo/duckduckgo_search.py "search query" --proxy http://127.0.0.1:7890
```

## 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `query` | 搜索关键词（必需） | - |
| `-p, --page` | 页码 | 1 |
| `-m, --max-results` | 最大结果数 | 10 |
| `-r, --region` | 地区代码 | wt-wt (全球) |
| `-t, --timelimit` | 时间限制 (d/w/m/y) | 无 |
| `--proxy` | 代理地址 | 无 |
| `--json` | JSON 格式输出 | False |
| `--pretty` | 格式化 JSON | False |

## 环境变量

```bash
# .env 文件（可选）
DUCKDUCKGO_PROXY=http://127.0.0.1:7890
```

## 地区代码

- `wt-wt` - 全球
- `us-en` - 美国英语
- `uk-en` - 英国英语
- `cn-zh` - 中国中文

## 时间限制

- `d` - 最近一天
- `w` - 最近一周
- `m` - 最近一月
- `y` - 最近一年

## 依赖

```bash
pip install requests lxml python-dotenv
```
