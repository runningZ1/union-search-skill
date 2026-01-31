# 微博搜索 - 快速开始

## 5 分钟快速上手

### 步骤 1: 安装依赖

```bash
cd D:\Programs\weiboSpider
pip install -r requirements.txt
```

### 步骤 2: 获取 Cookie

1. 打开浏览器,访问 https://weibo.cn
2. 登录你的微博账号
3. 按 F12 打开开发者工具
4. 切换到 Network 标签
5. 刷新页面
6. 找到任意请求,查看 Request Headers
7. 复制 Cookie 字段的值

### 步骤 3: 运行搜索

```bash
cd C:\Users\zijie\.claude\skills\union-search-skill

# 替换 YOUR_COOKIE 为你的实际 Cookie
python scripts/weibo/weibo_search.py --user-id 1669879400 --cookie "YOUR_COOKIE"
```

## 常用命令

```bash
# 获取用户最新 20 条微博
python scripts/weibo/weibo_search.py --user-id 1669879400 --limit 20

# 只获取原创微博
python scripts/weibo/weibo_search.py --user-id 1669879400 --filter 1

# 按点赞数排序
python scripts/weibo/weibo_search.py --user-id 1669879400 --sort-by up_num --sort-order desc

# JSON 格式输出
python scripts/weibo/weibo_search.py --user-id 1669879400 --json --pretty

# 保存原始数据
python scripts/weibo/weibo_search.py --user-id 1669879400 --save-raw
```

## 使用环境变量(推荐)

1. 复制配置模板:
   ```bash
   cp scripts/weibo/.env.example scripts/weibo/.env
   ```

2. 编辑 `.env` 文件,填入你的配置:
   ```bash
   WEIBO_USER_ID=1669879400
   WEIBO_COOKIE=你的Cookie
   WEIBO_LIMIT=20
   ```

3. 直接运行(无需命令行参数):
   ```bash
   python scripts/weibo/weibo_search.py
   ```

## 获取用户 ID

方法 1: 从微博主页 URL 获取
- 访问用户主页,URL 格式: `https://weibo.com/u/1669879400`
- 数字部分就是 user_id

方法 2: 使用微博搜索
- 搜索用户昵称
- 点击用户主页
- 从 URL 中提取 user_id

详细教程: https://github.com/dataabc/weiboSpider/blob/master/docs/userid.md

## 故障排除

### 问题: 导入错误

```bash
# 确保已安装依赖
cd D:\Programs\weiboSpider
pip install -r requirements.txt
```

### 问题: Cookie 无效

Cookie 可能已过期(约 3 个月有效期),需要重新获取。

### 问题: 获取数据失败

可能原因:
- Cookie 无效或过期
- 用户 ID 不存在
- 网络连接问题
- 被微博限流(等待一段时间后重试)

## 更多帮助

- 详细文档: `scripts/weibo/README.md`
- 集成报告: `scripts/weibo/INTEGRATION_REPORT.md`
- 测试脚本: `python scripts/weibo/test_weibo_search.py`
- 获取帮助: `python scripts/weibo/weibo_search.py --help`
