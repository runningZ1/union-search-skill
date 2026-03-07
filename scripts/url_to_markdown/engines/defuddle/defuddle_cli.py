#!/usr/bin/env python3
"""
Defuddle CLI 包装器 - 调用 Node.js Defuddle 进行网页内容提取

Defuddle 是一个免费、开源的网页内容提取库，可以：
- 提取网页主要内容，移除导航、广告、侧边栏等干扰元素
- 提取元数据（标题、作者、发布时间等）
- 转换为 Markdown 格式
- 无 API 限制，完全本地运行

GitHub: https://github.com/kepano/defuddle
"""

import json
import subprocess
import sys
from pathlib import Path
from typing import Optional, Dict, Any, List

# Defuddle 安装目录
DEFUDDLE_ROOT = Path(__file__).parent.parent.parent / "defuddle-node"
DEFUDDLE_CLI = DEFUDDLE_ROOT / "dist" / "cli.js"


class DefuddleClient:
    """
    Defuddle CLI 客户端

    通过子进程调用 Node.js Defuddle CLI 进行网页内容提取。
    """

    def __init__(self, timeout: int = 60):
        """
        初始化 DefuddleClient

        Args:
            timeout: 请求超时时间 (秒)
        """
        self.timeout = timeout
        self.cli_path = str(DEFUDDLE_CLI)

        # 验证 CLI 存在
        if not DEFUDDLE_CLI.exists():
            raise RuntimeError(
                f"Defuddle CLI not found at {DEFUDDLE_CLI}. "
                "Please ensure Defuddle is properly installed."
            )

    def fetch(
        self,
        url: str,
        markdown: bool = True,
        json_output: bool = False,
        debug: bool = False,
    ) -> Dict[str, Any]:
        """
        使用 Defuddle 提取网页内容

        Args:
            url: 要提取的网页 URL
            markdown: 是否输出 Markdown 格式
            json_output: 是否输出 JSON 格式（包含元数据）
            debug: 是否启用调试模式

        Returns:
            包含 title, content, url 等字段的字典
        """
        # 构建命令
        cmd = ["node", self.cli_path, "parse", url]

        if markdown:
            cmd.append("--markdown")
        if json_output:
            cmd.append("--json")
        if debug:
            cmd.append("--debug")

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout,
            )

            if result.returncode != 0:
                error_msg = result.stderr.strip() or f"Exit code: {result.returncode}"
                raise RuntimeError(f"Defuddle failed: {error_msg}")

            # 解析输出
            if json_output:
                # JSON 输出
                try:
                    data = json.loads(result.stdout)
                    return {
                        "url": url,
                        "title": data.get("title", ""),
                        "content": data.get("content", ""),
                        "description": data.get("description", ""),
                        "domain": data.get("domain", ""),
                        "favicon": data.get("favicon", ""),
                        "image": data.get("image", ""),
                        "author": data.get("author", ""),
                        "published": data.get("published", ""),
                        "meta_tags": data.get("metaTags", []),
                        "markdown": data.get("content", ""),
                    }
                except json.JSONDecodeError as e:
                    raise RuntimeError(f"Failed to parse JSON output: {e}")
            else:
                # Markdown 输出 - 同时也获取 JSON 来提取元数据
                cmd_with_json = ["node", self.cli_path, "parse", url, "--json"]
                json_result = subprocess.run(
                    cmd_with_json,
                    capture_output=True,
                    text=True,
                    timeout=self.timeout,
                )

                metadata = {}
                if json_result.returncode == 0:
                    try:
                        metadata = json.loads(json_result.stdout)
                    except json.JSONDecodeError:
                        pass

                content = result.stdout.strip()
                title = metadata.get("title", "")

                return {
                    "url": url,
                    "title": title,
                    "content": content,
                    "markdown": content,
                    "description": metadata.get("description", ""),
                    "domain": metadata.get("domain", ""),
                }

        except subprocess.TimeoutExpired:
            raise RuntimeError(f"Defuddle request timed out after {self.timeout} seconds")
        except FileNotFoundError:
            raise RuntimeError(
                "Node.js not found. Please install Node.js to use Defuddle."
            )


def url_to_markdown(
    url: str,
    timeout: int = 60,
    with_metadata: bool = False,
    debug: bool = False,
) -> Dict[str, Any]:
    """
    便捷函数：使用 Defuddle 将 URL 转换为 Markdown

    Args:
        url: 要提取的网页 URL
        timeout: 请求超时时间 (秒)
        with_metadata: 是否返回元数据
        debug: 是否启用调试模式

    Returns:
        包含 title, content, url 等字段的字典
    """
    client = DefuddleClient(timeout=timeout)
    return client.fetch(
        url=url,
        markdown=True,
        json_output=with_metadata,
        debug=debug,
    )


def main():
    """CLI entry point for testing."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Defuddle URL to Markdown - 免费无限制的网页内容提取"
    )
    parser.add_argument("url", help="要转换的 URL")
    parser.add_argument(
        "--json",
        action="store_true",
        help="JSON 格式输出（包含元数据）"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=60,
        help="请求超时时间 (秒)"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="启用调试模式"
    )

    args = parser.parse_args()

    try:
        result = url_to_markdown(
            url=args.url,
            timeout=args.timeout,
            with_metadata=args.json,
            debug=args.debug,
        )

        if args.json:
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            if result.get("title"):
                print(f"# {result['title']}")
                print()
            print(result.get("content", ""))

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
