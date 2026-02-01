# YouTube 搜索工具

基于 YouTube Data API v3 的视频搜索工具，支持获取详细视频信息、互动数据和评论区内容。

## 功能特性

- ✅ 关键词搜索 YouTube 视频
- ✅ 多种排序方式（相关性、日期、播放量、评分）
- ✅ 获取详细视频信息（标题、频道、发布时间、时长）
- ✅ 获取互动数据（播放量、点赞数、评论数）
- ✅ 可选获取评论区内容（热门评论）
- ✅ 多种输出格式（文本、JSON、Markdown）
- ✅ 自动保存原始响应
- ✅ 无外部依赖（仅使用 Python 标准库）

## 安装

无需安装额外依赖，仅使用 Python 标准库。

## 配置

### 获取 API 密钥

1. 访问 [Google Cloud Console](https://console.cloud.google.com/)
2. 创建新项目或选择现有项目
3. 启用 YouTube Data API v3
4. 创建 API 密钥（凭据 → 创建凭据 → API 密钥）
5. 复制 API 密钥

### 配置方式

三种配置方式（优先级从高到低）：

1. **命令行参数**（推荐用于测试）
   ```bash
   python youtube_search.py "关键词" --api-key YOUR_API_KEY
   ```

2. **环境变量**（推荐用于生产）
   在项目根目录的 `.env` 文件中添加：
   ```bash
   YOUTUBE_API_KEY=YOUR_API_KEY
   ```

3. **直接在脚本中**（不推荐，安全风险）

## 使用示例

### 基础搜索

```bash
# 搜索 Python 教程
python youtube_search.py "Python tutorial" --limit 5

# 搜索中文内容
python youtube_search.py "机器学习" --limit 10
```

### 排序选项

```bash
# 按播放量排序
python youtube_search.py "AI" --order viewCount --limit 10

# 按发布日期排序
python youtube_search.py "编程" --order date --limit 10

# 按评分排序
python youtube_search.py "教程" --order rating --limit 10
```

### 包含评论

```bash
# 获取视频和评论
python youtube_search.py "Python" --include-comments --max-comments 5

# 获取更多评论
python youtube_search.py "AI" --include-comments --max-comments 20
```

### 输出格式

```bash
# JSON 格式输出
python youtube_search.py "Python" --json --pretty

# Markdown 格式输出
python youtube_search.py "AI" --markdown -o results.md

# 保存原始响应
python youtube_search.py "教程" --save-raw
```

### 地区和语言

```bash
# 指定地区和语言
python youtube_search.py "Python" --region CN --language zh-CN

# 美国地区，英文
python youtube_search.py "Python" --region US --language en
```

## 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `keyword` | 搜索关键词（必需） | - |
| `--api-key` | YouTube Data API 密钥 | 从 .env 读取 |
| `--limit` | 返回结果数量（1-50） | 10 |
| `--order` | 排序方式 | relevance |
| `--region` | 地区代码（如 US, CN） | US |
| `--language` | 语言代码（如 zh-CN, en） | zh-CN |
| `--include-comments` | 包含评论区内容 | False |
| `--max-comments` | 每个视频的最大评论数 | 10 |
| `--json` | JSON 格式输出 | False |
| `--pretty` | 格式化 JSON 输出 | False |
| `--markdown` | Markdown 格式输出 | False |
| `-o, --output` | 保存输出到文件 | - |
| `--save-raw` | 保存原始响应 | False |

### 排序方式

- `relevance` - 相关性（默认）
- `date` - 发布日期（最新优先）
- `rating` - 评分（最高优先）
- `viewCount` - 播放量（最多优先）
- `title` - 标题（字母顺序）

## 输出信息

### 基础信息
- 视频 ID、标题
- 频道名称、频道 ID
- 发布时间、视频时长
- 视频链接、缩略图

### 视频详情
- 分类 ID
- 清晰度（HD/SD）
- 字幕可用性
- 视频标签
- 视频描述

### 互动数据
- 播放量
- 点赞数
- 评论数

### 评论信息（可选）
- 评论作者
- 评论内容
- 点赞数
- 发布时间

## API 配额

YouTube Data API v3 使用配额系统：

- **每日配额**: 10,000 单位（默认）
- **Search 请求**: 100 单位/次
- **Videos.list 请求**: 1 单位/次
- **CommentThreads.list 请求**: 1 单位/次

### 配额计算示例

搜索 10 个视频并获取评论：
- Search: 100 单位
- Videos.list: 1 单位
- CommentThreads.list (10个视频): 10 单位
- **总计**: 111 单位

每日可执行约 90 次这样的搜索。

## 测试

运行测试脚本：

```bash
python test_youtube_search.py
```

测试脚本会：
1. 搜索 "Python tutorial" 关键词
2. 获取前 3 个视频的详细信息
3. 显示格式化的结果

## 注意事项

1. **API 密钥安全**
   - 不要将 API 密钥提交到版本控制系统
   - 使用环境变量或配置文件存储
   - 定期轮换 API 密钥

2. **配额限制**
   - 注意每日配额限制
   - 合理设置 `--limit` 参数
   - 避免频繁请求

3. **评论获取**
   - 某些视频可能禁用评论
   - 评论获取会消耗额外配额
   - 使用 `--max-comments` 控制数量

4. **搜索限制**
   - 单次搜索最多返回 50 个结果
   - 需要更多结果时使用分页（需修改代码）

## 故障排除

### 错误：缺少 API 密钥
```
错误: 缺少 YouTube API 密钥
```
**解决方案**: 设置 `YOUTUBE_API_KEY` 环境变量或使用 `--api-key` 参数

### 错误：配额超限
```
API 请求失败: The request cannot be completed because you have exceeded your quota.
```
**解决方案**: 等待配额重置（每日 00:00 PST）或申请增加配额

### 错误：API 密钥无效
```
API 请求失败: API key not valid.
```
**解决方案**: 检查 API 密钥是否正确，确保已启用 YouTube Data API v3

### 错误：评论被禁用
```
⚠️  评论获取失败: disabled comments
```
**说明**: 该视频禁用了评论功能，这是正常情况

## 文件结构

```
scripts/youtube/
├── youtube_search.py          # 主搜索脚本
├── test_youtube_search.py     # 测试脚本
├── README.md                  # 本文档
└── responses/                 # 原始响应保存目录（自动创建）
```

## 相关链接

- [YouTube Data API v3 文档](https://developers.google.com/youtube/v3/docs)
- [API 配额说明](https://developers.google.com/youtube/v3/getting-started#quota)
- [Google Cloud Console](https://console.cloud.google.com/)

## 许可证

本工具遵循项目主许可证。
