import argparse
import json
import sys
from pathlib import Path

from lxml import html

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


DOCUMENT_CARDS = {'ss_doc', 'ss_kv', 'ss_text', 'baike', 'structure_web_novel'}


def _plain(value):
    if value is None or value == '':
        return ''
    return text(html.fragment_fromstring(value, create_parent='div'))


def _card_results(category, data):
    if category in DOCUMENT_CARDS:
        if 'titleProps' in data:
            yield data['titleProps']['content'], data['sourceProps']['dest_url'], data.get('summaryProps', {}).get('content', '')
        elif 'normal_url' in data:
            yield data['title'], data['normal_url'], data.get('show_body', '')
        else:
            yield data['title'], data['url'], data.get('desc', data.get('text', ''))
    elif category == 'nature_result':
        yield data['title'], data['url'], data.get('desc', '')
    elif category == 'addition':
        yield data['title']['content'], data['source']['url'], data.get('summary', {}).get('content', '')
    elif category == 'ss_note':
        yield data['title']['content'], data['source']['dest_url'], data.get('summary', {}).get('content', '')
    elif category == 'baike_sc':
        card = data['data']
        yield card['title'], card['url'], card.get('abstract', '')
    elif category == 'news_uchq':
        for card in data['feed']:
            yield card['title'], card['url'], card.get('summary', '')
    elif category == 'ai_page':
        for card in data['list']:
            content = card.get('content', '')
            if isinstance(content, list):
                content = ' | '.join(content)
            yield card['title'], card['url'], content


def search_quark(query, max_results=None, proxy=None, page=1, timeout=20):
    validate_options(page, max_results, None)
    deadline = SearchDeadline(timeout)
    if not query.strip():
        raise ValueError('query 不能为空')
    with create_session(proxy) as session:
        response = request(session, 'GET', 'https://quark.sm.cn/s',
                           timeout=deadline.remaining(),
                           params={'q': query, 'layout': 'html', 'page': page})
        tree = document(response)
    return _parse_results(tree)[:max_results or None]


def _parse_results(tree):
    if tree.xpath('//script[contains(@src,"x5sec") or contains(.,"_____tmd_____/") or contains(.,"window._config_")] | //form[contains(@action,"captcha")]'):
        raise SearchBlockedError('Quark 返回验证码')
    scripts = tree.xpath('//script[@type="application/json" and starts-with(@id,"s-data-") and @data-used-by="hydrate"]')
    if not scripts:
        raise RuntimeError('Quark 未返回可识别的 hydration 搜索结果结构')
    results = []
    for script in scripts:
        payload = json.loads(script.text)
        category = payload['extraData']['sc']
        data = payload['data']['initialData']
        for title, url, content in _card_results(category, data):
            results.append(result(_plain(title), url, _plain(content), 'quark', category=category))
    if not results:
        raise RuntimeError('Quark 页面中没有受支持的网页结果卡片')
    return results


def main():
    parser = argparse.ArgumentParser(description='Quark 网页搜索，无需 API Key')
    parser.add_argument('query')
    parser.add_argument('-m', '--max-results', type=int, default=None)
    parser.add_argument('--page', type=int, default=1)
    parser.add_argument('--timeout', type=float, default=20)
    parser.add_argument('--proxy')
    parser.add_argument('--json', action='store_true')
    args = parser.parse_args()
    results = search_quark(args.query, args.max_results, args.proxy, args.page, args.timeout)
    if args.json:
        print(json.dumps({'results': results}, ensure_ascii=False, indent=2))
    else:
        for item in results:
            print(f"{item['title']}\n{item['url']}\n{item['content']}\n")


if __name__ == '__main__':
    main()
