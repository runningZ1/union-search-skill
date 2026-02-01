#!/usr/bin/env python3
"""
GitHub Search 测试脚本

测试 GitHub 搜索功能的基本操作
"""

import subprocess
import sys
from pathlib import Path


def run_command(cmd, description):
    """运行命令并显示结果"""
    print(f"\n{'='*70}")
    print(f"测试: {description}")
    print(f"{'='*70}")
    print(f"命令: {' '.join(cmd)}\n")

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode == 0:
        print(result.stdout)
        return True
    else:
        print(f"错误: {result.stderr}")
        return False


def main():
    """运行所有测试"""
    script_path = Path(__file__).parent / "github_search.py"

    tests = [
        # 仓库搜索测试
        ([sys.executable, str(script_path), "repo", "react", "--limit", "3"],
         "搜索 React 仓库"),

        ([sys.executable, str(script_path), "repo", "machine learning",
          "--language", "python", "--stars", ">1000", "--limit", "3"],
         "搜索高星标 Python 机器学习仓库"),

        # 代码搜索测试
        ([sys.executable, str(script_path), "code", "async def fetch",
          "--language", "python", "--limit", "3"],
         "搜索 Python 代码"),

        # 问题搜索测试
        ([sys.executable, str(script_path), "issue", "good first issue",
          "--label", "help wanted", "--limit", "3"],
         "搜索适合新手的问题"),

        # 速率限制测试
        ([sys.executable, str(script_path), "rate-limit"],
         "检查 API 速率限制"),

        # JSON 格式测试
        ([sys.executable, str(script_path), "repo", "django",
          "--limit", "2", "--format", "json"],
         "JSON 格式输出"),

        # Markdown 格式测试
        ([sys.executable, str(script_path), "repo", "rust web framework",
          "--language", "rust", "--limit", "2", "--format", "markdown"],
         "Markdown 格式输出"),
    ]

    passed = 0
    failed = 0

    for cmd, description in tests:
        if run_command(cmd, description):
            passed += 1
        else:
            failed += 1

    # 打印总结
    print(f"\n{'='*70}")
    print("测试总结")
    print(f"{'='*70}")
    print(f"通过: {passed}")
    print(f"失败: {failed}")
    print(f"总计: {passed + failed}")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
