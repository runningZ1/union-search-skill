import math
import sqlite3
import time
from contextlib import closing
from datetime import timezone
from email.utils import parsedate_to_datetime
from pathlib import Path


STATE_PATH = Path(__file__).resolve().parents[3] / '.work' / 'web-search-state.sqlite'
MIN_INTERVAL = 2.0
RATE_LIMIT_COOLDOWN = 300.0
CAPTCHA_COOLDOWN = 900.0


class CooldownActiveError(RuntimeError):
    def __init__(self, host, remaining, reason):
        self.host = host
        self.remaining = remaining
        self.reason = reason
        super().__init__(f'{host} 请求冷却中，remaining={remaining:.3f}s，原因：{reason}')


def remaining(end):
    budget = end - time.monotonic()
    if budget <= 0:
        raise TimeoutError('搜索请求超过截止时间')
    return budget


def retry_after_seconds(value):
    if value is None:
        return RATE_LIMIT_COOLDOWN
    value = value.strip()
    if value.isascii() and value.isdigit():
        return int(value)
    try:
        parsed = parsedate_to_datetime(value)
    except (TypeError, ValueError, OverflowError):
        return RATE_LIMIT_COOLDOWN
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return max(0.0, parsed.timestamp() - time.time())


class RequestState:
    def __init__(self, path=STATE_PATH, interval=MIN_INTERVAL):
        if not math.isfinite(interval) or interval < 0:
            raise ValueError('interval 必须是非负有限数值')
        self.path = Path(path)
        self.interval = interval

    def _connect(self, end):
        budget = remaining(end)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.path, timeout=min(budget, 59.0), isolation_level=None)
        return connection

    def _begin(self, connection, end):
        connection.execute('BEGIN IMMEDIATE')
        remaining(end)
        connection.execute('''CREATE TABLE IF NOT EXISTS host_state (
            host TEXT PRIMARY KEY,
            next_request REAL NOT NULL DEFAULT 0,
            cooldown_until REAL NOT NULL DEFAULT 0,
            reason TEXT NOT NULL DEFAULT ''
        )''')

    def _check(self, connection, host):
        row = connection.execute(
            'SELECT next_request, cooldown_until, reason FROM host_state WHERE host = ?', (host,)
        ).fetchone()
        now = time.time()
        if row is not None and row[1] > now:
            raise CooldownActiveError(host, row[1] - now, row[2])
        return row

    def reserve(self, host, end):
        if not host:
            raise ValueError('请求地址必须包含 host')
        host = host.lower()
        with closing(self._connect(end)) as connection, connection:
            self._begin(connection, end)
            row = self._check(connection, host)
            now = time.time()
            slot = max(now, row[0] if row else now)
            delay = slot - now
            if delay >= remaining(end):
                raise TimeoutError(f'{host} 请求预约等待 {delay:.3f}s 超过搜索截止时间')
            connection.execute('''INSERT INTO host_state(host, next_request) VALUES (?, ?)
                ON CONFLICT(host) DO UPDATE SET next_request = excluded.next_request''',
                (host, slot + self.interval))
        # 单次等待小于 60 秒，等待期间反复检查截止时间。
        wake = time.monotonic() + delay
        while True:
            wait = wake - time.monotonic()
            if wait <= 0:
                break
            time.sleep(min(wait, remaining(end), 59.0))
        self.check(host, end)
        remaining(end)

    def check(self, host, end):
        with closing(self._connect(end)) as connection, connection:
            self._begin(connection, end)
            self._check(connection, host.lower())
        remaining(end)

    def cooldown(self, host, duration, reason, end=None):
        if not host:
            raise ValueError('冷却记录必须包含 host')
        if not math.isfinite(duration) or duration < 0:
            raise ValueError('duration 必须是非负有限数值')
        # 响应返回后即使请求预算耗尽，也需要保存服务端的冷却信号。
        if end is None:
            end = time.monotonic() + 1.0
        until = time.time() + duration
        with closing(self._connect(end)) as connection, connection:
            self._begin(connection, end)
            connection.execute('''INSERT INTO host_state(host, cooldown_until, reason) VALUES (?, ?, ?)
                ON CONFLICT(host) DO UPDATE SET
                    cooldown_until = MAX(host_state.cooldown_until, excluded.cooldown_until),
                    reason = CASE WHEN excluded.cooldown_until >= host_state.cooldown_until
                        THEN excluded.reason ELSE host_state.reason END''',
                (host.lower(), until, reason))
        return until
