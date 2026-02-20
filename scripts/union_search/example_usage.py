#!/usr/bin/env python3
"""
Union Search 使用示例

演示如何使用 union_search 模块进行多平台搜索。
"""

import sys
from pathlib import Path

# 添加模块路径
sys.path.insert(0, str(Path(__file__).parent))

from union_search import union_search, format_markdown, format_json


def example_1_basic_search():
    """示例 1: 基础多平台搜索"""
    print("\n" + "=" * 80)
    print("示例 1: 基础多平台搜索")
    print("=" * 80)

    # 搜索多个平台
    results = union_search(
        keyword="Python编程",
        platforms=["wikipedia", "github", "reddit"],
        limit=3,
        max_workers=3
    )

    print(format_markdown(results))


def example_2_search_group():
    """示例 2: 使用平台组搜索"""
    print("\n" + "=" * 80)
    print("示例 2: 搜索社交媒体平台组")
    print("=" * 80)

    # 搜索社交媒体组
    results = union_search(
        keyword="机器学习",
        platforms=["xiaohongshu", "bilibili", "zhihu"],
        limit=5,
        max_workers=3
    )

    print(format_markdown(results))


def example_3_search_engines():
    """示例 3: 搜索多个搜索引擎"""
    print("\n" + "=" * 80)
    print("示例 3: 搜索多个搜索引擎")
    print("=" * 80)

    # 搜索多个搜索引擎并启用去重
    results = union_search(
        keyword="人工智能应用",
        platforms=["google", "duckduckgo", "brave"],
        limit=5,
        deduplicate=True,
        max_workers=3
    )

    # 输出 JSON 格式
    print(format_json(results, pretty=True))


def example_4_custom_output():
    """示例 4: 自定义输出处理"""
    print("\n" + "=" * 80)
    print("示例 4: 自定义输出处理")
    print("=" * 80)

    results = union_search(
        keyword="React框架",
        platforms=["github", "reddit"],
        limit=3
    )

    # 自定义输出格式
    print(f"\n🔍 搜索关键词: {results['keyword']}")
    print(f"⏰ 搜索时间: {results['timestamp']}")
    print(f"📊 统计:")

    summary = results['summary']
    print(f"   - 总平台数: {summary['total_platforms']}")
    print(f"   - 成功: {summary['successful']}")
    print(f"   - 失败: {summary['failed']}")
    print(f"   - 总结果数: {summary['total_items']}")

    print(f"\n📝 各平台详情:")
    for platform, result in results['results'].items():
        if result['success']:
            print(f"\n  {platform.upper()}:")
            for item in result['items']:
                title = item.get('title', item.get('name', 'N/A'))
                url = item.get('url', item.get('link', 'N/A'))
                print(f"    - {title}")
                print(f"      {url}")


def example_5_save_results():
    """示例 5: 保存搜索结果"""
    print("\n" + "=" * 80)
    print("示例 5: 保存搜索结果到文件")
    print("=" * 80)

    results = union_search(
        keyword="深度学习框架",
        platforms=["github", "wikipedia"],
        limit=5
    )

    # 保存为 JSON
    output_file = Path(__file__).parent / "test-file" / "example_output.json"
    output_file.parent.mkdir(exist_ok=True)

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(format_json(results, pretty=True))

    print(f"\n✅ 结果已保存到: {output_file}")
    print(f"   文件大小: {output_file.stat().st_size} 字节")


def main():
    """运行所有示例"""
    print("\n" + "=" * 80)
    print("Union Search 使用示例")
    print("=" * 80)

    examples = [
        example_1_basic_search,
        example_2_search_group,
        example_3_search_engines,
        example_4_custom_output,
        example_5_save_results,
    ]

    for example in examples:
        try:
            example()
        except Exception as e:
            print(f"\n❌ 示例执行失败: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "=" * 80)
    print("所有示例执行完成!")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
