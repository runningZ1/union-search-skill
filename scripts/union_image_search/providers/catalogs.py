import json
from urllib.parse import quote, urljoin

import chompjs
from lxml import html

from no_api.web_search import SearchDeadline, create_session, document, request


SUPPORTED_PLATFORMS = ('pixabay', 'flickr', 'pinterest', '500px', 'wikicommons')


def _record(provider, title=None, image_url=None, source_url=None, thumbnail=None,
            width=None, height=None, author=None, license=None, image_variant='original'):
    return dict(provider=provider, title=title or None, image_url=image_url or None,
                source_url=source_url or None, thumbnail=thumbnail or None,
                width=width, height=height, author=author or None, license=license or None,
                image_variant=image_variant if image_url else None)


def _json(response):
    if 'json' not in response.headers.get('Content-Type', '').lower():
        document(response)
        raise ValueError('图片服务未返回 JSON，可能需要登录或完成网页验证')
    value = response.json()
    if isinstance(value, dict) and (value.get('errors') or value.get('error')):
        raise ValueError(f'图片服务返回错误：{value.get("errors") or value["error"]}')
    return value


def _pixabay(session, query, count, deadline):
    response = request(session, 'GET', f'https://pixabay.com/images/search/{quote(query, safe="")}/',
                       timeout=deadline.remaining(), headers={'Accept': 'application/json',
                       'x-fetch-bootstrap': '1', 'x-bootstrap-cache-miss': '1'})
    data = _json(response)
    records = []
    for item in data['page']['results']:
        if item['mediaType'] not in ('photo', 'illustration', 'vector'):
            continue
        download = item['sources'].get('downloadUrl')
        records.append(_record('pixabay', item.get('name'),
            urljoin('https://pixabay.com', download) if download else None,
            urljoin('https://pixabay.com', item['href']), item['sources'].get('1x'),
            author=(item.get('user') or {}).get('username'), image_variant='largest_available'))
    return records


def _pinterest(session, query, count, deadline):
    options = {'options': {'query': query, 'bookmarks': ['']}, 'context': {}}
    response = request(session, 'GET', 'https://www.pinterest.com/resource/BaseSearchResource/get/',
                       timeout=deadline.remaining(), params={'data': json.dumps(options)},
                       headers={'X-Requested-With': 'XMLHttpRequest', 'X-Pinterest-AppState': 'active',
                                'X-Pinterest-Source-Url': '/ideas/', 'X-Pinterest-PWS-Handler': 'www/ideas.js'})
    data = _json(response)['resource_response']
    if data.get('status') == 'failure':
        raise ValueError(f'Pinterest 搜索失败：{data.get("message")}')
    records = []
    for item in data['data']['results']:
        if item.get('type') != 'pin':
            continue
        original = item['images'].get('orig') or {}
        records.append(_record('pinterest', item.get('title'), original.get('url'),
            f'https://www.pinterest.com/pin/{quote(str(item["id"]), safe="")}/',
            item['images'].get('236x', {}).get('url'), original.get('width'), original.get('height'),
            (item.get('pinner') or {}).get('full_name')))
    return records


_PHOTO_QUERY = '''query ImageCatalog($keyword: String!, $first: Int!) {
  searchResource(keyword: $keyword, first: $first, resourceTypes: [PHOTO]) {
    edges { node { ... on Photo {
      id title width height urls { size_600 size_4k } uploader { displayName }
    } } }
  }
}'''


def _fivehundredpx(session, query, count, deadline):
    response = request(session, 'POST', 'https://api-neo.500px.com/graphql',
                       timeout=deadline.remaining(), json={'query': _PHOTO_QUERY,
                       'variables': {'keyword': query, 'first': min(count, 30)}})
    records = []
    for edge in _json(response)['data']['searchResource']['edges']:
        item = edge['node']
        records.append(_record('500px', item.get('title'), item['urls'].get('size_4k'),
            f'https://500px.com/photo/{item["id"]}', item['urls'].get('size_600'),
            author=(item.get('uploader') or {}).get('displayName'), image_variant='largest_available'))
    return records


_FLICKR_LICENSES = {
    0: 'All Rights Reserved', 1: 'https://creativecommons.org/licenses/by-nc-sa/2.0/',
    2: 'https://creativecommons.org/licenses/by-nc/2.0/',
    3: 'https://creativecommons.org/licenses/by-nc-nd/2.0/',
    4: 'https://creativecommons.org/licenses/by/2.0/',
    5: 'https://creativecommons.org/licenses/by-sa/2.0/',
    6: 'https://creativecommons.org/licenses/by-nd/2.0/',
    7: 'No known copyright restrictions', 8: 'United States Government Work',
    9: 'https://creativecommons.org/publicdomain/zero/1.0/',
    10: 'https://creativecommons.org/publicdomain/mark/1.0/',
}


def _photo_models(value):
    if isinstance(value, dict):
        if value.get('_flickrModelRegistry') == 'photo-lite-models':
            yield value
        else:
            for child in value.values():
                yield from _photo_models(child)
    elif isinstance(value, list):
        for child in value:
            yield from _photo_models(child)


def _flickr(session, query, count, deadline):
    response = request(session, 'GET', 'https://www.flickr.com/search/',
                       timeout=deadline.remaining(), params={'text': query})
    tree = document(response)
    scripts = tree.xpath('//script[contains(text(), "modelExport:")]/text()')
    if len(scripts) != 1:
        raise ValueError('Flickr 搜索页面缺少唯一的 modelExport 状态')
    marker = 'modelExport:'
    state = chompjs.parse_js_object(scripts[0].partition(marker)[2])
    records = []
    seen = set()
    for photo in _photo_models(state['main']):
        if photo['id'] in seen:
            continue
        seen.add(photo['id'])
        sizes = {key: value['data'] for key, value in photo['sizes']['data'].items()}
        if not sizes:
            continue
        largest = max(sizes.values(), key=lambda size: size['width'] * size['height'])
        image = sizes['o'] if 'o' in sizes else largest
        preview = min(sizes.values(), key=lambda size: abs(size['width'] - 320))
        records.append(_record('flickr', photo.get('title'), urljoin(response.url, image['url']),
            f'https://www.flickr.com/photos/{quote(photo["ownerNsid"], safe="@")}/{photo["id"]}/',
            urljoin(response.url, preview['url']), image.get('width'), image.get('height'),
            photo.get('username'), _FLICKR_LICENSES.get(photo.get('license')),
            image_variant='original' if 'o' in sizes else 'largest_available'))
    return records


def _plain_html(value):
    if not value:
        return None
    return ' '.join(html.fragment_fromstring(value, create_parent=True).text_content().split()) or None


def _wikicommons(session, query, count, deadline):
    response = request(session, 'GET', 'https://commons.wikimedia.org/w/api.php',
        timeout=deadline.remaining(), params={'action': 'query', 'format': 'json', 'formatversion': 2,
        'generator': 'search', 'gsrnamespace': 6, 'gsrsearch': f'{query} filetype:bitmap',
        'gsrlimit': min(count, 50), 'prop': 'imageinfo', 'iiprop': 'url|size|extmetadata', 'iiurlwidth': 320})
    records = []
    for page in sorted(_json(response).get('query', {}).get('pages', []), key=lambda value: value['index']):
        if not page.get('imageinfo'):
            continue
        image = page['imageinfo'][0]
        metadata = image.get('extmetadata', {})
        records.append(_record('wikicommons', page['title'].removeprefix('File:'), image['url'],
            image['descriptionurl'], image.get('thumburl'), image.get('width'), image.get('height'),
            _plain_html(metadata.get('Artist', {}).get('value')),
            metadata.get('LicenseUrl', {}).get('value') or metadata.get('LicenseShortName', {}).get('value')))
    return records


_SEARCHERS = {'pixabay': _pixabay, 'pinterest': _pinterest,
              '500px': _fivehundredpx, 'flickr': _flickr, 'wikicommons': _wikicommons}


def search(platform, query, limit, timeout=20):
    if platform not in _SEARCHERS:
        raise ValueError(f'不支持的图片来源：{platform}')
    if not isinstance(query, str) or not query.strip():
        raise ValueError('query 必须是非空字符串')
    if not isinstance(limit, int):
        raise ValueError('limit 必须是整数')
    count = limit if limit > 0 else 50
    deadline = SearchDeadline(timeout)
    with create_session() as session:
        records = _SEARCHERS[platform](session, query, count, deadline)
    deadline.remaining()
    return records[:limit] if limit > 0 else records
