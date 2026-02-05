# video_content_research - 快速迁移指南

> B站视频数据和评论获取工具包

---

## 🚀 一键迁移

### 步骤 1: 复制文件夹

```bash
cp -r video_content_research /your/project/path/
```

### 步骤 2: 安装依赖

```bash
cd video_content_research
pip install -r requirements.txt
```

### 步骤 3: 验证

```bash
python verify_migration.py
```

---

## 📋 文件清单

| 类型 | 文件 | 说明 |
|------|------|------|
| **核心** | get_video_full_data.py | 视频数据获取（无需登录） |
| **核心** | get_video_comments.py | 评论获取（需登录） |
| **测试** | test_comment_api.py | API测试脚本 |
| **验证** | verify_migration.py | 迁移验证脚本 |
| **配置** | config.py.example | 配置示例 |
| **配置** | requirements.txt | 依赖列表 |
| **配置** | .gitignore | Git忽略文件 |
| **文档** | README.md | 使用说明 |
| **文档** | MIGRATION.md | 详细迁移指南 |
| **文档** | research_notes.md | 研究笔记 |

---

## ⚙️ 配置凭证（可选）

如需获取评论等功能：

```bash
# 1. 复制配置示例
cp config.py.example config.py

# 2. 编辑 config.py，填入 SESSDATA
# SESSDATA 获取方法见 README.md
```

---

## ✅ 使用示例

```bash
# 获取视频数据（无需登录）
python get_video_full_data.py BV19CzjBvEGx

# 获取评论（需要配置凭证）
python get_video_comments.py BV19CzjBvEGx

# 测试API
python test_comment_api.py
```

---

## 📊 功能对照

| 功能 | 无需登录 | 需要登录 |
|------|---------|---------|
| 视频基本信息 | ✅ | - |
| 统计数据 | ✅ | - |
| 分P信息 | ✅ | - |
| 标签信息 | ✅ | - |
| 相关推荐 | ✅ | - |
| 弹幕获取 | ✅ | - |
| 字幕获取 | - | ✅ |
| 评论获取 | - | ✅ |
| 二级评论 | - | ✅ |

---

## 🎯 验证结果

```
✅ 视频数据获取 - 通过
✅ 导出功能 - 通过
✅ 评论API - 通过
✅ 评论获取 - 通过

🎉 所有测试通过！迁移成功！
```

---

## 📞 常见问题

**Q: ImportError: No module named 'bilibili_api'**
```bash
pip install bilibili-api
```

**Q: 评论获取失败**
- 检查是否配置了 `config.py`
- 检查 SESSDATA 是否过期

**Q: 更多问题**
- 查看 `README.md` 详细说明
- 查看 `MIGRATION.md` 迁移指南

---

## 🔒 安全提醒

⚠️ **不要将 `config.py` 提交到版本控制！**

`.gitignore` 已自动忽略此文件。

---

**版本**: 1.0.0 | **日期**: 2026-02-05 | **bilibili-api**: 17.4.1+
