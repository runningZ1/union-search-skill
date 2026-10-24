import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List
from urllib.parse import parse_qs, quote, urljoin, urlsplit

from lxml import html

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from no_api.web_search import SearchBlockedError, create_session, document, request, result, text, validate_options


def _excluded_url(url):
    location = urlsplit(url)
    host = (location.hostname or '').lower()
    if host != 'baidu.com' and not host.endswith('.baidu.com'):
        return False
    return (
        location.path.lower().rstrip('/') == '/baidu.php'
        or host in ('image.baidu.com', 'images.baidu.com', 'video.baidu.com')
        or (host in ('baidu.com', 'www.baidu.com') and location.path.startswith('/sf/vsearch')
            and parse_qs(location.query).get('pd', [''])[0] in ('image', 'video'))
    )


def _redirect_url(url):
    location = urlsplit(url)
    return location.hostname in ('baidu.com', 'www.baidu.com', 'm.baidu.com') and location.path.rstrip('/') in ('/link', '/from')


class BaiduSearchNoApi:
    ENGINE_NAME = 'baidu'
    ENGINE_DISPLAY_NAME = '百度搜索'
    SEARCH_URL = 'https://www.baidu.com/s?wd={keyword}'
    REQUIRES_PROXY = False

    def __init__(self, proxy=None):
        self.proxy = proxy
        self.session = create_session(proxy=proxy)

    def build_search_url(self, query: str, **kwargs) -> str:
        return self.SEARCH_URL.replace('{keyword}', quote(query))

    def parse_results(self, tree: html.HtmlElement) -> List[Dict[str, Any]]:
        headings = tree.xpath('//title')
        heading = text(headings[0]) if headings else ''
        if any(marker in heading for marker in ('百度安全验证', '验证码', '访问异常')):
            raise SearchBlockedError('百度搜索要求安全验证')
        results = []
        items = tree.xpath(
            '//div[@id="content_left"]/*['
            'contains(concat(" ", normalize-space(@class), " "), " c-container ")'
            ' or contains(concat(" ", normalize-space(@class), " "), " result ")'
            ' or contains(concat(" ", normalize-space(@class), " "), " result-op ")]'
        )
        for item in items:
            # 广告标签仅匹配独立标记，避免误删正文中讨论广告的网页。
            if item.xpath(
                'self::*[@data-tuiguang or @data-ad or @data-ad-id]'
                ' | .//*[@data-tuiguang or @data-ad or @data-ad-id]'
                ' | .//*[contains(concat(" ", normalize-space(@class), " "), " ec-tuiguang ")'
                ' or contains(concat(" ", normalize-space(@class), " "), " ec_tuiguang_pplink ")]'
                ' | .//*[self::span or self::a or self::label][normalize-space(.)="广告" or normalize-space(.)="商业推广"]'
            ):
                continue
            links = item.xpath('.//h3//a[@href] | .//a[contains(concat(" ", normalize-space(@class), " "), " c-title ")][@href]')
            if not links:
                continue
            link = links[0]
            title = text(link)
            if not title:
                continue
            target = urljoin('https://www.baidu.com/', link.get('href'))
            if _excluded_url(target):
                continue
            # data-tools 使用 JSON 解码；mu 是新版普通结果的目标地址。
            tools = item.xpath('./@data-tools | .//*[@data-tools]/@data-tools')
            candidates = [json.loads(value).get('url', '') for value in tools]
            candidates.append(item.get('mu', ''))
            for candidate in candidates:
                if not candidate:
                    continue
                candidate = urljoin('https://www.baidu.com/', candidate)
                location = urlsplit(candidate)
                if location.scheme in ('http', 'https') and location.netloc and not _redirect_url(candidate):
                    target = candidate
                    break
            if _excluded_url(target):
                continue
            summaries = item.xpath(
                './/*[contains(@class, "summary-text") or contains(@class, "c-abstract")'
                ' or contains(concat(" ", normalize-space(@class), " "), " abstract ")'
                ' or contains(concat(" ", normalize-space(@class), " "), " c-span-last ")]'
            )
            summaries = [node for node in summaries if not any(parent in summaries for parent in node.iterancestors())]
            content = ' '.join(filter(None, (text(node) for node in summaries)))
            results.append(result(title, target, content, self.ENGINE_NAME,
                                  link_type='redirect' if _redirect_url(target) else 'direct'))
        if not items:
            visible = ' '.join(tree.xpath('//body//text()[not(ancestor::script) and not(ancestor::style)]'))
            if not any(marker in visible for marker in ('没有找到', '未找到相关', '抱歉，没有找到')):
                raise RuntimeError('UNEXPECTED_RESPONSE: 百度搜索页面缺少可识别结果或无结果提示')
        return results

    def search(self, query, max_results=None, timeout=15, **kwargs):
        validate_options(1, max_results, None)
        if not query.strip():
            raise ValueError('query 不能为空')
        if timeout <= 0:
            raise ValueError('timeout 必须大于零')
        response = request(self.session, 'GET', self.build_search_url(query, **kwargs), timeout=timeout)
        if not response.content.strip():
            raise RuntimeError('UNEXPECTED_RESPONSE: 百度搜索返回空页面')
        return self.parse_results(document(response))[:max_results or None]

    def format_results(self, results, query):
        lines = [f'{self.ENGINE_DISPLAY_NAME}: {query}', f'找到 {len(results)} 条结果', '']
        for index, item in enumerate(results, 1):
            lines.extend([f'[{index}] {item["title"]}', f'    {item["href"]}', f'    {item["body"]}', ''])
        return '\n'.join(lines)


def search_baidu(query: str, max_results: int = None, proxy: str = None, timeout: float = 15, **kwargs):
    return BaiduSearchNoApi(proxy=proxy).search(query, max_results=max_results, timeout=timeout, **kwargs)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='百度搜索 (无需 API Key)')
    parser.add_argument('query', help='搜索关键词')
    parser.add_argument('-m', '--max-results', type=int, default=None)
    parser.add_argument('--proxy', help='代理地址')
    parser.add_argument('--timeout', type=float, default=15, help='请求超时时间（秒）')
    parser.add_argument('--json', action='store_true', help='JSON 输出')
    args = parser.parse_args()
    results = search_baidu(args.query, args.max_results, args.proxy, timeout=args.timeout)
    if args.json:
        print(json.dumps({'results': results}, ensure_ascii=False, indent=2))
    else:
        print(BaiduSearchNoApi().format_results(results, args.query))
