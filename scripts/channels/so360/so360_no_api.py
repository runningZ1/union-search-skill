import argparse
import json
import sys
from pathlib import Path
from urllib.parse import urlencode, urljoin, urlsplit

from lxml import html

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from no_api.web_search import SearchBlockedError, SearchDeadline, create_session, document, request, result, text, validate_options


class So360SearchNoAPI:
    ENGINE_NAME = "so360"
    ENGINE_DISPLAY_NAME = "360 搜索"
    SEARCH_URL = "https://www.so.com/s?q={keyword}"
    REQUIRES_PROXY = False

    def __init__(self, proxy=None):
        self.proxy = proxy
        self.session = create_session(proxy=proxy)

    def build_search_url(self, query: str, **kwargs) -> str:
        page = kwargs.get("page", 1)
        timelimit = kwargs.get("timelimit")
        validate_options(page, None, timelimit)
        params = {"q": query, "pn": page}
        if timelimit:
            params["adv_t"] = timelimit
        return "https://www.so.com/s?" + urlencode(params)

    def parse_results(self, tree: html.HtmlElement) -> list[dict]:
        heading = text(tree.xpath("//title")[0]) if tree.xpath("//title") else ""
        if any(marker in heading for marker in ("验证码", "安全验证", "访问异常")):
            raise SearchBlockedError("360 搜索要求安全验证")
        results = []
        seen = set()
        for item in tree.xpath("//li[contains(concat(' ', normalize-space(@class), ' '), ' res-list ')]"):
            links = item.xpath(".//h3/a[@href]")
            if not links:
                continue
            link = links[0]
            title = text(link)
            target = link.get("data-mdurl") or link.get("href")
            target = urljoin("https://www.so.com/", target)
            parsed = urlsplit(target)
            if not title or parsed.scheme not in ("http", "https") or target in seen:
                continue
            if parsed.hostname in {"ai.so.com", "video.so.com", "image.so.com", "news.so.com"}:
                continue
            if parsed.hostname == "wenku.so.com" and parsed.path == "/s":
                continue
            summaries = item.xpath(
                ".//*[@data-result-summary] | .//p[contains(concat(' ', normalize-space(@class), ' '), ' res-desc ')]"
                " | .//span[contains(concat(' ', normalize-space(@class), ' '), ' res-list-summary ')]"
                " | .//div[contains(concat(' ', normalize-space(@class), ' '), ' mh-desc ')]"
            )
            # 优先保留内部摘要，避免把导航链接和重复摘要带入正文。
            summaries = [node for node in summaries if not any(child in summaries for child in node.iterdescendants())]
            content = " ".join(filter(None, (text(node) for node in summaries)))
            results.append(result(title, target, content, self.ENGINE_NAME))
            seen.add(target)
        if not results:
            visible = " ".join(tree.xpath("//body//text()[not(ancestor::script) and not(ancestor::style)]"))
            if not any(marker in visible for marker in ("没有找到", "未找到", "找不到相关", "没有相关")):
                raise RuntimeError("UNEXPECTED_RESPONSE: 360 搜索页面缺少可识别结果或无结果提示")
        return results

    def search(self, query, max_results=None, timeout=15, **kwargs):
        page = kwargs.get("page", 1)
        timelimit = kwargs.get("timelimit")
        validate_options(page, max_results, timelimit)
        if not query.strip():
            raise ValueError("query 不能为空")
        if timeout <= 0:
            raise ValueError("timeout 必须大于零")
        url = self.build_search_url(query, page=page, timelimit=timelimit)
        # 同一 Session 保存首次访问产生的 Cookie，再请求搜索结果。
        deadline = SearchDeadline(timeout)
        request(self.session, "GET", url, timeout=deadline.remaining())
        response = request(self.session, "GET", url, timeout=deadline.remaining())
        if not response.content.strip():
            raise RuntimeError("UNEXPECTED_RESPONSE: 360 搜索返回空页面")
        results = self.parse_results(document(response))
        return results[:max_results or None]

    def format_results(self, results, query):
        lines = [f"{self.ENGINE_DISPLAY_NAME}: {query}", f"找到 {len(results)} 条结果", ""]
        for index, item in enumerate(results, 1):
            lines.extend([f"[{index}] {item['title']}", f"    {item['href']}", f"    {item['body']}", ""])
        return "\n".join(lines)


def search_so360(query: str, max_results: int = None, proxy: str = None, **kwargs):
    return So360SearchNoAPI(proxy=proxy).search(query, max_results=max_results, **kwargs)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="360 搜索 (无需 API Key)")
    parser.add_argument("query", help="搜索关键词")
    parser.add_argument("-m", "--max-results", type=int, default=None)
    parser.add_argument("--proxy", help="代理地址")
    parser.add_argument("--page", type=int, default=1)
    parser.add_argument("--timelimit", choices=("d", "w", "m", "y"))
    parser.add_argument("--timeout", type=float, default=15)
    parser.add_argument("--json", action="store_true", help="JSON 输出")
    args = parser.parse_args()
    results = search_so360(args.query, args.max_results, args.proxy, page=args.page,
                           timelimit=args.timelimit, timeout=args.timeout)
    if args.json:
        print(json.dumps({"results": results}, ensure_ascii=False, indent=2))
    else:
        print(So360SearchNoAPI().format_results(results, args.query))
