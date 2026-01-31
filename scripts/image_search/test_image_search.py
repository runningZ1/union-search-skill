#!/usr/bin/env python3
"""
快速测试脚本 - 测试多平台图片搜索功能
每个平台只下载 3 张图片用于测试
"""

import sys
import os

# 添加脚本目录到路径
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)

try:
    # 导入主模块中的函数
    from multi_platform_image_search import (
        search_platform,
        search_all_platforms,
        print_summary,
        save_summary
    )
    print("✓ 成功导入 multi_platform_image_search 模块")
except ImportError as e:
    print(f"✗ 导入失败: {e}")
    print("\n请确保已安装依赖:")
    print("  pip install pyimagedl")
    sys.exit(1)


def test_single_platform():
    """测试单个平台"""
    print("\n" + "="*70)
    print("测试 1: 单个平台搜索（Pixabay）")
    print("="*70)

    result = search_platform(
        platform='pixabay',
        keyword='cat',
        num_images=3,
        output_dir='./test_images',
        num_threads=2,
        save_meta=True
    )

    if result['success']:
        print(f"\n✓ 测试通过！")
        print(f"  - 下载: {result['downloaded']} 张")
        print(f"  - 位置: {result['output_dir']}")
    else:
        print(f"\n✗ 测试失败: {result.get('error', 'Unknown error')}")

    return result['success']


def test_multiple_platforms():
    """测试多个平台"""
    print("\n" + "="*70)
    print("测试 2: 多平台搜索（Baidu, Bing, Pixabay）")
    print("="*70)

    results = search_all_platforms(
        keyword='flower',
        num_images=3,
        platforms=['baidu', 'bing', 'pixabay'],
        output_dir='./test_images',
        num_threads=2,
        save_meta=True,
        delay=0.5
    )

    successful = [p for p in results['platforms'] if p['success']]

    if len(successful) > 0:
        print(f"\n✓ 测试通过！")
        print(f"  - 成功平台: {len(successful)}/3")
        print(f"  - 总下载: {sum(p['downloaded'] for p in successful)} 张")
    else:
        print(f"\n✗ 测试失败: 所有平台都失败")

    return len(successful) > 0


def main():
    """运行所有测试"""
    print("\n" + "="*70)
    print("多平台图片搜索 - 快速测试")
    print("="*70)
    print("注意: 每个平台只下载 3 张图片用于测试")
    print("="*70)

    # 测试 1: 单个平台
    test1_passed = test_single_platform()

    # 测试 2: 多个平台
    test2_passed = test_multiple_platforms()

    # 总结
    print("\n" + "="*70)
    print("测试总结")
    print("="*70)
    print(f"测试 1 (单平台): {'✓ 通过' if test1_passed else '✗ 失败'}")
    print(f"测试 2 (多平台): {'✓ 通过' if test2_passed else '✗ 失败'}")

    if test1_passed and test2_passed:
        print("\n✓ 所有测试通过！脚本工作正常。")
        print("\n下一步:")
        print("  python multi_platform_image_search.py --keyword 'your keyword' --num 50")
    else:
        print("\n✗ 部分测试失败，请检查:")
        print("  1. 是否已安装 pyimagedl: pip install pyimagedl")
        print("  2. 网络连接是否正常")
        print("  3. 查看错误信息")

    print("="*70 + "\n")


if __name__ == '__main__':
    main()
