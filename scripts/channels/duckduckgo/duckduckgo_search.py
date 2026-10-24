import argparse
import json
import os
from pathlib import Path
import sys
from urllib.parse import parse_qsl, urljoin, urlparse

from lxml import html

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from no_api.web_search import SearchBlockedError, SearchDeadline, create_session, document, request, result, validate_options


class DuckDuckGoSearch:
    def __init__(self, proxy=None):
        self.session = create_session(proxy or os.getenv('DUCKDUCKGO_PROXY') or os.getenv('NO_API_KEY_PROXY'))
        self.session.impersonate = 'firefox'
        self.session.default_headers = False
        self.session.headers.update({'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:142.0) Gecko/20100101 Firefox/142.0', 'Accept-Language': 'en-US,en;q=0.5'})

    def search(self, query, page=1, region='wt-wt', timelimit=None, max_results=None, timeout=20):
        validate_options(page, max_results, timelimit)
        if not query.strip() or len(query) > 499:
            raise ValueError('DuckDuckGo 查询长度必须在 1 到 499 个字符之间')
        if region != 'wt-wt' or timelimit is not None:
            raise ValueError('DuckDuckGo 网页接口不支持地区或时间筛选')
        deadline = SearchDeadline(timeout)
        with self.session:
            home = request(self.session, 'GET', 'https://duckduckgo.com/', params={'q': query, 't': 'h_', 'ia': 'web'}, timeout=deadline.remaining())
            links = document(home).xpath('//link[@id="deep_preload_link"]/@href')
            if not links:
                raise SearchBlockedError('DuckDuckGo 未提供网页结果接口地址')
            endpoint = urljoin(home.url, links[0])
            for index in range(1, page + 1):
                parsed = urlparse(endpoint)
                if parsed.scheme != 'https' or parsed.hostname not in ('duckduckgo.com', 'links.duckduckgo.com') or parsed.path != '/d.js':
                    raise ValueError('DuckDuckGo 返回非预期的结果接口地址')
                if dict(parse_qsl(parsed.query)).get('o') != 'json':
                    endpoint = endpoint.replace('/d.js?', '/d.js?o=json&', 1)
                response = request(self.session, 'GET', endpoint, timeout=deadline.remaining(), headers={'Referer': 'https://duckduckgo.com/', 'Accept': '*/*', 'Sec-Fetch-Dest': 'script', 'Sec-Fetch-Mode': 'no-cors', 'Sec-Fetch-Site': 'same-site'})
                if 'let jsa =' in response.text:
                    raise SearchBlockedError('DuckDuckGo 返回 JavaScript 验证页面')
                rows = response.json()['results']
                if index < page:
                    next_links = [row['n'] for row in rows if row.get('n')]
                    if not next_links:
                        return []
                    endpoint = urljoin('https://duckduckgo.com/', next_links[-1])
            items = []
            for row in rows:
                if not row.get('u'):
                    continue
                title = html.fragment_fromstring(row['t'], create_parent='div').text_content()
                content = html.fragment_fromstring(row.get('a', ''), create_parent='div').text_content()
                items.append(result(title, row['u'], content, 'duckduckgo', source_rank=len(items) + 1))
            return items[:max_results or None]

    def format_results(self, results, query):
        return '\n\n'.join(f"{item['title']}\n{item['url']}\n{item['content']}" for item in results)


def main():
    parser = argparse.ArgumentParser(description='DuckDuckGo 网页搜索')
    parser.add_argument('query')
    parser.add_argument('-p', '--page', type=int, default=1)
    parser.add_argument('-m', '--max-results', type=int)
    parser.add_argument('-r', '--region', default='wt-wt')
    parser.add_argument('-t', '--timelimit', choices=['d', 'w', 'm', 'y'])
    parser.add_argument('--timeout', type=float, default=20)
    parser.add_argument('--proxy')
    parser.add_argument('--json', action='store_true')
    parser.add_argument('--pretty', action='store_true')
    args = parser.parse_args()
    client = DuckDuckGoSearch(args.proxy)
    items = client.search(args.query, args.page, args.region, args.timelimit, args.max_results, args.timeout)
    payload = {'query': args.query, 'page': args.page, 'total_results': len(items), 'results': items}
    print(json.dumps(payload, ensure_ascii=False, indent=2 if args.pretty else None) if args.json else client.format_results(items, args.query))


if __name__ == '__main__':
    main()
