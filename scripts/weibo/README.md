# 微博搜索集成说明

## 概述

本目录包含微博搜索功能的集成脚本,基于 [weiboSpider](https://github.com/dataabc/weiboSpider) 项目实现。

## 功能特性

- 获取微博用户信息(昵称、性别、地区、粉丝数等)
- 获取用户微博内容(正文、图片、视频、互动数据)
- 支持筛选原创微博或包含转发
- 支持时间范围过滤
- 支持按点赞、转发、评论数排序
- 支持批量查询多个用户
- 多种输出格式(文本、JSON)
- 自动保存原始响应

## 安装依赖

```bash
# 安装 weiboSpider 项目依赖
cd D:\Programs\weiboSpider
pip install -r requirements.txt
```

## 获取 Cookie

微博搜索需要 Cookie 进行身份验证。获取方法:

1. 打开浏览器,访问 https://weibo.cn
2. 登录你的微博账号
3. 按 F12 打开开发者工具
4. 切换到 Network 标签
5. 刷新页面
6. 找到任意请求,查看 Request Headers
7. 复制 Cookie 字段的值

详细说明: https://github.com/dataabc/weiboSpider/blob/master/docs/cookie.md

## 使用方法

### 基本用法

```bash
# 搜索单个用户
python scripts/weibo/weibo_search.py --user-id 1669879400 --cookie "YOUR_COOKIE"

# 限制结果数量
python scripts/weibo/weibo_search.py --user-id 1669879400 --limit 20

# 只获取原创微博
python scripts/weibo/weibo_search.py --user-id 1669879400 --filter 1
```

### 高级用法

```bash
# 搜索多个用户
python scripts/weibo/weibo_search.py --user-id 1669879400,1223178222

# 指定时间范围
python scripts/weibo/weibo_search.py --user-id 1669879400 --since-date 2025-01-01 --end-date now

# 按点赞数排序
python scripts/weibo/weibo_search.py --user-id 1669879400 --sort-by up_num --sort-order desc

# JSON 输出
python scripts/weibo/weibo_search.py --user-id 1669879400 --json --pretty

# 保存原始响应
python scripts/weibo/weibo_search.py --user-id 1669879400 --save-raw
```

### 使用配置文件

```bash
# 使用 weiboSpider 的配置文件
python scripts/weibo/weibo_search.py --config-path D:\Programs\weiboSpider\config.json
```

### 使用环境变量

创建 `.env` 文件:

```bash
WEIBO_USER_ID=1669879400
WEIBO_COOKIE=YOUR_COOKIE_HERE
WEIBO_FILTER=0
WEIBO_SINCE_DATE=2025-01-01
WEIBO_END_DATE=now
WEIBO_LIMIT=10
```

然后直接运行:

```bash
python scripts/weibo/weibo_search.py
```

## 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--user-id` | 微博用户ID,多个用逗号分隔 | 必需 |
| `--cookie` | 微博 Cookie | 必需 |
| `--filter` | 0=全部微博, 1=仅原创 | 0 |
| `--since-date` | 开始日期 (YYYY-MM-DD) | 2025-01-01 |
| `--end-date` | 结束日期 (YYYY-MM-DD 或 'now') | now |
| `--limit` | 每个用户最多获取的微博数 | 10 |
| `--sort-by` | 排序字段: publish_time/up_num/retweet_num/comment_num | - |
| `--sort-order` | 排序顺序: asc/desc | desc |
| `--config-path` | weiboSpider 配置文件路径 | - |
| `--json` | JSON 格式输出 | False |
| `--pretty` | 格式化 JSON 输出 | False |
| `--save-raw` | 保存原始响应到 responses/ | False |

## 输出信息

### 用户信息
- 用户ID、昵称、性别、地区、生日
- 简介、认证信息
- 微博数、关注数、粉丝数

### 微博信息
- 微博ID、内容、发布时间、发布工具
- 发布位置(如有)
- 原始图片URL、视频URL
- 互动数据: 点赞数、转发数、评论数

## 注意事项

1. **Cookie 有效期**: Cookie 大约 3 个月过期,需要定期更新
2. **不能爬取自己**: 不能爬取用于登录的微博账号的内容
3. **速率限制**: 脚本会自动控制请求频率,避免被封禁
4. **隐私保护**: 请遵守微博服务条款,不要用于商业用途

## 故障排除

### 错误: 无法导入 weibo_spider 模块

确保 weiboSpider 项目位于正确路径:
```bash
D:\Programs\weiboSpider
```

如果路径不同,请修改 `weibo_search.py` 中的 `WEIBO_SPIDER_PATH` 变量。

### 错误: Cookie 错误或已过期

Cookie 已过期,需要重新获取。参考上面的"获取 Cookie"部分。

### 错误: 获取数据失败

可能原因:
- Cookie 无效
- 用户ID 不存在
- 网络连接问题
- 被微博限流

## 相关资源

- [weiboSpider 项目](https://github.com/dataabc/weiboSpider)
- [如何获取 Cookie](https://github.com/dataabc/weiboSpider/blob/master/docs/cookie.md)
- [如何获取 user_id](https://github.com/dataabc/weiboSpider/blob/master/docs/userid.md)
- [常见问题](https://github.com/dataabc/weiboSpider/blob/master/docs/FAQ.md)
