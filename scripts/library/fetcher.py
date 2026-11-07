import collections
import json
import os
import queue
import subprocess
import threading
import time
from pathlib import Path

from bs4 import UnicodeDammit
from curl_cffi import requests as curl_requests
from curl_cffi.requests.exceptions import RequestException, Timeout

from library import classify

EXTRACT_SCRIPT = Path(__file__).resolve().parents[1] / "url_to_markdown" / "engines" / "defuddle-node" / "extract_html.mjs"
# 与 extract_html.mjs 输出的 extractor 字段一致
EXTRACTOR = "defuddle@" + json.loads((EXTRACT_SCRIPT.parent / "node_modules" / "defuddle" / "package.json").read_text(encoding="utf-8"))["version"]
# HTML 页面读取上限；非 HTML 响应只读响应头，不下载文件内容
MAX_HTML_BYTES = 20 * 1024 * 1024
# 正文短于最长搜索摘要的该比例时不接受为正文
SUMMARY_RATIO = 0.8
# 提取是 CPU 密集操作。实测 14 核机器上 7 个进程吞吐最高，更多进程互相争用反而变慢，因此取核数的一半
EXTRACTOR_PROCESSES = max(2, (os.cpu_count() or 4) // 2)


class _ExtractProcess:
    """一个常驻 node 提取进程：同一时刻只处理一个请求，按行收发 JSON。"""

    def __init__(self):
        # Windows 上不为 node 子进程创建控制台窗口
        flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
        self.proc = subprocess.Popen(["node", str(EXTRACT_SCRIPT)], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE, creationflags=flags)
        self.replies = queue.Queue()
        self.stderr = collections.deque(maxlen=40)
        threading.Thread(target=self._read_stdout, daemon=True).start()
        threading.Thread(target=self._read_stderr, daemon=True).start()

    def _read_stdout(self):
        for line in self.proc.stdout:
            self.replies.put(json.loads(line.decode("utf-8")))
        self.replies.put(None)

    def _read_stderr(self):
        for line in self.proc.stderr:
            self.stderr.append(line.decode("utf-8", "replace").rstrip())

    def request(self, html_text, page_url, timeout):
        self.proc.stdin.write(json.dumps({"html": html_text, "url": page_url}, ensure_ascii=False).encode("utf-8") + b"\n")
        self.proc.stdin.flush()
        try:
            reply = self.replies.get(timeout=timeout)
        except queue.Empty:
            raise subprocess.TimeoutExpired(["node", str(EXTRACT_SCRIPT)], timeout)
        if reply is None:
            raise BrokenPipeError("Defuddle 提取进程已退出: " + "\n".join(self.stderr)[-800:])
        return reply

    def kill(self):
        self.proc.kill()
        self.proc.wait()


class ExtractorPool:
    """常驻提取进程池。超时或进程退出时终止该进程，下次按需重新启动。"""

    def __init__(self, size):
        self.size = size
        self.idle = []
        self.count = 0
        self.ready = threading.Condition()

    def warm(self):
        # 执行器启动时预先拉起全部进程，模块加载与等待搜索结果同时进行
        with self.ready:
            while self.count < self.size:
                self.idle.append(_ExtractProcess())
                self.count += 1

    def _acquire(self):
        # 等待空闲进程是本机排队，不计入单项时限，避免本机繁忙时把来源记为失败
        with self.ready:
            while not self.idle and self.count >= self.size:
                self.ready.wait()
            if self.idle:
                return self.idle.pop()
            self.count += 1
        return _ExtractProcess()

    def _release(self, worker, healthy):
        if not healthy:
            worker.kill()
        with self.ready:
            if healthy:
                self.idle.append(worker)
            else:
                self.count -= 1
            self.ready.notify()

    def extract(self, html_text, page_url, timeout, timing=None):
        """timeout 只限制提取运算本身。"""
        started = time.monotonic()
        worker = self._acquire()
        if timing is not None:
            timing["extract_wait"] = round((time.monotonic() - started) * 1000)
        try:
            reply = worker.request(html_text, page_url, timeout)
        except (subprocess.TimeoutExpired, BrokenPipeError, OSError):
            self._release(worker, healthy=False)
            raise
        self._release(worker, healthy=True)
        if not reply["ok"]:
            raise RuntimeError("Defuddle 提取失败: " + reply["error"][-800:])
        return reply["result"]

    def close(self):
        with self.ready:
            for worker in self.idle:
                worker.kill()
            self.idle.clear()


EXTRACTORS = ExtractorPool(EXTRACTOR_PROCESSES)
# 每个执行线程复用自己的会话，同一主机的后续请求复用连接
_sessions = threading.local()


def _session():
    if not hasattr(_sessions, "session"):
        _sessions.session = curl_requests.Session(impersonate="chrome")
    return _sessions.session


def _request(url, timeout, etag, last_modified):
    headers = {}
    if etag:
        headers["If-None-Match"] = etag
    if last_modified:
        headers["If-Modified-Since"] = last_modified
    response = _session().get(url, headers=headers, timeout=timeout, allow_redirects=True, stream=True)
    mime = response.headers.get("content-type", "")
    if classify.type_from_response(mime) is not None:
        response.close()
        return response, mime, None
    chunks = []
    size = 0
    for chunk in response.iter_content():
        size += len(chunk)
        if size > MAX_HTML_BYTES:
            response.close()
            raise ValueError(f"HTML 超过 {MAX_HTML_BYTES} 字节")
        chunks.append(chunk)
    response.close()
    return response, mime, b"".join(chunks)


def decode_html(payload, mime):
    """按响应头、页面声明的字符集和内容检测解码，避免中文页面乱码。"""
    declared = []
    if "charset=" in mime.lower():
        declared.append(mime.lower().split("charset=")[-1].split(";")[0].strip().strip('"'))
    dammit = UnicodeDammit(payload, known_definite_encodings=declared, is_html=True)
    if dammit.unicode_markup is None:
        raise ValueError("无法识别页面字符集")
    return dammit.unicode_markup, dammit.original_encoding


def extract(html_text, page_url, timeout, timing=None):
    """把解码后的页面交给常驻 Defuddle 进程，用真实页面地址解析。"""
    return EXTRACTORS.extract(html_text, page_url, timeout, timing)


def fetch(url, timeout, etag=None, last_modified=None, previous_chars=None, summary_chars=None):
    """请求来源并给出结论。网络、限制和提取问题都作为结论返回，不抛给调用方。"""
    outcome = dict(status=None, http_status=None, final_url=url, response_type=None, content_type=None,
                           content_type_evidence=[], restrictions=[], technical_reason=None, evidence=[],
                           body=None, partial_body=None, metadata={}, extractor=None, etag=None, last_modified=None, error=None)
    # 各阶段耗时只写入执行日志，用于定位慢项
    timing = outcome["timing_ms"] = {}
    started = time.monotonic()

    def mark(stage):
        nonlocal started
        now = time.monotonic()
        timing[stage] = round((now - started) * 1000)
        started = now

    try:
        response, mime, payload = _request(url, timeout, etag, last_modified)
        mark("request")
    except Timeout as exc:
        outcome.update(status="failed", technical_reason="timeout", error=str(exc))
        return outcome
    except RequestException as exc:
        outcome.update(status="failed", technical_reason="network_error", error=str(exc))
        return outcome
    except ValueError as exc:
        outcome.update(status="failed", technical_reason="too_large", error=str(exc))
        return outcome

    outcome.update(http_status=response.status_code, final_url=str(response.url), response_type=mime or None,
                   etag=response.headers.get("etag"), last_modified=response.headers.get("last-modified"))
    if response.status_code == 304:
        outcome.update(status="not_modified", evidence=["http_status:304"])
        return outcome

    restrictions, technical = classify.restrictions_from_status(response.status_code)
    non_html = classify.type_from_response(mime)
    if non_html is not None:
        outcome.update(content_type=non_html, content_type_evidence=["response_type:" + mime.split(";")[0].strip()])
        if restrictions or technical:
            outcome.update(status="restricted" if restrictions else "failed", restrictions=restrictions, technical_reason=technical,
                           error=f"HTTP {response.status_code}")
        elif non_html in ("pdf", "video", "podcast"):
            outcome.update(status="pending_preprocess")
        else:
            outcome.update(status="failed", technical_reason="unsupported_content_type")
        return outcome

    try:
        html_text, encoding = decode_html(payload, mime)
    except ValueError as exc:
        outcome.update(status="failed", technical_reason="undecodable", error=str(exc))
        return outcome
    mark("decode")
    tree = classify.parse_html(html_text)
    mark("parse")
    if tree is None:
        outcome.update(status="failed" if not restrictions else "restricted", restrictions=restrictions,
                       technical_reason=technical or "empty_response", error=f"HTTP {response.status_code} 空响应")
        return outcome

    # 单项时限分别限制网络请求和提取运算；等待空闲提取进程的时间不计入
    try:
        extracted = extract(html_text, outcome["final_url"], timeout, timing)
    except (RuntimeError, subprocess.TimeoutExpired, BrokenPipeError, OSError) as exc:
        outcome.update(status="failed", technical_reason="extraction_error", error=str(exc))
        return outcome
    mark("extract")
    timing["extract"] -= timing.get("extract_wait", 0)
    markdown = extracted["content"] or ""
    text = markdown
    outcome["extractor"] = extracted["extractor"]
    outcome["metadata"] = {key: extracted[key] for key in ("title", "description", "author", "published", "site", "image") if extracted.get(key)}
    page_title = (tree.findtext(".//title") or "").strip()
    outcome["evidence"].extend(["charset:" + str(encoding), f"html_chars:{len(html_text)}", f"extracted_chars:{len(markdown)}",
                                "page_title:" + page_title[:200]])

    from_html = classify.restrictions_from_html(tree, text, outcome["final_url"])
    if any(item["kind"] == "captcha" and item["confidence"] == "confirmed" for item in from_html):
        # 人机验证页常以 401/403 返回，此时状态码不代表登录或权限要求
        restrictions = [{**item, "confidence": "suspected"} for item in restrictions]
    restrictions += from_html
    kind, kind_evidence = classify.page_type(tree, text)
    outcome.update(content_type=kind, content_type_evidence=kind_evidence, restrictions=restrictions)
    mark("classify")

    if technical:
        outcome.update(status="failed", technical_reason=technical, error=f"HTTP {response.status_code}")
        return outcome
    server_error = classify.server_error_page(tree)
    if server_error:
        # 状态码为 200 的服务器程序错误页，不是正文
        outcome.update(status="failed", technical_reason="server_error_page", partial_body=markdown or None,
                       evidence=outcome["evidence"] + [server_error], error=f"页面输出程序错误（HTTP {response.status_code}）")
        return outcome
    short = len(text.strip()) < classify.SHORT_BODY_CHARS
    if restrictions:
        confirmed = any(item["confidence"] == "confirmed" for item in restrictions)
        if short or response.status_code in (401, 403, 451):
            # 限制页上的零星文字不是正文，只作为本次结果留存；限制页本身不能说明资料类型
            outcome.update(status="restricted", partial_body=markdown or None)
            if kind_evidence == ["extracted_body"]:
                outcome.update(content_type=None, content_type_evidence=[])
        elif confirmed:
            # 有明确限制时，取得的文字只是公开部分
            outcome.update(status="partial", partial_body=markdown)
        elif previous_chars and len(markdown) < previous_chars * 0.5:
            # 疑似受限且明显短于已有正文时，不用它覆盖已有正文
            outcome.update(status="partial", partial_body=markdown,
                           evidence=outcome["evidence"] + [f"shorter_than_current:{len(markdown)}<{previous_chars}"])
        else:
            _accept(outcome, markdown, summary_chars)
        return outcome
    shell = classify.js_shell(tree, text)
    if shell:
        outcome.update(status="failed", technical_reason="js_required", evidence=outcome["evidence"] + [shell])
        return outcome
    if not text.strip():
        outcome.update(status="failed", technical_reason="empty_extraction")
        return outcome
    _accept(outcome, markdown, summary_chars)
    return outcome


def _accept(outcome, markdown, summary_chars):
    """正文应至少包含搜索摘要的信息量；明显短于摘要时多为软 404、错误页或提取不全，不作为正文接受。"""
    if summary_chars and len(markdown) < summary_chars * SUMMARY_RATIO:
        outcome.update(status="partial", partial_body=markdown, technical_reason="shorter_than_summary",
                       evidence=outcome["evidence"] + [f"shorter_than_summary:{len(markdown)}<{summary_chars}"])
        return
    outcome.update(status="succeeded", body=markdown)
