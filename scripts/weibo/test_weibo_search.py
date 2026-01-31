#!/usr/bin/env python3
"""
微博搜索测试脚本
用于验证微博搜索功能是否正常工作
"""
import os
import sys

# 添加当前目录到 Python 路径
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

def test_import():
    """测试是否能正确导入 weiboSpider 模块"""
    print("=" * 60)
    print("测试 1: 导入 weiboSpider 模块")
    print("=" * 60)

    WEIBO_SPIDER_PATH = r"D:\Programs\weiboSpider"

    if not os.path.exists(WEIBO_SPIDER_PATH):
        print(f"❌ 错误: weiboSpider 项目不存在于: {WEIBO_SPIDER_PATH}")
        return False

    if WEIBO_SPIDER_PATH not in sys.path:
        sys.path.insert(0, WEIBO_SPIDER_PATH)

    try:
        from weibo_spider.spider import Spider
        print(f"✓ 成功导入 Spider 类")
        print(f"✓ weiboSpider 路径: {WEIBO_SPIDER_PATH}")
        return True
    except ImportError as e:
        print(f"❌ 导入失败: {e}")
        print(f"提示: 请确保已安装 weiboSpider 依赖:")
        print(f"  cd {WEIBO_SPIDER_PATH}")
        print(f"  pip install -r requirements.txt")
        return False


def test_env_file():
    """测试环境变量文件是否存在"""
    print("\n" + "=" * 60)
    print("测试 2: 检查环境变量配置")
    print("=" * 60)

    env_file = os.path.join(current_dir, ".env")
    env_example = os.path.join(current_dir, ".env.example")

    if os.path.exists(env_file):
        print(f"✓ 找到 .env 文件: {env_file}")

        # 检查必需的环境变量
        with open(env_file, "r", encoding="utf-8") as f:
            content = f.read()

        has_user_id = "WEIBO_USER_ID=" in content and "YOUR_" not in content
        has_cookie = "WEIBO_COOKIE=" in content and "YOUR_COOKIE_HERE" not in content

        if has_user_id:
            print("✓ WEIBO_USER_ID 已配置")
        else:
            print("⚠ WEIBO_USER_ID 未配置或使用默认值")

        if has_cookie:
            print("✓ WEIBO_COOKIE 已配置")
        else:
            print("⚠ WEIBO_COOKIE 未配置或使用默认值")

        return has_user_id and has_cookie
    else:
        print(f"⚠ 未找到 .env 文件")
        print(f"提示: 复制 .env.example 为 .env 并填入配置:")
        print(f"  cp {env_example} {env_file}")
        return False


def test_script_exists():
    """测试脚本文件是否存在"""
    print("\n" + "=" * 60)
    print("测试 3: 检查脚本文件")
    print("=" * 60)

    script_file = os.path.join(current_dir, "weibo_search.py")

    if os.path.exists(script_file):
        print(f"✓ 找到脚本文件: {script_file}")
        return True
    else:
        print(f"❌ 未找到脚本文件: {script_file}")
        return False


def test_responses_dir():
    """测试 responses 目录"""
    print("\n" + "=" * 60)
    print("测试 4: 检查 responses 目录")
    print("=" * 60)

    # 获取项目根目录
    root_dir = os.path.dirname(os.path.dirname(current_dir))
    responses_dir = os.path.join(root_dir, "responses")

    if os.path.exists(responses_dir):
        print(f"✓ responses 目录存在: {responses_dir}")
    else:
        print(f"⚠ responses 目录不存在,将在首次运行时自动创建")
        print(f"  路径: {responses_dir}")

    return True


def print_usage_example():
    """打印使用示例"""
    print("\n" + "=" * 60)
    print("使用示例")
    print("=" * 60)

    script_path = os.path.join(current_dir, "weibo_search.py")

    print("\n基本用法:")
    print(f"python {script_path} --user-id 1669879400 --cookie \"YOUR_COOKIE\"")

    print("\n使用环境变量:")
    print(f"python {script_path}")

    print("\n高级用法:")
    print(f"python {script_path} --user-id 1669879400 --limit 20 --filter 1 --sort-by up_num")

    print("\n获取帮助:")
    print(f"python {script_path} --help")


def main():
    """运行所有测试"""
    print("微博搜索功能测试")
    print("=" * 60)

    results = []

    # 运行测试
    results.append(("导入模块", test_import()))
    results.append(("环境变量", test_env_file()))
    results.append(("脚本文件", test_script_exists()))
    results.append(("响应目录", test_responses_dir()))

    # 打印测试结果
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)

    all_passed = True
    for name, passed in results:
        status = "✓ 通过" if passed else "❌ 失败"
        print(f"{name}: {status}")
        if not passed:
            all_passed = False

    # 打印使用示例
    if all_passed:
        print("\n✓ 所有测试通过!")
        print_usage_example()
    else:
        print("\n⚠ 部分测试失败,请根据上述提示修复问题")

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
