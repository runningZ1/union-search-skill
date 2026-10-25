import json
import re
from datetime import datetime
from pathlib import Path
from uuid import uuid4


DEFAULT_OUTPUT_DIR = Path(__file__).resolve().parents[2] / 'output'
ARCHIVE_VERSION = '1.0'
SECTIONS = {'metadata', 'raw_results', 'channel_results', 'final_results', 'result'}


def _write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def archive_search(result, *, command, started_at, options):
    root = DEFAULT_OUTPUT_DIR
    root.mkdir(parents=True, exist_ok=True)
    slug = re.sub(r'[^\w\-]+', '_', result['keyword'], flags=re.UNICODE).strip('_')[:48] or 'search'
    search_id = f"{started_at:%Y%m%dT%H%M%S%f}_{slug}_{uuid4().hex[:8]}"
    pending = root / ('.pending-' + search_id)
    pending.mkdir()
    target = root / search_id
    rows = result['results']
    raw = {platform: row['raw_items'] for platform, row in rows.items() if 'raw_items' in row}
    finished_at = datetime.now().astimezone()
    failed = result['summary']['failed']
    successful = result['summary']['successful']
    metadata = {
        'archive_version': ARCHIVE_VERSION,
        'search_id': search_id,
        'command': command,
        'query': result['keyword'],
        'started_at': started_at.isoformat(),
        'finished_at': finished_at.isoformat(),
        'status': 'success' if failed == 0 else ('partial_failure' if successful else 'failed'),
        'platforms': result['platforms'],
        'options': options,
        'summary': result['summary'],
        'timing': result['timing'],
        'processing': ['normalize_fields', 'aggregate_successful_channels', 'deduplicate_url_and_title'],
        'files': {section: section + '.json' for section in sorted(SECTIONS)},
    }
    result['archive'] = {'search_id': search_id, 'directory': str(target)}
    _write_json(pending / 'raw_results.json', raw)
    _write_json(pending / 'channel_results.json', rows)
    _write_json(pending / 'final_results.json', result['final_items'])
    _write_json(pending / 'result.json', result)
    _write_json(pending / 'metadata.json', metadata)
    pending.rename(target)
    return result['archive']


def list_history(*, query=None, platform=None, status=None, since=None, until=None, limit=20, offset=0):
    if limit < 0 or offset < 0:
        raise ValueError('limit 和 offset 必须大于或等于 0')
    start = datetime.strptime(since, '%Y-%m-%d').date() if since else None
    end = datetime.strptime(until, '%Y-%m-%d').date() if until else None
    if start and end and start > end:
        raise ValueError('since 不能晚于 until')
    records = []
    for path in DEFAULT_OUTPUT_DIR.glob('*/metadata.json'):
        if path.parent.name.startswith('.'):
            continue
        metadata = json.loads(path.read_text(encoding='utf-8'))
        date = datetime.fromisoformat(metadata['started_at']).date()
        if query and query.casefold() not in metadata['query'].casefold():
            continue
        if platform and platform not in metadata['platforms']:
            continue
        if status and status != metadata['status']:
            continue
        if start and date < start:
            continue
        if end and date > end:
            continue
        records.append({**metadata, 'directory': str(path.parent)})
    records.sort(key=lambda row: (row['started_at'], row['search_id']), reverse=True)
    selected = records[offset:offset + limit] if limit else records[offset:]
    return {'total': len(records), 'limit': limit, 'offset': offset, 'items': selected}


def read_history(search_id, section='metadata'):
    if not search_id or Path(search_id).name != search_id or search_id.startswith('.') or '/' in search_id or '\\' in search_id:
        raise ValueError('search_id 必须是归档目录名称')
    if section not in SECTIONS:
        raise ValueError('不支持的归档文件')
    directory = DEFAULT_OUTPUT_DIR / search_id
    metadata = json.loads((directory / 'metadata.json').read_text(encoding='utf-8'))
    value = metadata if section == 'metadata' else json.loads((directory / (section + '.json')).read_text(encoding='utf-8'))
    return {'search_id': search_id, 'directory': str(directory), 'section': section, 'content': value}
