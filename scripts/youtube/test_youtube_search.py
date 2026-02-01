#!/usr/bin/env python3
"""
YouTube 搜索功能测试脚本
"""

import os
import sys
from pathlib import Path

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from youtube_search import (
    search_videos,
    get_video_details,
    format_text_output,
)


def test_youtube_search():
    """测试 YouTube 搜索功能"""
    # 从环境变量获取 API 密钥
    api_key = os.getenv("YOUTUBE_API_KEY", "AIzaSyA0CyfDsdFDVRSbfD6fEI3_AWlgazdf78s")

    if not api_key:
        print("错误: 未设置 YOUTUBE_API_KEY 环境变量")
        return 1

    print("=" * 80)
    print("YouTube 搜索功能测试")
    print("=" * 80)

    # 测试搜索
    keyword = "Python tutorial"
    print(f"\n测试 1: 搜索关键词 '{keyword}'")
    print("-" * 80)

    try:
        video_ids = search_videos(
            api_key=api_key,
            keyword=keyword,
            limit=3,
            order="relevance",
        )

        print(f"✅ 搜索成功，找到 {len(video_ids)} 个视频")
        print(f"视频 ID: {', '.join(video_ids)}")

        # 测试获取详细信息
        print(f"\n测试 2: 获取视频详细信息")
        print("-" * 80)

        results = get_video_details(
            api_key=api_key,
            video_ids=video_ids,
            include_comments=False,
        )

        print(f"✅ 获取详细信息成功，共 {len(results)} 个视频")

        # 显示结果
        format_text_output(results, keyword, include_comments=False)

        print("\n" + "=" * 80)
        print("✅ 所有测试通过")
        print("=" * 80)

        return 0

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(test_youtube_search())
