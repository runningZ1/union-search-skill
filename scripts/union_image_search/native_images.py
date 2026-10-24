import hashlib
import io
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
import sys
import time
from urllib.parse import urlsplit

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'channels'))
from no_api.web_search import SearchDeadline, create_session, request


ENGINE_PLATFORMS = {'baidu', 'bing', 'sogou', 'quark'}
CATALOG_PLATFORMS = {'pixabay', 'flickr', 'pinterest', '500px', 'wikicommons'}
SPECIALTY_PLATFORMS = {'naver', 'artstation', 'findthatmeme'}


def search_images(platform, query, limit, timeout):
    if platform in ENGINE_PLATFORMS:
        from providers.search_engines import search
    elif platform in CATALOG_PLATFORMS:
        from providers.catalogs import search
    elif platform in SPECIALTY_PLATFORMS:
        from providers.specialty import search
    else:
        raise ValueError(f'Unsupported native image platform: {platform}')
    rows = search(platform, query, limit, timeout=timeout)
    output = []
    seen = set()
    for row in rows:
        image_url = row['image_url']
        parsed = urlsplit(image_url)
        if parsed.scheme not in ('http', 'https') or not parsed.hostname:
            raise ValueError(f'{platform} 返回无效原图 URL')
        if image_url in seen:
            continue
        source = row.get('source_url')
        if source is not None and (urlsplit(source).scheme not in ('http', 'https') or not urlsplit(source).hostname):
            raise ValueError(f'{platform} 返回无效来源网页地址')
        seen.add(image_url)
        item = {key: row.get(key) for key in ('title', 'image_url', 'source_url', 'thumbnail', 'width', 'height', 'author', 'license', 'image_variant')}
        item.update({'provider': platform, 'id': len(output) + 1, 'file_path': None, 'download_status': 'not_requested'})
        output.append(item)
    return output[:limit or None]


def download_image(item, directory, deadline):
    with create_session() as session:
        response = request(session, 'GET', item['image_url'], timeout=deadline.remaining())
    content = response.content
    deadline.remaining()
    with Image.open(io.BytesIO(content)) as image:
        image.verify()
    with Image.open(io.BytesIO(content)) as image:
        image_format = image.format
        width, height = image.size
    suffix = Image.registered_extensions()
    extensions = sorted(key for key, value in suffix.items() if value == image_format)
    if image_format == 'JPEG':
        extensions = ['.jpg']
    if not extensions:
        raise ValueError(f'Unsupported image format: {image_format}')
    digest = hashlib.sha256(content).hexdigest()
    path = directory / (digest + extensions[0])
    if path.exists():
        if path.read_bytes() != content:
            raise FileExistsError(str(path))
    else:
        path.write_bytes(content)
    return {**item, 'file_path': str(path.resolve()), 'download_status': 'downloaded', 'width': width, 'height': height, 'bytes': len(content), 'sha256': digest}


def run_platform(platform, query, limit, output_dir, threads, save_metadata, search_only=False, timeout=30):
    import json
    started = time.monotonic()
    deadline = SearchDeadline(timeout)
    items = search_images(platform, query, limit, deadline.remaining())
    directory = None
    if threads < 1:
        raise ValueError('threads 必须大于零')
    if not search_only:
        stamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
        directory = Path(output_dir) / f'{platform}_{stamp}'
        directory.mkdir(parents=True, exist_ok=False)
        tasks = {}
        output = list(items)
        with ThreadPoolExecutor(max_workers=threads) as executor:
            for index, item in enumerate(items):
                tasks[executor.submit(download_image, item, directory, deadline)] = index
            for task in as_completed(tasks):
                index = tasks[task]
                # 在任务边界保留单张图片失败，其余真实文件继续交付。
                try:
                    output[index] = task.result()
                except Exception as error:
                    output[index] = {**items[index], 'download_status': 'failed', 'error': str(error).splitlines()[-1]}
        items = output
    downloaded = sum(item['download_status'] == 'downloaded' for item in items)
    failed = sum(item['download_status'] == 'failed' for item in items)
    metadata_file = None
    if save_metadata and directory is not None:
        metadata_file = directory / 'metadata.json'
        metadata_file.write_text(json.dumps({'platform': platform, 'query': query, 'images': items}, ensure_ascii=False, indent=2), encoding='utf-8')
    return {'platform': platform, 'keyword': query, 'success': failed == 0, 'found': len(items), 'downloaded': downloaded,
            'download_failed': failed, 'metadata': items, 'output_dir': str(directory or ''), 'metadata_file': str(metadata_file) if metadata_file else None,
            'duration_ms': round((time.monotonic() - started) * 1000), 'error': f'{failed} image downloads failed' if failed else None}
