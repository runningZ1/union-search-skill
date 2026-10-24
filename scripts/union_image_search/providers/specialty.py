from urllib.parse import quote, urlsplit

import chompjs
from lxml import html

from no_api.web_search import SearchDeadline, create_session, document, request


SUPPORTED_PLATFORMS = ('artstation', 'findthatmeme', 'naver')


def _record(provider, title, image_url, source_url, thumbnail=None, width=None,
            height=None, author=None, license=None, image_variant='original'):
    for url in (image_url, source_url):
        parsed = urlsplit(url)
        if parsed.scheme not in ('http', 'https') or not parsed.netloc:
            raise ValueError(f'{provider} 返回无效地址')
    return dict(title=title or None, image_url=image_url, source_url=source_url,
                thumbnail=thumbnail or None, width=int(width) if width else None,
                height=int(height) if height else None, author=author or None,
                license=license or None, provider=provider, image_variant=image_variant)


def _json(response):
    if 'json' not in response.headers.get('Content-Type', '').lower():
        document(response)
        raise ValueError('图片服务没有返回 JSON')
    return response.json()


def _artstation(session, query, limit, deadline):
    token = request(session, 'POST', 'https://www.artstation.com/api/v2/csrf_protection/token.json',
                    timeout=deadline.remaining())
    public = _json(token)['public_csrf_token']
    response = request(session, 'POST', 'https://www.artstation.com/api/v2/search/projects.json',
                       timeout=deadline.remaining(), headers={'PUBLIC-CSRF-TOKEN': public},
                       json={'query': query, 'page': 1, 'per_page': 20,
                             'sorting': 'relevance', 'pro_first': 1})
    records = []
    for item in _json(response)['data']:
        project = _json(request(session, 'GET',
            f'https://www.artstation.com/projects/{quote(item["hash_id"], safe="")}.json',
            timeout=deadline.remaining()))
        for asset in project['assets']:
            if asset['asset_type'] != 'image' or not asset.get('image_url'):
                continue
            # 使用项目明确提供的图片地址，公开尺寸不能证明是上传原图。
            records.append(_record('artstation', item['title'], asset['image_url'], item['url'],
                item.get('smaller_square_cover_url'), author=item['user'].get('full_name'),
                image_variant='largest_available'))
            if len(records) == limit:
                return records
    return records


def _findthatmeme(session, query, limit, deadline):
    response = request(session, 'POST', 'https://findthatmeme.com/api/v1/search',
                       timeout=deadline.remaining(), json={'search': query, 'offset': 0})
    records = []
    for item in _json(response):
        if item['type'] != 'IMAGE':
            continue
        records.append(_record('findthatmeme', item.get('transcription') or item.get('source_site'),
            item['image_url'], item['source_page_url'], item.get('thumbnail_url')))
        if len(records) == limit:
            break
    return records


def _naver(session, query, limit, deadline):
    response = request(session, 'GET', 'https://search.naver.com/search.naver',
                       timeout=deadline.remaining(), params={'query': query, 'where': 'image', 'start': 1})
    tree = document(response)
    scripts = tree.xpath('//script[contains(.,"var imageSearchTabData =")]/text()')
    if not scripts:
        raise ValueError('Naver 图片搜索页面缺少结果数据')
    data = chompjs.parse_js_object(scripts[0].split('var imageSearchTabData =', 1)[1])
    records = []
    for item in data['content']['items'][:limit]:
        title = html.fragment_fromstring(item['title'], create_parent='div').text_content()
        records.append(_record('naver', title, item['originalUrl'], item['link'], item.get('thumb'),
                               item.get('orgWidth'), item.get('orgHeight')))
    return records


_SEARCHERS = {'artstation': _artstation, 'findthatmeme': _findthatmeme, 'naver': _naver}


def search(platform, query, limit, timeout=20):
    if platform not in SUPPORTED_PLATFORMS:
        raise ValueError(f'不支持图片渠道：{platform}')
    if not isinstance(query, str) or not query.strip():
        raise ValueError('query 必须是非空字符串')
    if isinstance(limit, bool) or not isinstance(limit, int) or limit < 0:
        raise ValueError('limit 必须是非负整数')
    deadline = SearchDeadline(timeout)
    count = limit or 20
    with create_session() as session:
        records = _SEARCHERS[platform](session, query, count, deadline)
        deadline.remaining()
        return records
