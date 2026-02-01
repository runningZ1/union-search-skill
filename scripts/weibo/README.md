# 微博搜索

搜索微博用户信息和帖子，基于 weiboSpider 项目

## 安装

```bash
cd D:\Programs\weiboSpider
pip install -r requirements.txt
```

## 配置

在根目录 `.env` 文件中添加：
```bash
WEIBO_USER_ID=1669879400
WEIBO_COOKIE=your_weibo_cookie_here
WEIBO_FILTER=0
WEIBO_SINCE_DATE=2025-01-01
WEIBO_END_DATE=now
WEIBO_LIMIT=10
```

获取 Cookie: https://github.com/dataabc/weiboSpider/blob/master/docs/cookie.md

## 使用示例

### 搜索单个用户
```bash
python scripts/weibo/weibo_search.py --user-id 1669879400 --cookie "YOUR_COOKIE"
```

### 带过滤器搜索
```bash
python scripts/weibo/weibo_search.py --user-id 1669879400 --filter 1 --limit 20
```

### 搜索多个用户
```bash
python scripts/weibo/weibo_search.py --user-id 1669879400,1223178222 --since-date 2025-01-01
```

### 按互动排序
```bash
python scripts/weibo/weibo_search.py --user-id 1669879400 --sort-by up_num --sort-order desc
```

## 主要参数

- `--user-id`: 微博用户 ID，逗号分隔（必需）
- `--cookie`: 微博认证 cookie（必需）
- `--filter`: 0=所有微博，1=仅原创（默认 0）
- `--since-date`: 开始日期（YYYY-MM-DD）
- `--end-date`: 结束日期（YYYY-MM-DD 或 'now'）
- `--limit`: 每个用户的最大微博数（默认 10）
- `--sort-by`: 排序字段（publish_time/up_num/retweet_num/comment_num）
- `--sort-order`: 排序顺序（asc/desc）
- `--json`, `--pretty`: 输出格式
- `--save-raw`: 保存原始响应

## 注意事项

- Cookie 约 3 个月过期，需定期更新
- 无法爬取自己的微博（用于 cookie 的账号）
- 遵守速率限制以避免被封禁
