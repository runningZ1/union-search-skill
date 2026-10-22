#!/usr/bin/env python3
"""
Exa Search - 基于 Exa AI 的神经搜索

支持网页搜索、代码搜索、公司研究、人物搜索、深度研究等功能
"""

import os
import sys
import json
import argparse
import subprocess
import re
import shlex
from typing import Optional, Dict, Any, List


def run_mcporter(call_arg: str) -> Dict[str, Any]:
    """执行 mcporter 命令并返回结果"""
    try:
        # 需要用反斜杠转义内部双引号
        escaped_arg = call_arg.replace('"', '\\"')
        cmd_str = f'mcporter call "exa.{escaped_arg}"'

        result = subprocess.run(
            cmd_str,
            shell=True,
            capture_output=True,
            text=True,
            timeout=120
        )

        if result.returncode != 0:
            error_msg = result.stderr or result.stdout
            # 尝试解析 JSON 错误响应
            try:
                error_data = json.loads(error_msg)
                return {"error": error_data.get("error", error_data), "raw": error_msg}
            except:
                return {"error": error_msg, "raw": error_msg}

        # 解析输出
        output = result.stdout.strip()
        if not output:
            return {"error": "No output from mcporter", "raw": ""}

        # 尝试解析 JSON
        try:
            return json.loads(output)
        except:
            return {"raw": output}

    except subprocess.TimeoutExpired:
        return {"error": "Request timeout", "raw": ""}
    except Exception as e:
        return {"error": str(e), "raw": ""}


def search_web(query: str, num_results: int = 8, search_type: str = "auto") -> Dict[str, Any]:
    """网页搜索"""
    call_arg = f'web_search_exa(query: "{query}", numResults: {num_results}, type: "{search_type}")'
    return run_mcporter(call_arg)


def search_code(query: str, tokens: int = 5000) -> Dict[str, Any]:
    """代码搜索"""
    call_arg = f'get_code_context_exa(query: "{query}", tokensNum: {tokens})'
    return run_mcporter(call_arg)


def search_company(company_name: str, num_results: int = 5) -> Dict[str, Any]:
    """公司研究"""
    call_arg = f'company_research_exa(companyName: "{company_name}", numResults: {num_results})'
    return run_mcporter(call_arg)


def search_people(query: str, num_results: int = 5) -> Dict[str, Any]:
    """人物搜索"""
    call_arg = f'people_search_exa(query: "{query}", numResults: {num_results})'
    return run_mcporter(call_arg)


def crawl_url(url: str, max_chars: int = 3000) -> Dict[str, Any]:
    """网页抓取"""
    call_arg = f'crawling_exa(url: "{url}", maxCharacters: {max_chars})'
    return run_mcporter(call_arg)


def deep_research(instructions: str, model: str = "exa-research-fast") -> Dict[str, Any]:
    """启动深度研究"""
    call_arg = f'deep_researcher_start(instructions: "{instructions}", model: "{model}")'
    return run_mcporter(call_arg)


def check_research(research_id: str) -> Dict[str, Any]:
    """检查深度研究结果"""
    call_arg = f'deep_researcher_check(researchId: "{research_id}")'
    return run_mcporter(call_arg)


def format_results(search_type: str, data: Dict[str, Any]) -> str:
    """格式化搜索结果"""
    output = []

    if "error" in data:
        output.append(f"❌ 错误: {data.get('error', 'Unknown error')}")
        if "raw" in data and data.get("raw"):
            output.append(f"   原始输出: {data['raw'][:200]}")
        return "\n".join(output)

    # 处理不同类型的搜索结果
    if search_type == "web":
        results = data.get("results", [])
        if not results and "raw" in data:
            # 尝试从原始输出中提取
            output.append(f"🔍 搜索结果:")
            output.append(data.get("raw", ""))
            return "\n".join(output)

        output.append(f"🔍 找到 {len(results)} 条结果:")
        output.append("")

        for i, item in enumerate(results, 1):
            title = item.get("title", "N/A")
            url = item.get("url", "N/A")
            content = item.get("content", "")[:200] if item.get("content") else ""

            output.append(f"[{i}] {title}")
            output.append(f"    🔗 {url}")
            if content:
                output.append(f"    📝 {content}...")
            output.append("")

    elif search_type == "code":
        results = data.get("results", [])
        output.append(f"💻 找到 {len(results)} 个代码结果:")
        output.append("")

        for i, item in enumerate(results, 1):
            title = item.get("title", "N/A")
            url = item.get("url", "N/A")
            content = item.get("content", "")[:300] if item.get("content") else ""

            output.append(f"[{i}] {title}")
            output.append(f"    🔗 {url}")
            if content:
                output.append(f"    📝 {content}...")
            output.append("")

    elif search_type == "company":
        results = data.get("results", [])
        output.append(f"🏢 找到 {len(results)} 条公司信息:")
        output.append("")

        for i, item in enumerate(results, 1):
            title = item.get("title", "N/A")
            url = item.get("url", "N/A")
            content = item.get("content", "")[:200] if item.get("content") else ""

            output.append(f"[{i}] {title}")
            output.append(f"    🔗 {url}")
            if content:
                output.append(f"    📝 {content}")
            output.append("")

    elif search_type == "people":
        results = data.get("results", [])
        output.append(f"👤 找到 {len(results)} 个人员结果:")
        output.append("")

        for i, item in enumerate(results, 1):
            title = item.get("title", "N/A")
            url = item.get("url", "N/A")
            content = item.get("content", "")[:200] if item.get("content") else ""

            output.append(f"[{i}] {title}")
            output.append(f"    🔗 {url}")
            if content:
                output.append(f"    📝 {content}")
            output.append("")

    elif search_type == "crawl":
        content = data.get("content", "")
        output.append("📄 网页内容:")
        output.append("")
        if content:
            output.append(content[:5000])
        else:
            output.append(data.get("raw", "无内容"))

    elif search_type == "deep":
        if "raw" in data:
            output.append("🔬 深度研究已启动")
            output.append("")
            output.append(data["raw"])
        else:
            output.append("🔬 深度研究结果:")
            output.append("")
            output.append(json.dumps(data, indent=2, ensure_ascii=False))

    elif search_type == "check":
        if "raw" in data:
            output.append("📊 研究状态:")
            output.append(data["raw"])
        else:
            output.append("📊 研究结果:")
            output.append(json.dumps(data, indent=2, ensure_ascii=False))

    return "\n".join(output)


def main():
    parser = argparse.ArgumentParser(description="Exa AI 搜索")
    parser.add_argument("type", choices=["web", "code", "company", "people", "crawl", "deep", "check"],
                        help="搜索类型")
    parser.add_argument("query", help="搜索关键词/URL/研究ID")
    parser.add_argument("--max-results", type=int, default=8, help="最大结果数量")
    parser.add_argument("--tokens", type=int, default=5000, help="代码搜索的 token 数量")
    parser.add_argument("--max-chars", type=int, default=3000, help="网页抓取的最大字符数")
    parser.add_argument("--search-type", choices=["auto", "fast", "deep"], default="auto",
                        help="网页搜索类型")
    parser.add_argument("--model", choices=["exa-research-fast", "exa-research", "exa-research-pro"],
                        default="exa-research-fast", help="深度研究模型")
    parser.add_argument("--json", action="store_true", help="JSON 格式输出")
    parser.add_argument("--pretty", action="store_true", help="格式化 JSON 输出")

    args = parser.parse_args()

    try:
        if args.type == "web":
            result = search_web(args.query, args.max_results, args.search_type)
        elif args.type == "code":
            result = search_code(args.query, args.tokens)
        elif args.type == "company":
            result = search_company(args.query, args.max_results)
        elif args.type == "people":
            result = search_people(args.query, args.max_results)
        elif args.type == "crawl":
            result = crawl_url(args.query, args.max_chars)
        elif args.type == "deep":
            result = deep_research(args.query, args.model)
        elif args.type == "check":
            result = check_research(args.query)
        else:
            print(f"错误: 未知的搜索类型 {args.type}", file=sys.stderr)
            sys.exit(1)

        if args.json:
            if args.pretty:
                print(json.dumps(result, indent=2, ensure_ascii=False))
            else:
                print(json.dumps(result, ensure_ascii=False))
        else:
            print(format_results(args.type, result))

    except Exception as e:
        print(f"错误: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
