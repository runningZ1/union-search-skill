import argparse
import json
import sys
from pathlib import Path
from urllib.parse import urlencode, urljoin, urlsplit

from lxml import html

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from no_api.web_search import SearchBlockedError, create_session, document, request, result, text, validate_options


class SogouSearchNoAPI:
    ENGINE_NAME = "sogou"
    ENGINE_DISPLAY_NAME = "搜狗搜索"
    SEARCH_URL = "https://www.sogou.com/web?query={keyword}"
    REQUIRES_PROXY = False
    TIME_FILTERS = {"d": "inttime_day", "w": "inttime_week", "m": "inttime_month", "y": "inttime_year"}

    def __init__(self, proxy=None):
        self.proxy = proxy
        self.session = create_session(proxy=proxy)

    def build_search_url(self, query: str, **kwargs) -> str:
        page = kwargs.get("page", 1)
        timelimit = kwargs.get("timelimit")
        validate_options(page, None, timelimit)
        params = {"query": query, "page": page}
        if timelimit:
            params.update(s_from=self.TIME_FILTERS[timelimit], tsn=1)
        return "https://www.sogou.com/web?" + urlencode(params)

    def parse_results(self, tree: html.HtmlElement) -> list[dict]:
        headings = tree.xpath("//title")
        heading = text(headings[0]) if headings else ""
        if any(marker in heading for marker in ("验证码", "用户验证", "安全验证", "访问异常")):
            raise SearchBlockedError("搜狗搜索要求安全验证")
        results = []
        seen = set()
        items = tree.xpath(
            "//div[contains(concat(' ', normalize-space(@class), ' '), ' rb ')"
            " or contains(concat(' ', normalize-space(@class), ' '), ' vrwrap ')]"
        )
        for item in items:
            links = item.xpath(".//h3/a[@href]")
            if not links:
                continue
            link = links[0]
            title = text(link)
            target = link.get("href")
            if urlsplit(urljoin("https://www.sogou.com/", target)).path == "/link":
                targets = item.xpath(".//*[@data-url]/@data-url")
                if link.get("data-url"):
                    targets.insert(0, link.get("data-url"))
                if targets:
                    target = targets[0]
            target = urljoin("https://www.sogou.com/", target)
            if not title or urlsplit(target).scheme not in ("http", "https") or target in seen:
                continue
            summaries = item.xpath(
                ".//*[contains(concat(' ', normalize-space(@class), ' '), ' ft ')"
                " or contains(concat(' ', normalize-space(@class), ' '), ' attribute-centent ')"
                " or contains(concat(' ', normalize-space(@class), ' '), ' fz-mid ')"
                " or contains(concat(' ', normalize-space(@class), ' '), ' star-wiki ')"
                " or contains(concat(' ', normalize-space(@class), ' '), ' vr-info ')"
                " or contains(concat(' ', normalize-space(@class), ' '), ' str_info ')]"
            )
            # 合并摘要区域，排除嵌套摘要重复输出。
            summaries = [node for node in summaries if not any(parent in summaries for parent in node.iterancestors())]
            content = " ".join(filter(None, (text(node) for node in summaries)))
            results.append(result(title, target, content, self.ENGINE_NAME))
            seen.add(target)
        if not results:
            visible = " ".join(tree.xpath("//body//text()[not(ancestor::script) and not(ancestor::style)]"))
            if not any(marker in visible for marker in ("没有找到", "未找到", "找不到相关", "没有相关")):
                raise RuntimeError("UNEXPECTED_RESPONSE: 搜狗搜索页面缺少可识别结果或无结果提示")
        return results

    def search(self, query, max_results=None, timeout=15, **kwargs):
        page = kwargs.get("page", 1)
        timelimit = kwargs.get("timelimit")
        validate_options(page, max_results, timelimit)
        if not query.strip():
            raise ValueError("query 不能为空")
        if timeout <= 0:
            raise ValueError("timeout 必须大于零")
        response = request(self.session, "GET", self.build_search_url(query, page=page, timelimit=timelimit),
                           timeout=timeout, allow_redirects=False)
        location = urlsplit(urljoin(response.url, response.headers.get("Location", "")))
        if "/antispider" in location.path or "/captcha" in location.path:
            raise SearchBlockedError("搜狗搜索跳转至验证码页面")
        if not 200 <= response.status_code < 300:
            raise RuntimeError(f"UNEXPECTED_RESPONSE: 搜狗搜索返回 HTTP {response.status_code}")
        if not response.content.strip():
            raise RuntimeError("UNEXPECTED_RESPONSE: 搜狗搜索返回空页面")
        return self.parse_results(document(response))[:max_results or None]

    def format_results(self, results, query):
        lines = [f"{self.ENGINE_DISPLAY_NAME}: {query}", f"找到 {len(results)} 条结果", ""]
        for index, item in enumerate(results, 1):
            lines.extend([f"[{index}] {item['title']}", f"    {item['href']}", f"    {item['body']}", ""])
        return "\n".join(lines)


def search_sogou(query: str, max_results: int = None, proxy: str = None, **kwargs):
    return SogouSearchNoAPI(proxy=proxy).search(query, max_results=max_results, **kwargs)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="搜狗搜索 (无需 API Key)")
    parser.add_argument("query", help="搜索关键词")
    parser.add_argument("-m", "--max-results", type=int, default=None)
    parser.add_argument("--proxy", help="代理地址")
    parser.add_argument("--page", type=int, default=1)
    parser.add_argument("--timelimit", choices=("d", "w", "m", "y"))
    parser.add_argument("--timeout", type=float, default=15)
    parser.add_argument("--json", action="store_true", help="JSON 输出")
    args = parser.parse_args()
    results = search_sogou(args.query, args.max_results, args.proxy, page=args.page,
                           timelimit=args.timelimit, timeout=args.timeout)
    if args.json:
        print(json.dumps({"results": results}, ensure_ascii=False, indent=2))
    else:
        print(SogouSearchNoAPI().format_results(results, args.query))
