#!/usr/bin/env python3
"""
Bilibili API 搜索测试脚本
快速测试 bilibili_api_search.py 的功能
"""

import asyncio
import sys
from pathlib import Path

# 添加脚本目录到路径
sys.path.insert(0, str(Path(__file__).parent))

try:
    from bilibili_api import search
except ImportError:
    print("错误: 未安装 bilibili-api 库")
    print("请运行: pip install bilibili-api-python aiohttp")
    sys.exit(1)


async def test_search():
    """测试基础搜索功能"""
    print("=" * 80)
    print("测试 Bilibili API 搜索功能")
    print("=" * 80)
    print()

    # 测试关键词
    test_keyword = "Python教程"

    print(f"🔍 搜索关键词: {test_keyword}")
    print("⏳ 正在搜索...\n")

    try:
        # 执行搜索
        search_result = await search.search_by_type(
            keyword=test_keyword,
            search_type=search.SearchObjectType.VIDEO,
            order_type=search.OrderVideo.TOTALRANK,
            page=1
        )

        results = search_result.get('result', [])

        if not results:
            print("❌ 未找到相关视频")
            return False

        print(f"✅ 找到 {len(results)} 个相关视频\n")

        # 显示前3个结果
        for idx, item in enumerate(results[:3], 1):
            print(f"{'='*80}")
            print(f"📹 视频 #{idx}")
            print(f"{'='*80}")
            print(f"标题: {item.get('title', '').replace('<em class=\"keyword\">', '').replace('</em>', '')}")
            print(f"BVID: {item.get('bvid', '')}")
            print(f"作者: {item.get('author', '')}")
            print(f"播放量: {item.get('play', 0):,}")
            print(f"链接: https://www.bilibili.com/video/{item.get('bvid', '')}")
            print()

        print("=" * 80)
        print("✅ 测试成功！bilibili-api 库工作正常")
        print("=" * 80)
        return True

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    success = await test_search()
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
