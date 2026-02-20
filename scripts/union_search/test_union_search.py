#!/usr/bin/env python3
"""
Union Search 模块测试脚本

测试 union_search 模块的基本功能,包括单平台搜索、多平台搜索、结果去重等。
"""

import sys
import json
from pathlib import Path

# 添加模块路径
sys.path.insert(0, str(Path(__file__).parent))

from union_search import (
    search_platform,
    union_search,
    format_markdown,
    format_json,
    list_platforms,
    PLATFORM_MODULES,
    PLATFORM_GROUPS,
)


def test_list_platforms():
    """测试列出所有平台"""
    print("=" * 80)
    print("测试 1: 列出所有可用平台")
    print("=" * 80)

    try:
        print("\n可用平台数量:", len(PLATFORM_MODULES))
        print("\n平台分组:")
        for group_name, platforms in PLATFORM_GROUPS.items():
            print(f"  - {group_name}: {len(platforms)} 个平台")
            for p in platforms:
                desc = PLATFORM_MODULES.get(p, {}).get("description", "无描述")
                print(f"    · {p}: {desc}")

        print("\n✅ 测试通过: 成功列出所有平台\n")
        return True
    except Exception as e:
        print(f"\n❌ 测试失败: {e}\n")
        return False


def test_single_platform_search():
    """测试单平台搜索"""
    print("=" * 80)
    print("测试 2: 单平台搜索 (Wikipedia)")
    print("=" * 80)

    try:
        platform, result = search_platform(
            platform="wikipedia",
            keyword="Python编程语言",
            limit=3
        )

        print(f"\n平台: {platform}")
        print(f"成功: {result['success']}")
        print(f"关键词: {result['keyword']}")

        if result['success']:
            print(f"结果数量: {result['total']}")
            print("\n前3条结果:")
            for i, item in enumerate(result['items'][:3], 1):
                print(f"\n  {i}. {item.get('title', 'N/A')}")
                if 'url' in item:
                    print(f"     URL: {item['url']}")
                if 'description' in item:
                    desc = item['description'][:100] + "..." if len(item['description']) > 100 else item['description']
                    print(f"     描述: {desc}")

            print("\n✅ 测试通过: Wikipedia 搜索成功\n")
            return True
        else:
            print(f"\n⚠️ 搜索失败: {result.get('error', '未知错误')}\n")
            return False

    except Exception as e:
        print(f"\n❌ 测试失败: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def test_multi_platform_search():
    """测试多平台并发搜索"""
    print("=" * 80)
    print("测试 3: 多平台并发搜索")
    print("=" * 80)

    try:
        # 测试搜索引擎组
        platforms = ["wikipedia", "duckduckgo", "brave"]
        keyword = "人工智能"

        print(f"\n搜索平台: {', '.join(platforms)}")
        print(f"关键词: {keyword}")

        results = union_search(
            keyword=keyword,
            platforms=platforms,
            limit=3,
            max_workers=3,
            timeout=30,
            deduplicate=False  # 测试时先不去重
        )

        print(f"\n搜索完成!")
        print(f"总平台数: {results['summary']['total_platforms']}")
        print(f"成功: {results['summary']['successful']}")
        print(f"失败: {results['summary']['failed']}")
        print(f"总结果数: {results['summary']['total_items']}")

        print("\n各平台结果:")
        for platform, result in results['results'].items():
            status = "✅" if result['success'] else "❌"
            print(f"  {status} {platform}: {result['total']} 条")
            if not result['success'] and result.get('error'):
                print(f"     错误: {result['error']}")

            # 显示第一条结果
            if result['items']:
                item = result['items'][0]
                print(f"     首条: {item.get('title', 'N/A')[:60]}")

        print("\n✅ 测试通过: 多平台并发搜索成功\n")
        return True

    except Exception as e:
        print(f"\n❌ 测试失败: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def test_deduplication():
    """测试结果去重功能"""
    print("=" * 80)
    print("测试 4: 结果去重功能")
    print("=" * 80)

    try:
        # 使用可能产生重复结果的平台组合
        platforms = ["google", "bing", "duckduckgo"]
        keyword = "Python编程"

        print(f"\n搜索平台: {', '.join(platforms)}")
        print(f"关键词: {keyword}")

        # 先不去重
        results_no_dedupe = union_search(
            keyword=keyword,
            platforms=platforms,
            limit=5,
            deduplicate=False
        )

        total_no_dedupe = results_no_dedupe['summary']['total_items']
        print(f"\n不去重: 总结果数 = {total_no_dedupe}")

        # 去重
        results_dedupe = union_search(
            keyword=keyword,
            platforms=platforms,
            limit=5,
            deduplicate=True
        )

        total_dedupe = results_dedupe['summary']['total_items']
        removed = results_dedupe['summary'].get('deduplicated', {}).get('total_removed', 0)

        print(f"去重后: 总结果数 = {total_dedupe}")
        print(f"移除重复项: {removed}")
        print(f"去重率: {removed / total_no_dedupe * 100:.1f}%")

        if 'deduplicated' in results_dedupe['summary']:
            dup_info = results_dedupe['summary']['deduplicated']
            print(f"\n去重详情:")
            print(f"  - URL 重复: {dup_info['url_duplicates']}")
            print(f"  - 标题重复: {dup_info['title_duplicates']}")

        print("\n✅ 测试通过: 去重功能正常\n")
        return True

    except Exception as e:
        print(f"\n❌ 测试失败: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def test_format_output():
    """测试输出格式化"""
    print("=" * 80)
    print("测试 5: 输出格式化")
    print("=" * 80)

    try:
        # 创建一个简单的测试结果
        test_result = {
            "keyword": "测试关键词",
            "timestamp": "2024-02-19T12:00:00",
            "platforms": ["wikipedia"],
            "limit_per_platform": 3,
            "summary": {
                "total_platforms": 1,
                "successful": 1,
                "failed": 0,
                "total_items": 2
            },
            "results": {
                "wikipedia": {
                    "platform": "wikipedia",
                    "success": True,
                    "items": [
                        {
                            "title": "测试词条1",
                            "url": "https://example.com/1",
                            "description": "这是测试描述1"
                        },
                        {
                            "title": "测试词条2",
                            "url": "https://example.com/2",
                            "description": "这是测试描述2"
                        }
                    ],
                    "total": 2
                }
            }
        }

        # 测试 Markdown 格式化
        print("\nMarkdown 格式输出:")
        print("-" * 80)
        md_output = format_markdown(test_result)
        print(md_output[:500] + "..." if len(md_output) > 500 else md_output)

        # 测试 JSON 格式化
        print("\nJSON 格式输出 (pretty):")
        print("-" * 80)
        json_output = format_json(test_result, pretty=True)
        print(json_output[:300] + "..." if len(json_output) > 300 else json_output)

        # 验证 JSON 可以被解析
        parsed = json.loads(json_output)
        print(f"\n✅ JSON 解析成功: {len(parsed)} 个顶级键")

        print("\n✅ 测试通过: 输出格式化正常\n")
        return True

    except Exception as e:
        print(f"\n❌ 测试失败: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def test_platform_groups():
    """测试平台分组功能"""
    print("=" * 80)
    print("测试 6: 平台分组功能")
    print("=" * 80)

    try:
        # 测试 dev 分组
        print("\n测试 'dev' 分组:")
        dev_platforms = PLATFORM_GROUPS.get("dev", [])
        print(f"平台: {dev_platforms}")

        results = union_search(
            keyword="machine learning",
            platforms=dev_platforms,
            limit=2,
            max_workers=2,
            timeout=30
        )

        print(f"\n结果:")
        print(f"  - 成功: {results['summary']['successful']}/{len(dev_platforms)}")
        print(f"  - 总结果数: {results['summary']['total_items']}")

        for platform, result in results['results'].items():
            status = "✅" if result['success'] else "❌"
            print(f"  {status} {platform}: {result['total']} 条")

        print("\n✅ 测试通过: 平台分组功能正常\n")
        return True

    except Exception as e:
        print(f"\n❌ 测试失败: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def main():
    """运行所有测试"""
    print("\n" + "=" * 80)
    print("Union Search 模块测试套件")
    print("=" * 80 + "\n")

    tests = [
        ("列出所有平台", test_list_platforms),
        ("单平台搜索", test_single_platform_search),
        ("多平台并发搜索", test_multi_platform_search),
        ("结果去重功能", test_deduplication),
        ("输出格式化", test_format_output),
        ("平台分组功能", test_platform_groups),
    ]

    results = []

    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"\n❌ 测试 '{test_name}' 发生异常: {e}\n")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))

    # 输出测试总结
    print("\n" + "=" * 80)
    print("测试总结")
    print("=" * 80)

    passed = sum(1 for _, success in results if success)
    total = len(results)

    for test_name, success in results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"  {status} - {test_name}")

    print(f"\n总计: {passed}/{total} 测试通过")
    print(f"成功率: {passed / total * 100:.1f}%")
    print("=" * 80 + "\n")

    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
