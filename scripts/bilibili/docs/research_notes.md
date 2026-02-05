# 视频内容获取与评论区研究笔记

> 记录B站API研究和开发过程中的发现、问题和解决方案

---

## 📅 2026-02-05

### 初步探索

#### 1. 评论API分析

**问题**：直接调用 `comment.get_comments()` 返回的评论数为0

**测试结果**：
```python
# 使用 aid 作为 oid
result = await comment.get_comments(
    oid=aid,
    type_=comment.CommentResourceType.VIDEO,
    page_index=1
)
# 返回：count=0, replies=None
```

**结论**：B站评论API需要登录凭证（Credential）才能获取评论

---

#### 2. 弹幕API分析

**问题**：弹幕对象属性不明确

**测试结果**：
```python
danmakus = await v.get_danmakus()
dm = danmakus[0]

# 弹幕对象属性：
# - dm_time: 弹幕在视频中的时间位置（毫秒）
# - send_time: 发送时间戳
# - text: 弹幕文本
# - uid: 发送者ID
# - color: 颜色
# - font_size: 字体大小
# - mode: 弹幕模式
```

**解决**：修正了弹幕数据结构，使用 `dm.dm_time` 而非 `dm.time`

---

#### 3. 字幕API分析

**问题**：`get_subtitle()` 需要登录

**错误信息**：
```
Credential 类未提供 sessdata 或者是空
```

**结论**：字幕API同样需要登录凭证

---

## 🔐 登录凭证研究

### 如何获取 SESSDATA

1. 登录 B站网页版 (https://www.bilibili.com)
2. 打开浏览器开发者工具（F12）
3. 切换到 Network 标签
4. 刷新页面，找到任意请求
5. 查看 Request Headers
6. 在 Cookie 中找到 `SESSDATA=xxxxx`

### Credential 初始化

```python
from bilibili_api import Credential

# 最简配置（只需SESSDATA）
credential = Credential(sessdata="你的SESSDATA")

# 完整配置
credential = Credential(
    sessdata="你的SESSDATA",
    bili_jct="你的bili_jct",  # 从Cookie中获取
    buvid3="你的buvid3"      # 从Cookie中获取
)
```

### 使用凭证

```python
# 方法1：创建Video对象时传入
v = video.Video(bvid=bvid, credential=credential)

# 方法2：调用API时传入
result = await comment.get_comments(
    oid=aid,
    type_=comment.CommentResourceType.VIDEO,
    page_index=1,
    credential=credential
)
```

---

## 📊 API参数研究

### comment.get_comments() 参数

| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| oid | int | ✅ | 资源ID（视频的aid） |
| type_ | CommentResourceType | ✅ | 资源类型（VIDEO） |
| page_index | int | ❌ | 页码（默认1） |
| order | OrderType | ❌ | 排序方式（TIME/LIKE/HOT） |
| credential | Credential | ❌ | 登录凭证 |

### OrderType 枚举

```python
from bilibili_api import comment

comment.OrderType.TIME  # 按时间排序
comment.OrderType.LIKE  # 按点赞数排序
comment.OrderType.HOT   # 按热度排序
```

---

## 🧪 测试发现

### 1. 评论数据结构

```json
{
  "page": {
    "num": 0,
    "size": 0,
    "count": 0,  // 总评论数
    "acount": 0
  },
  "replies": [
    {
      "rpid": 1234567890,  // 评论ID
      "member": {
        "mid": "用户ID",
        "uname": "用户名",
        "face": "头像URL"
      },
      "content": {
        "message": "评论内容",
        "emote": [...],  // 表情
        "jump_url": [...]  // 跳转链接
      },
      "like": 10,  // 点赞数
      "rcount": 5,  // 回复数
      "ctime": 1234567890,  // 发布时间戳
      "reply_control": {  // 回复控制
        "time_desc": "3小时前"
      }
    }
  ],
  "top": {...},  // 置顶评论
  "upper": {...}  // UP主评论
}
```

### 2. 二级评论获取

使用 `root` 参数指定父评论的 `rpid`：

```python
# 获取某个评论的回复
sub_result = await comment.get_comments(
    oid=aid,
    type_=comment.CommentResourceType.VIDEO,
    root=parent_rpid,  // 父评论的rpid
    credential=credential
)
```

---

## ⚠️ 已知限制

1. **评论和字幕需要登录**
   - 必须提供有效的 SESSDATA
   - SESSDATA 有过期时间

2. **请求频率限制**
   - 需要在请求间添加延迟（建议0.3秒）
   - 过快请求可能导致IP被限制

3. **弹幕文本为空**
   - 部分弹幕的 `text` 字段为空字符串
   - 可能是特殊类型弹幕（代码弹幕等）

---

## 🚀 下一步计划

- [ ] 实现带登录的完整评论获取脚本
- [ ] 实现字幕获取功能
- [ ] 实现评论二级回复获取
- [ ] 优化请求频率控制
- [ ] 添加错误重试机制
- [ ] 实现评论导出为JSON/Markdown/CSV

---

## 📚 参考资料

- [bilibili-api 评论文档](https://nemo2011.github.io/bilibili-api/#/modules/comment)
- [bilibili-api Credential文档](https://nemo2011.github.io/bilibili-api/#/credential)
- [B站API分析 - 评论区](https://github.com/SocialSisterYi/bilibili-API-collect/blob/master/docs/comment/comment.md)
