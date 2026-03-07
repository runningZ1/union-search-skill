#!/usr/bin/env python3
"""
Defuddle 引擎

Defuddle 是备选引擎，本地运行、无速率限制，但需要 Node.js 依赖。
当 Jina AI 失败时自动使用。
"""

import json
import subprocess
import sys
from pathlib import Path
from typing import Optional, Dict, Any, List


class DefuddleEngine:
    """
    Defuddle CLI 引擎

    通过子进程调用 Node.js Defuddle CLI 进行网页内容提取。
    作为 Jina AI 的备选引擎使用。
    """

    def __init__(self, timeout: int = 60):
        """
        初始化 DefuddleEngine

        Args:
            timeout: 请求超时时间 (秒)
        """
        self.timeout = timeout
        # Defuddle CLI 路径 - 相对于 engines 目录
        self.defuddle_root = Path(__file__).parent / "defuddle-node"
        self.cli_path = str(self.defuddle_root / "dist" / "cli.js")

        # 验证 CLI 存在
        if not Path(self.cli_path).exists():
            raise RuntimeError(
                f"Defuddle CLI not found at {self.cli_path}. "
                "Please ensure Defuddle is properly installed."
            )

    def fetch(
        self,
        url: str,
        markdown: bool = True,
        json_output: bool = False,
        timeout: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        使用 Defuddle 提取网页内容

        Args:
            url: 要提取的网页 URL
            markdown: 是否输出 Markdown 格式
            json_output: 是否输出 JSON 格式（包含元数据）
            timeout: 请求超时时间 (秒)

        Returns:
            包含 title, content, url 等字段的字典
        """
        request_timeout = timeout or self.timeout

        # 构建命令
        cmd = ["node", self.cli_path, "parse", url]

        if markdown:
            cmd.append("--markdown")
        if json_output:
            cmd.append("--json")

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=request_timeout,
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
                    timeout=request_timeout,
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
            raise RuntimeError(f"Defuddle request timed out after {request_timeout} seconds")
        except FileNotFoundError:
            raise RuntimeError(
                "Node.js not found. Please install Node.js to use Defuddle."
            )

    def fetch_batch(
        self,
        urls: List[str],
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        批量获取多个 URL 的 Markdown 内容

        Args:
            urls: URL 列表
            **kwargs: fetch() 方法的其他参数

        Returns:
            结果列表
        """
        results = []
        for url in urls:
            try:
                result = self.fetch(url, **kwargs)
                results.append(result)
            except Exception as e:
                results.append({
                    "url": url,
                    "error": str(e),
                    "content": None,
                })
        return results
