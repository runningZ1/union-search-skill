import argparse
import json
import os
import sys
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlencode, urljoin, urlparse

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from no_api.web_search import SearchDeadline, create_session, document, request, result, text, validate_options


class YahooSearch:
    ENGINE_NAME = 'yahoo'
    ENGINE_DISPLAY_NAME = 'Yahoo 搜索'
    SEARCH_URL = 'https://search.yahoo.com/search'
    REQUIRES_PROXY = True

    def __init__(self, proxy=None):
        self.proxy = proxy or os.getenv('YAHOO_PROXY') or os.getenv('NO_API_KEY_PROXY')
        self.session = create_session(self.proxy)

    def _unwrap_yahoo_url(self, raw_url):
        parsed = urlparse(raw_url)
        if parsed.hostname != 'r.search.yahoo.com':
            return raw_url
        targets = [segment[3:] for segment in parsed.path.split('/') if segment.startswith('RU=')]
        if len(targets) != 1:
            raise ValueError('Yahoo 包装地址缺少唯一的 RU 目标')
        return unquote(targets[0])

    def build_search_url(self, query, page=1, timelimit=None, safesearch='moderate'):
        validate_options(page, None, timelimit)
        if timelimit == 'y':
            raise ValueError('Yahoo 网页搜索不支持年度时间过滤')
        if safesearch not in ('off', 'moderate', 'strict'):
            raise ValueError('safesearch 仅支持 off、moderate、strict')
        params = {'p': query, 'iscqry': ''}
        if timelimit:
            params['btf'] = timelimit
        if page > 1:
            params.update({'b': (page - 1) * 7 + 1, 'pz': 7, 'bct': 0, 'xargs': 0})
        return self.SEARCH_URL + '?' + urlencode(params)

    def parse_results(self, tree):
        results = []
        for item in tree.xpath('//div[contains(concat(" ",normalize-space(@class)," ")," algo-sr ")]'):
            anchors = item.xpath('./div[contains(concat(" ",normalize-space(@class)," ")," compTitle ")]//a[.//h3]')
            if not anchors:
                raise ValueError('Yahoo 网页结果缺少标题链接')
            anchor = anchors[0]
            title = anchor.xpath('.//h3')
            content = item.xpath('./div[contains(concat(" ",normalize-space(@class)," ")," compText ")]')
            results.append(result(text(title), self._unwrap_yahoo_url(anchor.attrib['href']),
                                  text(content), self.ENGINE_NAME))
        if not results:
            raise ValueError('Yahoo 页面未返回可识别的网页结果')
        return results

    def search(self, query, page=1, timelimit=None, max_results=None, timeout=20, safesearch='moderate'):
        validate_options(page, max_results, timelimit)
        url = self.build_search_url(query, 1, timelimit, safesearch)
        deadline = SearchDeadline(timeout)
        preferences = urlencode({'v': 1, 'vm': {'off': 'p', 'moderate': 'i', 'strict': 'r'}[safesearch],
                                 'fl': 1, 'vl': 'lang_any', 'pn': 10, 'rw': 'new', 'userset': 1})
        self.session.cookies.set('sB', preferences, domain='.search.yahoo.com', path='/')
        for current in range(1, page + 1):
            response = request(self.session, 'GET', url, timeout=deadline.remaining())
            tree = document(response)
            if current == page:
                return self.parse_results(tree)[:max_results or None]
            links = tree.xpath('//div[contains(concat(" ",normalize-space(@class)," ")," compPagination ")]//a[contains(concat(" ",normalize-space(@class)," ")," next ")]/@href')
            if not links:
                raise ValueError(f'Yahoo 第 {current} 页缺少下一页链接')
            url = urljoin(response.url, links[0])
            parsed = urlparse(url)
            if parsed.scheme != 'https' or parsed.hostname != 'search.yahoo.com':
                raise ValueError('Yahoo 分页链接指向非搜索页面')
            if timelimit and parse_qs(parsed.query).get('btf') != [timelimit]:
                raise ValueError('Yahoo 分页链接未保留时间过滤')

    def format_results(self, results, query):
        lines = [f'Yahoo 搜索: {query}', f'找到 {len(results)} 条结果', '']
        for index, item in enumerate(results, 1):
            lines.extend([f'[{index}] {item["title"]}', item['href'], item['body'], ''])
        return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(description='Yahoo 搜索')
    parser.add_argument('query', help='搜索关键词')
    parser.add_argument('-p', '--page', type=int, default=1)
    parser.add_argument('-m', '--max-results', type=int, default=None)
    parser.add_argument('-t', '--timelimit', choices=['d', 'w', 'm'])
    parser.add_argument('-s', '--safesearch', choices=['off', 'moderate', 'strict'], default='moderate')
    parser.add_argument('--proxy')
    parser.add_argument('--timeout', type=float, default=20)
    parser.add_argument('--json', action='store_true')
    parser.add_argument('--pretty', action='store_true')
    args = parser.parse_args()
    client = YahooSearch(proxy=args.proxy)
    results = client.search(args.query, page=args.page, timelimit=args.timelimit,
                            max_results=args.max_results, timeout=args.timeout, safesearch=args.safesearch)
    if args.json:
        print(json.dumps({'query': args.query, 'page': args.page, 'total_results': len(results), 'results': results},
                         ensure_ascii=False, indent=2 if args.pretty else None))
    else:
        print(client.format_results(results, args.query))


if __name__ == '__main__':
    main()
