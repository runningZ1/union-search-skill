import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from no_api.web_search import (
    SearchBlockedError,
    SearchDeadline,
    create_session,
    document,
    request,
    result,
    text,
    validate_options,
)


def search_yandex(query, max_results=None, proxy=None, page=1, timeout=20):
    validate_options(page, max_results, None)
    deadline = SearchDeadline(timeout)
    if not query.strip():
        raise ValueError('query 不能为空')
    params = {
        'text': query,
        'tmpl_version': 'releases',
        'web': '1',
        'frame': '1',
        'searchid': '3131712',
    }
    if page > 1:
        params['p'] = page - 1
    with create_session(proxy) as session:
        response = request(session, 'GET', 'https://yandex.com/search/site/',
                           timeout=deadline.remaining(), params=params)
        if response.headers.get('x-yandex-captcha') == 'captcha':
            raise SearchBlockedError('Yandex 返回验证码')
        tree = document(response)
    items = tree.xpath('//li[contains(concat(" ", normalize-space(@class), " "), " b-serp-item ")]')
    if not items:
        raise RuntimeError('Yandex 未返回可识别的搜索结果结构')
    results = []
    for item in items:
        links = item.xpath('.//h3//a[contains(concat(" ", normalize-space(@class), " "), " b-serp-item__title-link ")]')
        if len(links) != 1:
            raise RuntimeError('Yandex 搜索结果缺少唯一标题链接')
        link = links[0]
        summary = item.xpath('.//div[contains(concat(" ", normalize-space(@class), " "), " b-serp-item__text ")]')
        results.append(result(text(link), link.attrib['href'], text(summary), 'yandex'))
    return results[:max_results or None]


def main():
    parser = argparse.ArgumentParser(description='Yandex 网页搜索，无需 API Key')
    parser.add_argument('query')
    parser.add_argument('-m', '--max-results', type=int, default=None)
    parser.add_argument('--page', type=int, default=1)
    parser.add_argument('--timeout', type=float, default=20)
    parser.add_argument('--proxy')
    parser.add_argument('--json', action='store_true')
    args = parser.parse_args()
    results = search_yandex(args.query, args.max_results, args.proxy, args.page, args.timeout)
    if args.json:
        print(json.dumps({'results': results}, ensure_ascii=False, indent=2))
    else:
        for item in results:
            print(f"{item['title']}\n{item['url']}\n{item['content']}\n")


if __name__ == '__main__':
    main()
