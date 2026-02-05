# video_content_research 迁移指南

## 📋 概述

`video_content_research` 是一个B站视频数据和评论获取工具包，可以迁移到任何Python项目中使用。

---

## ✅ 前置条件

### 必需依赖

在目标项目中，必须安装 `bilibili-api` 库：

```bash
pip install bilibili-api
```

或使用 requirements.txt：

```bash
pip install -r requirements.txt
```

### Python 版本

- Python >= 3.9

---

## 🚀 迁移步骤

### 步骤 1：复制文件夹

将整个 `video_content_research` 文件夹复制到目标项目：

```bash
# 方式一：直接复制
cp -r video_content_research /your/project/path/

# 方式二：Windows
xcopy /E /I video_content_research C:\your\project\path\video_content_research
```

### 步骤 2：配置凭证（可选）

如果需要获取评论、字幕等需要登录的功能：

1. 复制 `config.py.example` 为 `config.py`
2. 填入你的 SESSDATA

```python
# config.py
SESSDATA = "你的SESSDATA"
BILI_JCT = ""  # 可选
BUVID3 = ""    # 可选
```

### 步骤 3：验证功能

在目标项目中运行验证脚本：

```bash
cd video_content_research
python verify_migration.py
```

---

## 📁 文件结构

迁移后的文件结构：

```
your_project/
├── video_content_research/
│   ├── README.md                          # 使用说明
│   ├── MIGRATION.md                      # 本文件
│   ├── verify_migration.py               # 迁移验证脚本
│   ├── config.py.example                 # 配置文件示例
│   ├── config.py                         # 配置文件（需创建）
│   ├── get_video_full_data.py            # 视频数据获取
│   ├── get_video_comments.py             # 评论获取（需登录）
│   ├── test_comment_api.py               # API测试脚本
│   ├── research_notes.md                 # 研究笔记
│   ├── requirements.txt                  # 依赖列表
│   ├── .gitignore                        # Git忽略文件
│   └── output/                           # 输出目录
│       ├── video_data_*.json             # 视频数据
│       └── comments_*.json               # 评论数据
└── your_code.py                          # 你的代码
```

---

## 🔧 使用方式

### 方式一：直接运行脚本

```bash
cd video_content_research

# 获取视频完整数据（无需登录）
python get_video_full_data.py BV19CzjBvEGx

# 获取评论（需要配置凭证）
python get_video_comments.py BV19CzjBvEGx

# 测试API
python test_comment_api.py
```

### 方式二：作为模块导入

```python
# 获取视频数据
import asyncio
from video_content_research.get_video_full_data import get_all_video_data

async def main():
    data = await get_all_video_data("BV19CzjBvEGx")
    print(data['basic_info']['title'])

asyncio.run(main())
```

---

## 📦 各脚本功能说明

### get_video_full_data.py - 视频数据获取

**功能**：获取视频的完整基础数据

**需要登录**：否

**获取内容**：
- 基本信息（标题、UP主、发布时间等）
- 统计数据（播放、点赞、投币等）
- 分P信息、标签
- 相关推荐视频
- 弹幕（前20条样本）

**输出**：
- `output/video_data_*.json`
- `output/video_data_*.md`

---

### get_video_comments.py - 评论获取

**功能**：获取视频所有评论（含二级评论）

**需要登录**：是（需配置 config.py）

**获取内容**：
- 一级评论
- 二级评论（楼中楼）
- 用户信息、点赞数、回复数
- 表情、跳转链接

**输出**：
- `output/comments_*.json`
- `output/comments_*.md`

---

### test_comment_api.py - API测试

**功能**：测试评论API的各种功能

**需要登录**：部分功能需要

**测试内容**：
1. 基础API（无需登录）
2. 带凭证的评论获取
3. 评论翻页
4. 评论排序
5. 二级评论

---

## ⚙️ 配置说明

### config.py 格式

```python
from bilibili_api import Credential

# 必需：SESSDATA
SESSDATA = "你的SESSDATA"

# 可选
BILI_JCT = ""
BUVID3 = ""

def get_credential() -> Credential:
    return Credential(
        sessdata=SESSDATA,
        bili_jct=BILI_JCT,
        buvid3=BUVID3
    )
```

### 如何获取 SESSDATA

1. 登录 B站网页版 (https://www.bilibili.com)
2. 打开浏览器开发者工具（F12）
3. 切换到 Application 标签
4. 找到 Cookies → https://www.bilibili.com
5. 复制 SESSDATA 的值

---

## ✅ 迁移检查清单

迁移完成后，请逐项检查：

- [ ] `video_content_research` 文件夹已完整复制
- [ ] 目标项目已安装 `bilibili-api` 库
- [ ] （可选）已创建 `config.py` 并配置凭证
- [ ] 运行 `verify_migration.py` 无错误
- [ ] 视频数据获取功能正常
- [ ] （如已配置凭证）评论获取功能正常
- [ ] 输出文件正常生成

---

## 🐛 常见问题

### Q1: ImportError: No module named 'bilibili_api'

**解决方案**：
```bash
pip install bilibili-api
```

### Q2: ModuleNotFoundError: No module named 'video_content_research'

**解决方案**：
确保 `video_content_research` 文件夹在你的 Python 路径中：
- 方法1：在项目根目录运行脚本
- 方法2：将 `video_content_research` 放在 `site-packages` 目录
- 方法3：设置 PYTHONPATH 环境变量

### Q3: 评论获取失败

**可能原因**：
1. 未配置 `config.py`
2. SESSDATA 过期
3. 网络问题

**解决方案**：
- 检查 `config.py` 是否存在
- 重新获取 SESSDATA
- 检查网络连接

### Q4: 字幕获取失败

**可能原因**：
字幕功能需要登录凭证

**解决方案**：
配置 `config.py` 并填入有效的 SESSDATA

---

## 📊 功能对照表

| 功能 | 原项目 | 迁移后 | 状态 |
|------|--------|--------|------|
| 视频基本信息 | ✅ | ✅ | 完全一致 |
| 视频统计数据 | ✅ | ✅ | 完全一致 |
| 分P信息 | ✅ | ✅ | 完全一致 |
| 标签信息 | ✅ | ✅ | 完全一致 |
| 相关推荐 | ✅ | ✅ | 完全一致 |
| 弹幕获取 | ✅ | ✅ | 完全一致 |
| JSON导出 | ✅ | ✅ | 完全一致 |
| Markdown导出 | ✅ | ✅ | 完全一致 |
| 评论获取 | ✅ | ✅ | 完全一致（需凭证）|
| 二级评论 | ✅ | ✅ | 完全一致（需凭证）|

---

## 🎯 核心保证

迁移到新项目后，以下内容**完全一致**：

1. **功能一致性**
   - 所有获取功能完全相同
   - 输出格式完全相同
   - API调用方式完全相同

2. **性能一致性**
   - 获取速度相同
   - 请求限流机制相同
   - 错误处理相同

3. **输出一致性**
   - JSON格式完全相同
   - Markdown报告格式相同
   - 控制台输出相同

---

## 🔒 安全建议

1. **不要提交凭证到版本控制**
   - 将 `config.py` 添加到 `.gitignore`
   - 只提交 `config.py.example`

2. **定期更新 SESSDATA**
   - SESSDATA 有过期时间
   - 过期后需重新获取

3. **保护个人信息**
   - 不要在公开场合分享 SESSDATA
   - 定期更换B站密码

---

## 📝 版本信息

- **创建时间**: 2026-02-05
- **bilibili-api 版本**: 17.4.1+
- **Python 版本**: 3.9+

---

## 💡 提示

1. **首次使用前**建议先运行验证脚本
2. **网络问题**：如遇到获取失败，检查网络连接
3. **API更新**：如遇到功能异常，检查 bilibili-api 是否需要更新
4. **输出目录**：默认为 `./output/`，可通过参数自定义

---

## 📞 支持

如遇到问题，请检查：
1. bilibili-api 是否正确安装
2. Python 版本是否符合要求
3. 网络连接是否正常
4. 文件夹是否完整复制
5. 凭证是否配置正确（如需要登录功能）

---

**迁移完成后，功能效果与原项目完全一致！** ✅
