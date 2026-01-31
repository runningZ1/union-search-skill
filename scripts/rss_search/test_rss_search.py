#!/usr/bin/env python3
"""
RSS 搜索工具测试脚本
"""
import subprocess
import sys
import os

# 测试用的 RSS feed
TEST_FEED = "http://feedmaker.kindle4rss.com/feeds/AI_era.weixin.xml"

def run_command(cmd, description):
    """运行命令并显示结果"""
    print(f"\n{'='*60}")
    print(f"测试: {description}")
    print(f"命令: {' '.join(cmd)}")
    print(f"{'='*60}\n")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding='utf-8',
            timeout=60
        )

        if result.stdout:
            print(result.stdout)

        if result.stderr:
            print("STDERR:", result.stderr, file=sys.stderr)

        if result.returncode != 0:
            print(f"❌ 命令执行失败，返回码: {result.returncode}")
            return False
        else:
            print(f"✅ 命令执行成功")
            return True

    except subprocess.TimeoutExpired:
        print("❌ 命令执行超时")
        return False
    except Exception as e:
        print(f"❌ 执行出错: {e}")
        return False


def main():
    """运行所有测试"""
    script_path = os.path.join(os.path.dirname(__file__), "rss_search.py")

    if not os.path.exists(script_path):
        print(f"❌ 找不到脚本: {script_path}")
        return 1

    print("开始测试 RSS 搜索工具...")
    print(f"脚本路径: {script_path}")

    tests = [
        {
            "cmd": ["python", script_path, "--feed", TEST_FEED, "--limit", "3"],
            "desc": "获取前 3 条 RSS 条目（无搜索关键词）"
        },
        {
            "cmd": ["python", script_path, "AI", "--feed", TEST_FEED, "--limit", "5"],
            "desc": "搜索关键词 'AI'，限制 5 条结果"
        },
        {
            "cmd": ["python", script_path, "GPT", "--feed", TEST_FEED, "--markdown"],
            "desc": "搜索 'GPT' 并输出 Markdown 格式"
        },
        {
            "cmd": ["python", script_path, "--feed", TEST_FEED, "--limit", "2", "--json", "--pretty"],
            "desc": "获取 2 条结果并输出美化的 JSON"
        },
        {
            "cmd": ["python", script_path, "技术", "--feed", TEST_FEED, "--full", "--limit", "2"],
            "desc": "搜索 '技术' 并显示完整内容"
        },
    ]

    passed = 0
    failed = 0

    for test in tests:
        if run_command(test["cmd"], test["desc"]):
            passed += 1
        else:
            failed += 1

    print(f"\n{'='*60}")
    print(f"测试完成: ✅ {passed} 通过, ❌ {failed} 失败")
    print(f"{'='*60}")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
