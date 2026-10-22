#!/usr/bin/env python3
"""
GitHub Search CLI - Search GitHub repositories, code, and issues

集成自 github-search-skill，遵循 union-search-skill 的代码风格
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
import requests


# =============================================================================
# Exceptions
# =============================================================================

class GitHubSearchError(Exception):
    """Base exception for GitHub Search errors"""
    pass


class AuthenticationError(GitHubSearchError):
    """Raised when authentication fails"""
    pass


class RateLimitError(GitHubSearchError):
    """Raised when rate limit is exceeded"""
    pass


class ValidationError(GitHubSearchError):
    """Raised when query validation fails"""
    pass


# =============================================================================
# GitHub Search Client
# =============================================================================

class GitHubSearchClient:
    """Client for interacting with GitHub Search API"""

    BASE_URL = "https://api.github.com"
    API_VERSION = "2022-11-28"

    def __init__(self, token: Optional[str] = None):
        """
        Initialize GitHub Search Client

        Args:
            token: GitHub Personal Access Token (optional but recommended)
        """
        self.token = token
        self.session = requests.Session()

        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "union-search-skill/1.0",
        }

        if token:
            headers["Authorization"] = f"Bearer {token}"
            headers["X-GitHub-Api-Version"] = self.API_VERSION

        self.session.headers.update(headers)

    def search_repositories(
        self,
        query: str,
        sort: Optional[str] = None,
        order: str = "desc",
        per_page: int = 30,
        max_results: int = 30,
    ) -> Dict[str, Any]:
        """Search for repositories"""
        return self._search(
            endpoint_path="repositories",
            query=query,
            sort=sort,
            order=order,
            per_page=per_page,
            max_results=max_results
        )

    def search_code(
        self,
        query: str,
        sort: Optional[str] = None,
        order: str = "desc",
        per_page: int = 30,
        max_results: int = 30,
    ) -> Dict[str, Any]:
        """Search for code"""
        return self._search(
            endpoint_path="code",
            query=query,
            sort=sort,
            order=order,
            per_page=per_page,
            max_results=max_results
        )

    def search_issues(
        self,
        query: str,
        sort: Optional[str] = None,
        order: str = "desc",
        per_page: int = 30,
        max_results: int = 30,
    ) -> Dict[str, Any]:
        """Search for issues and pull requests"""
        return self._search(
            endpoint_path="issues",
            query=query,
            sort=sort,
            order=order,
            per_page=per_page,
            max_results=max_results
        )

    def _search(
        self,
        endpoint_path: str,
        query: str,
        sort: Optional[str],
        order: str,
        per_page: int,
        max_results: int
    ) -> Dict[str, Any]:
        """Common search method for all search types"""
        endpoint = f"{self.BASE_URL}/search/{endpoint_path}"
        params = {"q": query, "order": order, "per_page": min(per_page, 100)}
        if sort:
            params["sort"] = sort
        return self._search_with_pagination(endpoint, params, max_results)

    def get_rate_limit(self) -> Dict[str, Any]:
        """Get current rate limit status"""
        try:
            response = self.session.get(f"{self.BASE_URL}/rate_limit", timeout=30)
            response.raise_for_status()
            data = response.json()

            result = {}
            for resource_name in ["search", "core"]:
                resource = data["resources"][resource_name]
                result[resource_name] = {
                    "limit": resource["limit"],
                    "remaining": resource["remaining"],
                    "reset": datetime.fromtimestamp(resource["reset"]),
                    "used": resource["used"],
                }
            return result
        except requests.exceptions.RequestException as e:
            raise GitHubSearchError(f"Failed to get rate limit: {str(e)}")

    def _search_with_pagination(
        self, endpoint: str, params: Dict[str, Any], max_results: int
    ) -> Dict[str, Any]:
        """Perform search with automatic pagination"""
        page = 1
        all_items = []
        total_count = 0
        incomplete_results = False

        max_results = min(max_results, 1000)

        while len(all_items) < max_results and page <= 10:
            params["page"] = page
            params["per_page"] = min(100, max_results - len(all_items))

            response = self._make_request(endpoint, params)
            data = self._handle_response(response)

            items = data.get("items", [])
            all_items.extend(items)
            total_count = data.get("total_count", 0)
            incomplete_results = data.get("incomplete_results", False)

            if len(items) < params["per_page"] or len(all_items) >= total_count:
                break

            page += 1

        return {
            "total_count": total_count,
            "incomplete_results": incomplete_results,
            "items": all_items,
        }

    def _make_request(self, endpoint: str, params: Dict[str, Any]) -> requests.Response:
        """Make HTTP request to GitHub API"""
        try:
            response = self.session.get(endpoint, params=params, timeout=30)
            return response
        except requests.exceptions.Timeout:
            raise GitHubSearchError("Request timed out")
        except requests.exceptions.ConnectionError:
            raise GitHubSearchError("Connection error. Please check your internet connection.")
        except requests.exceptions.RequestException as e:
            raise GitHubSearchError(f"Request failed: {str(e)}")

    def _handle_response(self, response: requests.Response) -> Dict[str, Any]:
        """Handle API response and errors"""
        if response.status_code == 200:
            return response.json()

        message = self._extract_error_message(response)

        error_map = {
            401: (AuthenticationError, "Authentication failed"),
            422: (ValidationError, "Query validation failed"),
        }

        if response.status_code in error_map:
            error_class, prefix = error_map[response.status_code]
            raise error_class(f"{prefix}: {message}")

        if response.status_code == 403:
            if "rate limit" in message.lower():
                raise RateLimitError(f"Rate limit exceeded: {message}")
            raise GitHubSearchError(f"Forbidden: {message}")

        raise GitHubSearchError(f"API error ({response.status_code}): {message}")

    def _extract_error_message(self, response: requests.Response) -> str:
        """Extract error message from response"""
        try:
            error_data = response.json()
            return error_data.get("message", "Unknown error")
        except ValueError:
            return response.text or f"HTTP {response.status_code}"


# =============================================================================
# Output Formatters
# =============================================================================

def format_table(results: Dict[str, Any], resource_type: str) -> str:
    """Format results as a text table"""
    items = results.get("items", [])
    total_count = results.get("total_count", 0)

    if not items:
        return f"No results found. Total count: {total_count}"

    lines = [
        "=" * 80,
        f"GitHub {resource_type.capitalize()} Results",
        f"Showing {len(items)} of {total_count} results",
        "=" * 80,
        ""
    ]

    formatter_map = {
        "repositories": _format_repository_item,
        "code": _format_code_item,
        "issues": _format_issue_item,
    }

    formatter = formatter_map.get(resource_type)
    if formatter:
        for item in items:
            lines.extend(formatter(item))

    return "\n".join(lines)


def _format_repository_item(item: Dict[str, Any]) -> List[str]:
    """Format a single repository item"""
    name = item.get("full_name", "N/A")
    stars = item.get("stargazers_count", 0)
    forks = item.get("forks_count", 0)
    language = item.get("language") or "N/A"
    description = item.get("description") or "No description"
    url = item.get("html_url", "")

    return [
        f"📦 {name}",
        f"   ⭐ {stars} | 🍴 {forks} | 💻 {language}",
        f"   📝 {description}",
        f"   🔗 {url}",
        ""
    ]


def _format_code_item(item: Dict[str, Any]) -> List[str]:
    """Format a single code item"""
    repo = item.get("repository", {})
    repo_name = repo.get("full_name", "N/A")
    file_path = item.get("path", "N/A")
    url = item.get("html_url", "")

    return [
        f"📄 {repo_name}",
        f"   📁 {file_path}",
        f"   🔗 {url}",
        ""
    ]


def _format_issue_item(item: Dict[str, Any]) -> List[str]:
    """Format a single issue/PR item"""
    number = item.get("number", "N/A")
    title = item.get("title", "N/A")
    state = item.get("state", "N/A")
    comments = item.get("comments", 0)
    user = item.get("user", {})
    author = user.get("login", "N/A")
    url = item.get("html_url", "")
    item_type = "PR" if "pull_request" in item else "Issue"

    state_emoji = "🟢" if state == "open" else "🔴"
    return [
        f"{state_emoji} #{number}: {title}",
        f"   📌 {item_type} | 👤 @{author} | 💬 {comments} comments",
        f"   🔗 {url}",
        ""
    ]


def format_json(results: Dict[str, Any]) -> str:
    """Format results as JSON"""
    return json.dumps(results, indent=2, ensure_ascii=False)


def format_markdown(results: Dict[str, Any], resource_type: str) -> str:
    """Format results as Markdown"""
    items = results.get("items", [])
    total_count = results.get("total_count", 0)

    if not items:
        return f"# GitHub Search Results\n\nNo results found. Total count: {total_count}"

    lines = [
        "# GitHub Search Results\n",
        f"**Showing {len(items)} of {total_count} results**\n"
    ]

    formatter_map = {
        "repositories": ("## Repositories\n", _format_repository_markdown),
        "code": ("## Code Files\n", _format_code_markdown),
        "issues": ("## Issues & Pull Requests\n", _format_issue_markdown),
    }

    if resource_type in formatter_map:
        header, formatter = formatter_map[resource_type]
        lines.append(header)
        for item in items:
            lines.extend(formatter(item))

    return "\n".join(lines)


def _format_repository_markdown(item: Dict[str, Any]) -> List[str]:
    """Format a single repository item as Markdown"""
    name = item.get("full_name", "N/A")
    stars = item.get("stargazers_count", 0)
    forks = item.get("forks_count", 0)
    language = item.get("language") or "N/A"
    description = item.get("description") or "No description"
    url = item.get("html_url", "")

    return [
        f"### [{name}]({url})",
        f"⭐ {stars} | 🍴 {forks} | 💻 {language}",
        f"{description}\n"
    ]


def _format_code_markdown(item: Dict[str, Any]) -> List[str]:
    """Format a single code item as Markdown"""
    repo = item.get("repository", {})
    repo_name = repo.get("full_name", "N/A")
    file_path = item.get("path", "N/A")
    url = item.get("html_url", "")

    return [
        f"### {repo_name}",
        f"**File:** `{file_path}`",
        f"**URL:** {url}\n"
    ]


def _format_issue_markdown(item: Dict[str, Any]) -> List[str]:
    """Format a single issue/PR item as Markdown"""
    number = item.get("number", "N/A")
    title = item.get("title", "N/A")
    state = item.get("state", "N/A")
    comments = item.get("comments", 0)
    user = item.get("user", {})
    author = user.get("login", "N/A")
    url = item.get("html_url", "")
    item_type = "Pull Request" if "pull_request" in item else "Issue"

    state_emoji = "🟢" if state == "open" else "🔴"
    return [
        f"### {state_emoji} #{number}: {title}",
        f"**Type:** {item_type} | **Author:** @{author} | **Comments:** {comments}",
        f"**URL:** {url}\n"
    ]


def format_rate_limit(rate_limit_data: Dict[str, Any]) -> str:
    """Format rate limit information for display"""
    lines = [
        "=" * 70,
        "GitHub API Rate Limit Status",
        "=" * 70,
        ""
    ]

    for resource_name, resource_data in rate_limit_data.items():
        limit = resource_data.get("limit", "N/A")
        used = resource_data.get("used", "N/A")
        remaining = resource_data.get("remaining", "N/A")
        reset_time = resource_data.get("reset")
        reset_str = reset_time.strftime("%Y-%m-%d %H:%M:%S") if reset_time else "N/A"

        lines.extend([
            f"{resource_name.capitalize()}:",
            f"  Limit:     {limit}",
            f"  Used:      {used}",
            f"  Remaining: {remaining}",
            f"  Resets At: {reset_str}",
            ""
        ])

    return "\n".join(lines)


# =============================================================================
# Response Archiving
# =============================================================================

def save_raw_response(data: Dict[str, Any], response_type: str, responses_dir: Path) -> str:
    """Save raw API response to file"""
    responses_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}_{response_type}.json"
    filepath = responses_dir / filename

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    return str(filepath)


# =============================================================================
# Query Builder
# =============================================================================

def build_query(base_query: str, **filters) -> str:
    """Build GitHub search query from base query and filters"""
    query_parts = [base_query]

    for key, value in filters.items():
        if value is None:
            continue

        value_str = str(value)
        if ' ' in value_str:
            query_parts.append(f'{key}:"{value_str}"')
        else:
            query_parts.append(f'{key}:{value_str}')

    return ' '.join(query_parts)


# =============================================================================
# CLI Main
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description='GitHub Search CLI - Search repositories, code, and issues',
        formatter_class=argparse.RawTextHelpFormatter
    )

    # Global options
    parser.add_argument('--token', help='GitHub Personal Access Token (或使用 GITHUB_TOKEN 环境变量)')

    subparsers = parser.add_subparsers(dest='command', help='搜索命令')

    # Common arguments for all search commands
    common_parser = argparse.ArgumentParser(add_help=False)
    common_parser.add_argument('--format', choices=['text', 'json', 'markdown'], default='text',
                               help='输出格式 (默认: text)')
    common_parser.add_argument('--output', '-o', help='输出文件路径')
    common_parser.add_argument('--save-raw', action='store_true',
                               help='保存原始响应到 responses/ 目录')

    # Repository search
    repo_parser = subparsers.add_parser('repo', parents=[common_parser], help='搜索仓库')
    repo_parser.add_argument('query', help='搜索关键词')
    repo_parser.add_argument('--sort', choices=['stars', 'forks', 'help-wanted-issues', 'updated'],
                            help='排序字段')
    repo_parser.add_argument('--order', choices=['asc', 'desc'], default='desc',
                            help='排序顺序 (默认: desc)')
    repo_parser.add_argument('--limit', type=int, default=30,
                            help='最大结果数 (默认: 30, 最大: 1000)')
    repo_parser.add_argument('--language', help='按编程语言筛选')
    repo_parser.add_argument('--user', help='按用户/组织筛选')
    repo_parser.add_argument('--stars', help='按星标数筛选 (例: ">1000", "100..500")')
    repo_parser.add_argument('--forks', help='按分支数筛选')
    repo_parser.add_argument('--topic', help='按主题筛选')
    repo_parser.add_argument('--license', help='按许可证筛选 (例: "mit", "apache-2.0")')
    repo_parser.add_argument('--created', help='按创建日期筛选 (例: ">2020-01-01")')
    repo_parser.add_argument('--pushed', help='按最后推送日期筛选')
    repo_parser.add_argument('--archived', choices=['true', 'false'],
                            help='按归档状态筛选')

    # Code search
    code_parser = subparsers.add_parser('code', parents=[common_parser], help='搜索代码')
    code_parser.add_argument('query', help='搜索关键词')
    code_parser.add_argument('--sort', choices=['indexed'],
                            help='排序字段 (仅 "indexed" 可用)')
    code_parser.add_argument('--order', choices=['asc', 'desc'], default='desc',
                            help='排序顺序 (默认: desc)')
    code_parser.add_argument('--limit', type=int, default=30,
                            help='最大结果数 (默认: 30, 最大: 1000)')
    code_parser.add_argument('--language', help='按编程语言筛选')
    code_parser.add_argument('--repo', help='按仓库筛选 (格式: owner/repo)')
    code_parser.add_argument('--user', help='按用户/组织筛选')
    code_parser.add_argument('--path', help='按文件路径筛选')
    code_parser.add_argument('--extension', help='按文件扩展名筛选 (例: "js", "py")')

    # Issue search
    issue_parser = subparsers.add_parser('issue', parents=[common_parser], help='搜索问题和 PR')
    issue_parser.add_argument('query', help='搜索关键词')
    issue_parser.add_argument('--sort', choices=['comments', 'reactions', 'interactions', 'created', 'updated'],
                             help='排序字段')
    issue_parser.add_argument('--order', choices=['asc', 'desc'], default='desc',
                             help='排序顺序 (默认: desc)')
    issue_parser.add_argument('--limit', type=int, default=30,
                             help='最大结果数 (默认: 30, 最大: 1000)')
    issue_parser.add_argument('--repo', help='按仓库筛选 (格式: owner/repo)')
    issue_parser.add_argument('--user', help='按用户/组织筛选')
    issue_parser.add_argument('--state', choices=['open', 'closed'],
                             help='按状态筛选')
    issue_parser.add_argument('--author', help='按作者筛选')
    issue_parser.add_argument('--assignee', help='按受让人筛选')
    issue_parser.add_argument('--label', help='按标签筛选')
    issue_parser.add_argument('--milestone', help='按里程碑筛选')
    issue_parser.add_argument('--is-pr', action='store_true',
                             help='仅显示 Pull Request')
    issue_parser.add_argument('--is-issue', action='store_true',
                             help='仅显示 Issue')
    issue_parser.add_argument('--created', help='按创建日期筛选 (例: ">2020-01-01")')
    issue_parser.add_argument('--updated', help='按更新日期筛选')

    # Rate limit check
    subparsers.add_parser('rate-limit', help='检查 API 速率限制')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # Get token from argument or environment
    token = args.token or os.environ.get('GITHUB_TOKEN')

    # Initialize client
    client = GitHubSearchClient(token)

    try:
        if args.command == 'rate-limit':
            rate_limit_data = client.get_rate_limit()
            print(format_rate_limit(rate_limit_data))
            return 0

        results, resource_type = _execute_search_command(client, args)

        if args.save_raw:
            _save_response(results, args.command)

        output = _format_output(results, resource_type, args.format)
        _write_output(output, args.output)

        return 0

    except GitHubSearchError as e:
        print(f"错误: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"未知错误: {e}", file=sys.stderr)
        return 1


def _execute_search_command(client: GitHubSearchClient, args) -> tuple[Dict[str, Any], str]:
    """Execute search command based on args"""
    command_config = {
        'repo': {
            'method': client.search_repositories,
            'resource_type': 'repositories',
            'filters': ['language', 'user', 'stars', 'forks', 'topic', 'license', 'created', 'pushed', 'archived']
        },
        'code': {
            'method': client.search_code,
            'resource_type': 'code',
            'filters': ['language', 'repo', 'user', 'path', 'extension']
        },
        'issue': {
            'method': client.search_issues,
            'resource_type': 'issues',
            'filters': ['repo', 'user', 'state', 'author', 'assignee', 'label', 'milestone', 'created', 'updated']
        }
    }

    config = command_config[args.command]
    filters = {key: getattr(args, key, None) for key in config['filters']}

    if args.command == 'issue':
        if args.is_pr:
            filters['type'] = 'pr'
        elif args.is_issue:
            filters['type'] = 'issue'
        else:
            filters['type'] = 'issue'

    query = build_query(args.query, **filters)
    results = config['method'](
        query=query,
        sort=args.sort,
        order=args.order,
        max_results=args.limit
    )

    return results, config['resource_type']


def _save_response(results: Dict[str, Any], command: str):
    """Save raw API response to file"""
    script_dir = Path(__file__).parent.parent
    responses_dir = script_dir / 'responses'
    filepath = save_raw_response(results, f'github_{command}', responses_dir)
    print(f"[原始响应已保存到: {filepath}]\n", file=sys.stderr)


def _format_output(results: Dict[str, Any], resource_type: str, format_type: str) -> str:
    """Format output based on format type"""
    format_map = {
        'json': lambda: format_json(results),
        'markdown': lambda: format_markdown(results, resource_type),
        'text': lambda: format_table(results, resource_type)
    }
    return format_map[format_type]()


def _write_output(output: str, output_path: Optional[str]):
    """Write output to file or stdout"""
    if output_path:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(output)
        print(f"结果已保存到: {output_path}")
    else:
        print(output)


if __name__ == "__main__":
    sys.exit(main())
