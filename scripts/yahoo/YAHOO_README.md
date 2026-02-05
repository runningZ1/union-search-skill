# Yahoo 搜索模块

使用 Yahoo Search 进行网络搜索。

## 特点

- 无需 API 密钥
- 支持分页
- 支持时间过滤
- 自动处理 URL 重定向

## 使用方法

### 基本搜索

```bash
python scripts/yahoo/yahoo_search.py "artificial intelligence"
```

### 高级选项

```bash
# 指定页码和结果数
python scripts/yahoo/yahoo_search.py "quantum computing" -p 2 -m 15

# 时间过滤
python scripts/yahoo/yahoo_search.py "breaking news" -t d  # 最近一天

# JSON 输出
python scripts/yahoo/yahoo_search.py "cloud computing" --json --pretty

# 使用代理
python scripts/yahoo/yahoo_search.py "search query" --proxy http://127.0.0.1:7890
```

## 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `query` | 搜索关键词（必需） | - |
| `-p, --page` | 页码 | 1 |
| `-m, --max-results` | 最大结果数 | 10 |
| `-t, --timelimit` | 时间限制 (d/w/m/y) | 无 |
| `--proxy` | 代理地址 | 无 |
| `--json` | JSON 格式输出 | False |
| `--pretty` | 格式化 JSON | False |

## 环境变量

```bash
# .env 文件（可选）
YAHOO_PROXY=http://127.0.0.1:7890
```

## 时间限制

- `d` - 最近一天
- `w` - 最近一周
- `m` - 最近一月
- `y` - 最近一年

## 技术细节

- 使用动态生成的 `_ylt` 和 `_ylu` token
- 自动解码 Yahoo 的 URL 重定向（/RU= 格式）
- 每页返回约 7 条结果

## 依赖

```bash
pip install requests lxml python-dotenv
```
