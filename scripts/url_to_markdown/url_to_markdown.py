#!/usr/bin/env python3
"""
URL to Markdown 模块 - 双引擎版本

将网页 URL 转换为 LLM 友好的 Markdown 内容。

架构说明：
- 首选引擎：Jina AI Reader API (快速、稳定、免费)
- 备选引擎：Defuddle (本地运行、无速率限制、需 Node.js)
- 自动降级：当 Jina 失败时自动切换到 Defuddle

Version: 2.0.0
Author: Claude
"""

import os
import sys
import json
import argparse
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
from urllib.parse import urlparse

import requests
from dotenv import load_dotenv

# 版本信息
__version__ = "2.0.0"
__author__ = "Claude"

# 加载环境变量
script_dir = os.path.dirname(os.path.abspath(__file__))
skill_root = os.path.dirname(os.path.dirname(script_dir))
load_dotenv(os.path.join(skill_root, ".env"))

# Jina Reader API 基础 URL
JINA_READER_BASE_URL = "https://r.jina.ai"

# Defuddle CLI 路径
DEFUDDLE_ROOT = Path(__file__).parent / "engines" / "defuddle-node"
DEFUDDLE_CLI = DEFUDDLE_ROOT / "dist" / "cli.js"


class UrlToMarkdown:
    """
    双引擎 URL 转 Markdown 客户端

    优先使用 Jina AI API（快速、无本地依赖），
    当 Jina 失败时自动切换到 Defuddle（本地运行、无速率限制）。
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        timeout: int = 30,
        prefer_engine: str = "auto",
        enable_fallback: bool = True,
    ):
        """
        初始化 UrlToMarkdown 客户端

        Args:
            api_key: Jina API Key (可选，免费版不需要)
            timeout: 请求超时时间 (秒)
            prefer_engine: 首选引擎 ("jina", "defuddle", "auto")
            enable_fallback: 是否启用自动降级
        """
        self.api_key = api_key or os.getenv("JINA_API_KEY", "")
        self.timeout = timeout
        self.base_url = JINA_READER_BASE_URL
        self.prefer_engine = prefer_engine
        self.enable_fallback = enable_fallback

    def _build_jina_headers(self, extra_headers: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        """构建 Jina 请求头"""
        headers = {
            "Accept": "text/plain, text/markdown",
            "User-Agent": "Union-Search-Skill/2.0",
        }

        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        if extra_headers:
            headers.update(extra_headers)

        return headers

    def _validate_url(self, url: str) -> str:
        """验证并规范化 URL"""
        if not url:
            raise ValueError("URL 不能为空")

        # 如果 URL 没有 scheme，添加 https://
        parsed = urlparse(url)
        if not parsed.scheme:
            url = f"https://{url}"

        # 验证 URL 格式
        parsed = urlparse(url)
        if not parsed.netloc:
            raise ValueError(f"无效的 URL: {url}")

        return url

    def _fetch_with_jina(
        self,
        url: str,
        extra_headers: Dict[str, str],
        return_json: bool,
        timeout: int,
    ) -> Dict[str, Any]:
        """使用 Jina AI 获取 URL 对应的 Markdown 内容"""
        headers = self._build_jina_headers(extra_headers)

        response = requests.get(
            f"{self.base_url}/{url}",
            headers=headers,
            timeout=timeout,
        )
        response.raise_for_status()

        if return_json:
            data = response.json()
            if isinstance(data, dict) and "data" in data:
                return {
                    "url": data.get("data", {}).get("url", url),
                    "title": data.get("data", {}).get("title", ""),
                    "content": data.get("data", {}).get("content", ""),
                    "description": data.get("data", {}).get("description", ""),
                    "markdown": data.get("data", {}).get("content", ""),
                    "metadata": data.get("data", {}).get("metadata", {}),
                    "usage": data.get("data", {}).get("usage", {}),
                    "warning": data.get("data", {}).get("warning", ""),
                }
            return data

        content = response.text

        # 尝试从响应中提取标题
        title = ""
        lines = content.split("\n")
        if lines and lines[0].startswith("# "):
            title = lines[0][2:].strip()
            content = "\n".join(lines[1:]).strip()

        return {
            "url": url,
            "title": title,
            "content": content,
            "markdown": content,
        }

    def _fetch_with_defuddle(
        self,
        url: str,
        return_json: bool,
        timeout: int,
    ) -> Dict[str, Any]:
        """使用 Defuddle 获取 URL 对应的 Markdown 内容"""
        if not DEFUDDLE_CLI.exists():
            raise RuntimeError(
                f"Defuddle CLI not found at {DEFUDDLE_CLI}. "
                "Please ensure Defuddle is properly installed."
            )

        cmd = ["node", str(DEFUDDLE_CLI), "parse", url]
        cmd.append("--markdown")
        if return_json:
            cmd.append("--json")

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )

        if result.returncode != 0:
            error_msg = result.stderr.strip() or f"Exit code: {result.returncode}"
            raise RuntimeError(f"Defuddle failed: {error_msg}")

        if return_json:
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
            cmd_with_json = ["node", str(DEFUDDLE_CLI), "parse", url, "--json"]
            json_result = subprocess.run(
                cmd_with_json,
                capture_output=True,
                text=True,
                timeout=timeout,
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

    def fetch(
        self,
        url: str,
        with_images: bool = False,
        with_links: bool = False,
        with_generated_alt: bool = False,
        target_selector: Optional[str] = None,
        wait_for_selector: Optional[str] = None,
        timeout: Optional[int] = None,
        no_cache: bool = False,
        return_json: bool = False,
    ) -> Dict[str, Any]:
        """
        获取 URL 对应的 Markdown 内容（双引擎，自动降级）

        Args:
            url: 要抓取的 URL
            with_images: 是否包含图片摘要
            with_links: 是否包含链接摘要
            with_generated_alt: 是否生成图片 alt 文本
            target_selector: CSS 选择器，指定要提取的内容区域
            wait_for_selector: 等待指定元素渲染完成
            timeout: 请求超时时间 (秒)
            no_cache: 是否绕过缓存
            return_json: 是否返回 JSON 格式

        Returns:
            包含 title, content, url 等字段的字典
        """
        url = self._validate_url(url)
        request_timeout = timeout or self.timeout

        # 构建 Jina 请求头
        extra_headers = {}
        if with_generated_alt:
            extra_headers["X-With-Generated-Alt"] = "true"
        if target_selector:
            extra_headers["X-Target-Selector"] = target_selector
        if wait_for_selector:
            extra_headers["X-Wait-For-Selector"] = wait_for_selector
        if no_cache:
            extra_headers["X-No-Cache"] = "true"

        # 确定引擎顺序
        if self.prefer_engine == "defuddle":
            if self.enable_fallback:
                engines = [("defuddle", self._fetch_with_defuddle), ("jina", self._fetch_with_jina)]
            else:
                engines = [("defuddle", self._fetch_with_defuddle)]
        else:  # auto or jina - 优先 Jina
            if self.enable_fallback:
                engines = [("jina", lambda u, rj, t: self._fetch_with_jina(u, extra_headers, rj, t)), ("defuddle", self._fetch_with_defuddle)]
            else:
                engines = [("jina", lambda u, rj, t: self._fetch_with_jina(u, extra_headers, rj, t))]

        last_error = None
        engine_used = "unknown"

        for engine_name, fetch_func in engines:
            try:
                if engine_name == "jina":
                    result = fetch_func(url, return_json, request_timeout)
                else:
                    result = fetch_func(url, return_json, request_timeout)

                # 添加引擎使用信息
                result["_engine_used"] = engine_name
                return result

            except Exception as e:
                last_error = e
                # 继续尝试下一个引擎
                continue

        # 所有引擎都失败
        raise RuntimeError(f"All engines failed. Last error: {last_error}")

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


def fetch_url_as_markdown(
    url: str,
    with_images: bool = False,
    with_links: bool = False,
    with_generated_alt: bool = False,
    timeout: int = 30,
) -> str:
    """
    便捷函数：直接将 URL 转换为 Markdown 字符串

    Args:
        url: 要抓取的 URL
        with_images: 是否包含图片摘要
        with_links: 是否包含链接摘要
        with_generated_alt: 是否生成图片 alt 文本
        timeout: 请求超时时间

    Returns:
        Markdown 格式的内容字符串
    """
    client = UrlToMarkdown(timeout=timeout)
    result = client.fetch(
        url,
        with_images=with_images,
        with_links=with_links,
        with_generated_alt=with_generated_alt,
    )
    return result.get("content", "")


def save_response(url: str, output_data: Dict[str, Any]) -> str:
    """保存响应到文件"""
    responses_dir = Path(__file__).parent / "responses"
    responses_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    parsed = urlparse(url)
    safe_name = parsed.netloc or "url"

    filename = responses_dir / f"{timestamp}_{safe_name}.json"

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    return str(filename)


def format_result(result: Dict[str, Any], verbose: bool = False) -> str:
    """格式化输出结果"""
    output = []

    if result.get("title"):
        output.append(f"# {result['title']}")
        output.append("")

    if result.get("url"):
        output.append(f"**Source**: {result['url']}")
        output.append("")

    # 显示使用的引擎
    if result.get("_engine_used"):
        output.append(f"**Engine**: {result['_engine_used']}")
        output.append("")

    content = result.get("content", "")
    if verbose:
        output.append(f"**Length**: {len(content)} characters")
        output.append("")

    output.append("---")
    output.append("")
    output.append(content)

    return "\n".join(output)


def main():
    parser = argparse.ArgumentParser(
        description="URL to Markdown - 将网页 URL 转换为 Markdown 内容（双引擎，自动降级）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s https://example.com
  %(prog)s https://example.com --json
  %(prog)s https://example.com --with-images --save-response
  %(prog)s https://github.com --target-selector "article"
        """
    )
    parser.add_argument("url", help="要转换的 URL")
    parser.add_argument("--json", action="store_true", help="JSON 格式输出")
    parser.add_argument("--verbose", "-v", action="store_true", help="详细输出")
    parser.add_argument("--with-images", action="store_true", help="包含图片摘要")
    parser.add_argument("--with-links", action="store_true", help="包含链接摘要")
    parser.add_argument("--with-generated-alt", action="store_true", help="生成图片 alt 文本 (较慢)")
    parser.add_argument("--target-selector", help="CSS 选择器，指定要提取的内容区域")
    parser.add_argument("--wait-for-selector", help="等待指定元素渲染完成")
    parser.add_argument("--timeout", type=int, default=30, help="请求超时时间 (秒)")
    parser.add_argument("--no-cache", action="store_true", help="绕过缓存")
    parser.add_argument("--save-response", action="store_true", help="保存响应到文件")
    parser.add_argument("--api-key", help="Jina API Key (可选)")
    parser.add_argument("--prefer-engine", choices=["auto", "jina", "defuddle"], default="auto", help="首选引擎")
    parser.add_argument("--no-fallback", action="store_true", help="禁用自动降级")

    args = parser.parse_args()

    try:
        client = UrlToMarkdown(
            api_key=args.api_key,
            timeout=args.timeout,
            prefer_engine=args.prefer_engine,
            enable_fallback=not args.no_fallback,
        )

        result = client.fetch(
            url=args.url,
            with_images=args.with_images,
            with_links=args.with_links,
            with_generated_alt=args.with_generated_alt,
            target_selector=args.target_selector,
            wait_for_selector=args.wait_for_selector,
            no_cache=args.no_cache,
            return_json=args.json,
        )

        output_data = {
            "url": args.url,
            "result": result,
        }

        # 保存响应
        saved_file = None
        if args.save_response:
            saved_file = save_response(args.url, output_data)

        # 输出
        if args.json:
            print(json.dumps(output_data, indent=2, ensure_ascii=False))
        else:
            print(format_result(result, verbose=args.verbose))

        if saved_file:
            print(f"\n响应已保存：{saved_file}", file=sys.stderr)

        # 提示使用的引擎
        if not args.json:
            print(f"\n[使用引擎：{result.get('_engine_used', 'unknown')}]", file=sys.stderr)

    except requests.exceptions.RequestException as e:
        print(f"网络错误：{e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"错误：{e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
