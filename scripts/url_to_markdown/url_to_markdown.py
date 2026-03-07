#!/usr/bin/env python3
"""
URL to Markdown 模块

将网页URL转换为LLM友好的Markdown内容。
基于Jina AI Reader API实现。

API文档: https://jina.ai/reader

Version: 1.0.0
Author: Claude
"""

import os
import sys
import json
import argparse
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List, Union
from urllib.parse import urlparse

import requests
from dotenv import load_dotenv

# 版本信息
__version__ = "1.0.0"
__author__ = "Claude"

# 加载环境变量
script_dir = os.path.dirname(os.path.abspath(__file__))
skill_root = os.path.dirname(os.path.dirname(script_dir))
load_dotenv(os.path.join(skill_root, ".env"))

# Jina Reader API 基础URL
JINA_READER_BASE_URL = "https://r.jina.ai"


class UrlToMarkdown:
    """
    Jina Reader API 客户端

    将网页URL转换为Markdown格式。
    官方文档: https://jina.ai/reader
    """

    def __init__(self, api_key: Optional[str] = None, timeout: int = 30):
        """
        初始化UrlToMarkdown客户端

        Args:
            api_key: Jina API Key (可选，免费版不需要)
            timeout: 请求超时时间(秒)
        """
        self.api_key = api_key or os.getenv("JINA_API_KEY", "")
        self.timeout = timeout
        self.base_url = JINA_READER_BASE_URL

    def _build_headers(self, extra_headers: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        """构建请求头"""
        headers = {
            "Accept": "text/plain, text/markdown",
            "User-Agent": "Union-Search-Skill/1.0",
        }

        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        if extra_headers:
            headers.update(extra_headers)

        return headers

    def _validate_url(self, url: str) -> str:
        """验证并规范化URL"""
        if not url:
            raise ValueError("URL不能为空")

        # 如果URL没有scheme，添加https://
        parsed = urlparse(url)
        if not parsed.scheme:
            url = f"https://{url}"

        # 验证URL格式
        parsed = urlparse(url)
        if not parsed.netloc:
            raise ValueError(f"无效的URL: {url}")

        return url

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
        获取URL对应的Markdown内容

        Args:
            url: 要抓取的URL
            with_images: 是否包含图片摘要
            with_links: 是否包含链接摘要
            with_generated_alt: 是否生成图片alt文本 (需要VLM处理，较慢)
            target_selector: CSS选择器，指定要提取的内容区域
            wait_for_selector: 等待指定元素渲染完成
            timeout: 请求超时时间(秒)
            no_cache: 是否绕过缓存
            return_json: 是否返回JSON格式

        Returns:
            包含title, content, url等字段的字典
        """
        url = self._validate_url(url)
        request_timeout = timeout or self.timeout

        # 构建请求头
        extra_headers = {}
        if with_generated_alt:
            extra_headers["X-With-Generated-Alt"] = "true"
        if target_selector:
            extra_headers["X-Target-Selector"] = target_selector
        if wait_for_selector:
            extra_headers["X-Wait-For-Selector"] = wait_for_selector
        if no_cache:
            extra_headers["X-No-Cache"] = "true"

        # 设置Accept header
        if return_json:
            extra_headers["Accept"] = "application/json"
        else:
            extra_headers["Accept"] = "text/markdown"

        headers = self._build_headers(extra_headers)

        # 发送请求
        response = requests.get(
            f"{self.base_url}/{url}",
            headers=headers,
            timeout=request_timeout,
        )
        response.raise_for_status()

        if return_json:
            data = response.json()
            # Jina API返回的JSON格式
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

        # 解析响应
        content = response.text

        # 尝试从响应中提取标题(如果API返回了的话)
        title = None
        # Jina Reader API的markdown响应可能以标题开头
        lines = content.split("\n")
        if lines and lines[0].startswith("# "):
            title = lines[0][2:].strip()
            content = "\n".join(lines[1:]).strip()

        return {
            "url": url,
            "title": title or "",
            "content": content,
            "markdown": content,
        }

    def fetch_batch(
        self,
        urls: List[str],
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        批量获取多个URL的Markdown内容

        Args:
            urls: URL列表
            **kwargs: fetch()方法的其他参数

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
    便捷函数：直接将URL转换为Markdown字符串

    Args:
        url: 要抓取的URL
        with_images: 是否包含图片摘要
        with_links: 是否包含链接摘要
        with_generated_alt: 是否生成图片alt文本
        timeout: 请求超时时间

    Returns:
        Markdown格式的内容字符串
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
        description="URL to Markdown - 将网页URL转换为Markdown内容",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s https://example.com
  %(prog)s https://example.com --json
  %(prog)s https://example.com --with-images --save-response
  %(prog)s https://github.com --target-selector "article"
        """
    )
    parser.add_argument("url", help="要转换的URL")
    parser.add_argument("--json", action="store_true", help="JSON格式输出")
    parser.add_argument("--verbose", "-v", action="store_true", help="详细输出")
    parser.add_argument("--with-images", action="store_true", help="包含图片摘要")
    parser.add_argument("--with-links", action="store_true", help="包含链接摘要")
    parser.add_argument("--with-generated-alt", action="store_true", help="生成图片alt文本(较慢)")
    parser.add_argument("--target-selector", help="CSS选择器，指定要提取的内容区域")
    parser.add_argument("--wait-for-selector", help="等待指定元素渲染完成")
    parser.add_argument("--timeout", type=int, default=30, help="请求超时时间(秒)")
    parser.add_argument("--no-cache", action="store_true", help="绕过缓存")
    parser.add_argument("--save-response", action="store_true", help="保存响应到文件")
    parser.add_argument("--api-key", help="Jina API Key (可选)")

    args = parser.parse_args()

    try:
        client = UrlToMarkdown(api_key=args.api_key, timeout=args.timeout)

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
            print(f"\n响应已保存: {saved_file}", file=sys.stderr)

    except requests.exceptions.RequestException as e:
        print(f"网络错误: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"错误: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
