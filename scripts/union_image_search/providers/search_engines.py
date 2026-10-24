import json
from urllib.parse import parse_qs, urlparse

import chompjs
from lxml import html

from no_api.web_search import SearchDeadline, create_session, document, request


def _http_url(value):
    if not isinstance(value, str):
        return None
    parsed = urlparse(value)
    return value if parsed.scheme in ('http', 'https') and parsed.netloc else None


def _title(value):
    if not value:
        return None
    return ' '.join(html.fragment_fromstring(value, create_parent=True).text_content().split()) or None


def _dimension(value):
    if value is None or value == '':
        return None
    return int(value) or None


def _image(provider, image_url, source_url=None, title=None, thumbnail=None, width=None, height=None):
    image_url = _http_url(image_url)
    if image_url is None:
        return None
    return {
        'title': _title(title),
        'image_url': image_url,
        'source_url': _http_url(source_url),
        'thumbnail': _http_url(thumbnail),
        'width': _dimension(width),
        'height': _dimension(height),
        'author': None,
        'license': None,
        'provider': provider,
        'image_variant': 'original',
    }


def _baidu(session, query, count, deadline):
    warmup = request(session, 'GET', 'https://image.baidu.com/', timeout=deadline.remaining())
    document(warmup)
    response = request(
        session, 'GET', 'https://image.baidu.com/search/acjson', timeout=deadline.remaining(),
        params={'word': query, 'rn': count, 'pn': 0, 'tn': 'resultjson_com'},
        headers={'Referer': 'https://image.baidu.com/'},
    )
    data = chompjs.parse_js_object(response.text)
    if data.get('antiFlag') == 1:
        raise RuntimeError(f"baidu 拒绝图片请求：{data.get('message')}")
    for item in data['data']:
        if not item:
            continue
        originals = item.get('replaceUrl') or []
        if not originals:
            continue
        original = originals[0]
        yield _image('baidu', original.get('ObjURL'), original.get('FromURL'),
                     item.get('fromPageTitle'), item.get('thumbURL'), item.get('width'), item.get('height'))


def _bing(session, query, count, deadline):
    response = request(
        session, 'GET', 'https://www.bing.com/images/async', timeout=deadline.remaining(),
        params={'q': query, 'mmasync': 1, 'first': 1, 'count': count},
    )
    tree = document(response)
    links = tree.xpath('//a[contains(concat(" ", normalize-space(@class), " "), " iusc ")][@m]')
    if not links:
        raise RuntimeError('bing 响应没有图片原图元数据')
    for link in links:
        item = json.loads(link.get('m'))
        dimensions = parse_qs(urlparse(link.get('href', '')).query)
        yield _image('bing', item.get('murl'), item.get('purl'), item.get('t'), item.get('turl'),
                     dimensions.get('expw', [None])[0], dimensions.get('exph', [None])[0])


def _sogou(session, query, count, deadline):
    response = request(
        session, 'GET', 'https://pic.sogou.com/pics', timeout=deadline.remaining(),
        params={'query': query, 'start': 0},
    )
    tree = document(response)
    scripts = tree.xpath('//script[contains(., "window.__INITIAL_STATE__")]/text()')
    if not scripts:
        raise RuntimeError('sogou 响应没有图片初始状态')
    data = chompjs.parse_js_object(scripts[0].split('window.__INITIAL_STATE__', 1)[1])
    for item in data['searchList']['searchList']:
        row = _image('sogou', item.get('picUrl'), item.get('url'), item.get('title'),
                     item.get('thumbUrl'), item.get('width'), item.get('height'))
        if row is not None:
            row['image_variant'] = 'largest_available'
        yield row


def _quark(session, query, count, deadline):
    response = request(
        session, 'GET', 'https://vt.sm.cn/api/pic/list', timeout=deadline.remaining(),
        params={'query': query, 'limit': count, 'start': 0},
    )
    data = response.json()
    items = data['data']['hit']['imgInfo']['item']
    for item in items:
        yield _image('quark', item.get('bigPicUrl'), item.get('imgUrl'), item.get('title'),
                     item.get('img'), item.get('width'), item.get('height'))


PROVIDERS = {
    'baidu': _baidu,
    'bing': _bing,
    'sogou': _sogou,
    'quark': _quark,
}
SUPPORTED_PLATFORMS = tuple(PROVIDERS)


def search(platform, query, limit, timeout=20):
    if platform not in PROVIDERS:
        raise ValueError(f'不支持的图片平台：{platform}')
    if not isinstance(query, str) or not query.strip():
        raise ValueError('query 必须是非空字符串')
    if not isinstance(limit, int):
        raise ValueError('limit 必须是整数')
    deadline = SearchDeadline(timeout)
    count = min(limit, 100) if limit > 0 else 100
    results = []
    seen = set()
    with create_session() as session:
        for item in PROVIDERS[platform](session, query, count, deadline):
            deadline.remaining()
            if item is None or item['image_url'] in seen:
                continue
            seen.add(item['image_url'])
            results.append(item)
            if limit > 0 and len(results) >= limit:
                break
    if not results:
        raise RuntimeError(f'{platform} 没有返回可用的原图地址')
    return results
