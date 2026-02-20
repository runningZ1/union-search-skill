# 知乎搜索模块

基于 TikHub API 的知乎搜索模块，单文件架构，生产就绪。

## 快速开始

### 安装依赖

```bash
pip install requests loguru python-dotenv
```

### 配置环境变量

在项目根目录的 `.env` 文件中配置：

```
TIKHUB_TOKEN=your_token_here
```

### Python 调用

```python
from scripts.zhihu.zhihu_core import ZhihuSearchCore, Vertical, SortType, TimeInterval

# 初始化
core = ZhihuSearchCore()

# 基础搜索
results = core.search(keyword="人工智能", limit=20)

# 高级搜索
results = core.search(
    keyword="深度学习",
    limit=20,
    vertical=Vertical.ANSWER,           # 只看回答
    sort=SortType.UPVOTED,              # 最多赞同
    time_interval=TimeInterval.ONE_WEEK, # 一周内
    save_response=True                   # 保存响应
)

# 处理结果
for item in results:
    print(f"{item['type']}: {item['title']}")
    print(f"赞同: {item['stats']['voteup_count']}")
```

### 命令行调用

```bash
# 基础搜索
python scripts/zhihu/zhihu_core.py "人工智能" --num 20

# 高级搜索
python scripts/zhihu/zhihu_core.py "机器学习" \
    --vertical answer \
    --sort upvoted \
    --time week \
    --save
```

## 参数说明

### 内容类型 (vertical)
- `all` - 不限类型（默认）
- `answer` - 只看回答
- `article` - 只看文章
- `zvideo` - 只看视频

### 排序方式 (sort)
- `default` - 综合排序（默认）
- `upvoted` - 最多赞同
- `newest` - 最新发布

### 时间筛选 (time)
- `all` - 全部时间（默认）
- `day` - 一天内
- `week` - 一周内
- `month` - 一个月内
- `3months` - 三个月内
- `6months` - 半年内
- `year` - 一年内

## 文件结构

```
scripts/zhihu/
├── zhihu_core.py          # 核心模块（唯一必需文件）
├── requirements.txt        # 依赖列表
├── README.md              # 本文档
├── responses/             # 响应缓存目录
└── archived_modules_20260220/  # 归档的旧模块
```

## 核心特性

- ✅ 单文件架构，部署简单
- ✅ 完整的错误处理和重试机制
- ✅ 支持所有 TikHub API 参数
- ✅ 自动保存响应到 JSON 文件
- ✅ 详细的日志记录
- ✅ 命令行和 Python 双接口

## API 说明

### ZhihuSearchCore.search()

```python
def search(
    keyword: str,              # 搜索关键词（必填）
    limit: int = 20,           # 返回结果数量
    vertical: Vertical = Vertical.ALL,  # 内容类型筛选
    sort: SortType = SortType.DEFAULT,  # 排序方式
    time_interval: TimeInterval = TimeInterval.ALL,  # 时间筛选
    show_all_topics: ShowAllTopics = ShowAllTopics.HIDE,  # 是否显示话题
    search_source: SearchSource = SearchSource.NORMAL,  # 搜索来源
    save_response: bool = False,  # 是否保存响应
    output_dir: Optional[str] = None  # 输出目录
) -> List[Dict[str, Any]]
```

## 返回数据结构

```python
{
    "type": "answer",           # 内容类型
    "id": "123456",            # ID
    "title": "标题",           # 标题
    "excerpt": "摘要",         # 摘要
    "url": "链接",             # URL
    "created_time": 1234567890, # 创建时间
    "author": {                # 作者信息
        "name": "作者名",
        "url_token": "token",
        "headline": "签名"
    },
    "stats": {                 # 统计信息
        "voteup_count": 100,   # 赞同数
        "comment_count": 10,   # 评论数
        "favorite_count": 5    # 收藏数
    }
}
```

## 技术栈

- Python 3.7+
- requests - HTTP 客户端
- loguru - 日志记录
- python-dotenv - 环境变量管理
- TikHub API v1

## 许可证

MIT
