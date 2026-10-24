import argparse
import json
import os
import sys
from pathlib import Path
from urllib.parse import urlencode

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from no_api.web_search import create_session, document, request, result, text, validate_options


class BraveSearch:
    ENGINE_NAME = 'brave'
    ENGINE_DISPLAY_NAME = 'Brave 搜索'
    SEARCH_URL = 'https://search.brave.com/search'
    REQUIRES_PROXY = True

    def __init__(self, proxy=None):
        self.proxy = proxy or os.getenv('BRAVE_PROXY') or os.getenv('NO_API_KEY_PROXY')
        self.session = create_session(self.proxy)

    def build_search_url(self, query, page=1, country='us', safesearch='moderate', timelimit=None):
        validate_options(page, None, timelimit)
        if page > 10:
            raise ValueError('Brave 仅支持前十页')
        if safesearch not in ('off', 'moderate', 'strict'):
            raise ValueError('safesearch 仅支持 off、moderate、strict')
        if country != 'all' and (len(country) != 2 or not country.isalpha()):
            raise ValueError('country 必须为两个字母的国家代码或 all')
        params = {'q': query, 'source': 'web', 'offset': page - 1}
        if timelimit:
            params['tf'] = {'d': 'pd', 'w': 'pw', 'm': 'pm', 'y': 'py'}[timelimit]
        return self.SEARCH_URL + '?' + urlencode(params)

    def parse_results(self, tree):
        results = []
        for item in tree.xpath('//*[@data-type="web"]'):
            title = item.xpath('.//div[contains(concat(" ",normalize-space(@class)," ")," title ")]')
            if not title:
                raise ValueError('Brave 网页结果缺少标题')
            anchors = title[0].xpath('ancestor::a[@href][1]')
            if not anchors:
                raise ValueError('Brave 网页结果缺少目标链接')
            content = item.xpath('.//div[contains(concat(" ",normalize-space(@class)," ")," generic-snippet ")]//div[contains(concat(" ",normalize-space(@class)," ")," content ")]')
            results.append(result(text(title[0]), anchors[0].get('href'), text(content), self.ENGINE_NAME))
        if not results:
            raise ValueError('Brave 页面未返回可识别的网页结果')
        return results

    def search(self, query, page=1, country='us', safesearch='moderate', timelimit=None, max_results=None, timeout=20):
        validate_options(page, max_results, timelimit)
        url = self.build_search_url(query, page, country, safesearch, timelimit)
        if timeout <= 0:
            raise ValueError('timeout 必须大于零')
        response = request(self.session, 'GET', url, timeout=timeout, cookies={
            'country': country.lower(), 'safesearch': safesearch, 'useLocation': '0', 'summarizer': '0',
        })
        return self.parse_results(document(response))[:max_results or None]

    def format_results(self, results, query):
        lines = [f'Brave 搜索: {query}', f'找到 {len(results)} 条结果', '']
        for index, item in enumerate(results, 1):
            lines.extend([f'[{index}] {item["title"]}', item['href'], item['body'], ''])
        return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(description='Brave 搜索')
    parser.add_argument('query', help='搜索关键词')
    parser.add_argument('-p', '--page', type=int, default=1)
    parser.add_argument('-m', '--max-results', type=int, default=None)
    parser.add_argument('-c', '--country', default='us')
    parser.add_argument('-s', '--safesearch', choices=['off', 'moderate', 'strict'], default='moderate')
    parser.add_argument('-t', '--timelimit', choices=['d', 'w', 'm', 'y'])
    parser.add_argument('--proxy')
    parser.add_argument('--timeout', type=float, default=20)
    parser.add_argument('--json', action='store_true')
    parser.add_argument('--pretty', action='store_true')
    args = parser.parse_args()
    client = BraveSearch(proxy=args.proxy)
    results = client.search(args.query, page=args.page, country=args.country, safesearch=args.safesearch,
                            timelimit=args.timelimit, max_results=args.max_results, timeout=args.timeout)
    if args.json:
        print(json.dumps({'query': args.query, 'page': args.page, 'country': args.country,
                          'total_results': len(results), 'results': results},
                         ensure_ascii=False, indent=2 if args.pretty else None))
    else:
        print(client.format_results(results, args.query))


if __name__ == '__main__':
    main()
