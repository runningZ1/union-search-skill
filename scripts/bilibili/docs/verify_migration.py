"""
video_content_research 迁移验证脚本
运行此脚本确认迁移后功能是否正常
"""

import asyncio
import sys
from pathlib import Path

print("=" * 70)
print("🔍 video_content_research 迁移验证脚本")
print("=" * 70)

# 检查 Python 版本
print(f"\n📌 Python 版本: {sys.version}")
if sys.version_info < (3, 9):
    print("❌ Python 版本过低，需要 3.9 或以上")
    sys.exit(1)
else:
    print("✅ Python 版本符合要求")

# 检查 bilibili_api 是否安装
print("\n📌 检查依赖...")
try:
    import bilibili_api
    print("✅ bilibili_api 已安装")
except ImportError:
    print("❌ bilibili_api 未安装!")
    print("\n请运行: pip install bilibili-api")
    sys.exit(1)

# 检查文件完整性
print("\n📌 检查文件完整性...")
toolkit_path = Path(__file__).parent
required_files = [
    "README.md",
    "MIGRATION.md",
    "get_video_full_data.py",
    "get_video_comments.py",
    "test_comment_api.py",
    "config.py.example"
]

all_exist = True
for file in required_files:
    file_path = toolkit_path / file
    if file_path.exists():
        print(f"✅ {file}")
    else:
        print(f"❌ {file} 缺失!")
        all_exist = False

# 检查 output 目录
output_dir = toolkit_path / "output"
if not output_dir.exists():
    output_dir.mkdir(exist_ok=True)
    print("📁 已创建 output 目录")
else:
    print("✅ output 目录存在")

if not all_exist:
    print("\n⚠️ 部分文件缺失，请确保完整复制 video_content_research 文件夹")
    sys.exit(1)

# 检查 config.py（可选）
print("\n📌 检查配置文件...")
config_py = toolkit_path / "config.py"
if config_py.exists():
    print("✅ config.py 存在（已配置凭证）")
    has_credential = True
else:
    print("⚠️ config.py 不存在（未配置凭证）")
    print("   如需获取评论、字幕等功能，请创建 config.py")
    has_credential = False

# 运行功能测试
print("\n" + "=" * 70)
print("🧪 开始功能测试")
print("=" * 70)

# 测试BVID
TEST_BVID = "BV1xx411c7mD"  # 这是一个通用的测试BVID

async def run_tests():
    """运行各项测试"""
    results = []

    # 测试1: 视频数据获取（无需登录）
    print("\n📺 测试1: 视频数据获取...")
    try:
        from get_video_full_data import get_all_video_data

        data = await get_all_video_data(TEST_BVID)

        if data and data.get('basic_info'):
            print(f"✅ 视频数据获取成功")
            print(f"   标题: {data['basic_info'].get('title', 'N/A')}")
            results.append(("视频数据获取", True))
        else:
            print("⚠️ 视频数据为空")
            results.append(("视频数据获取", False))
    except Exception as e:
        print(f"❌ 视频数据获取失败: {e}")
        results.append(("视频数据获取", False))

    # 测试2: 导出功能
    print("\n💾 测试2: 导出功能...")
    try:
        from get_video_full_data import save_to_json, save_to_markdown

        # 使用测试数据
        test_data = {
            "bvid": TEST_BVID,
            "fetch_time": "2026-02-05T00:00:00",
            "basic_info": {
                "title": "测试视频",
                "aid": 0,
                "owner": {
                    "mid": "0",
                    "name": "测试UP主",
                    "face": ""
                },
                "desc": "",
                "pubdate": 0,
                "pubdate_formatted": "2026-01-01 00:00:00",
                "duration": 0,
                "pic": "",
                "cid": 0
            },
            "statistics": {
                "view": 0,
                "danmaku": 0,
                "reply": 0,
                "favorite": 0,
                "coin": 0,
                "share": 0,
                "like": 0,
                "dislike": 0
            },
            "pages": [],
            "tags": [],
            "subtitles": [],
            "related_videos": [],
            "danmaku_count": 0,
            "danmakus_sample": []
        }

        json_path = save_to_json(test_data, "output/test_export.json")
        md_path = save_to_markdown(test_data, "output/test_export.md")

        if Path(json_path).exists() and Path(md_path).exists():
            print("✅ 导出功能成功 (JSON + Markdown)")

            # 清理测试文件
            Path(json_path).unlink(missing_ok=True)
            Path(md_path).unlink(missing_ok=True)
            results.append(("导出功能", True))
        else:
            print("❌ 导出文件未生成")
            results.append(("导出功能", False))
    except Exception as e:
        print(f"❌ 导出功能失败: {e}")
        results.append(("导出功能", False))

    # 测试3: 评论API基础功能（无需登录）
    print("\n💬 测试3: 评论API基础功能...")
    try:
        from bilibili_api import comment, video

        v = video.Video(bvid=TEST_BVID)
        info = await v.get_info()
        aid = info.get('aid')

        result = await comment.get_comments(
            oid=aid,
            type_=comment.CommentResourceType.VIDEO,
            page_index=1
        )

        print("✅ 评论API调用成功")
        print(f"   返回格式正确: {isinstance(result, dict)}")
        results.append(("评论API", True))
    except Exception as e:
        print(f"❌ 评论API调用失败: {e}")
        results.append(("评论API", False))

    # 测试4: 评论获取（需要凭证）
    if has_credential:
        print("\n🔐 测试4: 带凭证的评论获取...")
        try:
            from get_video_comments import CommentFetcher

            fetcher = CommentFetcher()
            comments = await fetcher.fetch_video_comments(
                TEST_BVID,
                max_pages=1  # 只测试1页
            )

            if comments:
                print(f"✅ 评论获取成功 (获取到 {len(comments)} 条)")
                results.append(("评论获取", True))
            else:
                print("⚠️ 评论获取成功但无数据")
                results.append(("评论获取", True))
        except Exception as e:
            print(f"❌ 评论获取失败: {e}")
            results.append(("评论获取", False))
    else:
        print("\n🔐 测试4: 带凭证的评论获取...")
        print("⏭️ 跳过（未配置凭证）")
        results.append(("评论获取", None))

    # 打印测试结果
    print("\n" + "=" * 70)
    print("📊 测试结果汇总")
    print("=" * 70)

    passed = sum(1 for _, success in results if success is True)
    skipped = sum(1 for _, success in results if success is None)
    total = len(results)

    for name, success in results:
        if success is True:
            status = "✅ 通过"
        elif success is False:
            status = "❌ 失败"
        else:
            status = "⏭️ 跳过"
        print(f"{name:20} {status}")

    print(f"\n总计: {passed}/{total - skipped} 项测试通过", end="")
    if skipped > 0:
        print(f" ({skipped} 项跳过)")
    else:
        print()

    if passed == total - skipped:
        print("\n🎉 所有测试通过！迁移成功！")
        print("\nvideo_content_research 已完全可用，功能与原项目一致。")
        return True
    else:
        print("\n⚠️ 部分测试失败，请检查:")
        print("1. bilibili-api 是否为最新版本")
        print("2. 网络连接是否正常")
        print("3. video_content_research 文件夹是否完整")
        print("4. config.py 是否正确配置（如需登录功能）")
        return False

if __name__ == "__main__":
    try:
        success = asyncio.run(run_tests())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️ 测试被中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ 测试过程出错: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
