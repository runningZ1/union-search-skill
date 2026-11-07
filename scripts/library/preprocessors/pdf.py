import multiprocessing
import os
import threading
import time
import traceback
import uuid
from pathlib import Path

import pymupdf
import pymupdf4llm
from curl_cffi import requests as curl_requests
from curl_cffi.requests.exceptions import RequestException, Timeout

from library import classify
from library.fetcher import decode_html

MAX_PDF_BYTES = 100 * 1024 * 1024
PDF_SIGNATURE = b"%PDF-"
# 使用文字层直接转换；layout 模式逐页运行版面模型，多个任务并发时 CPU 耗时成倍增加
pymupdf4llm.use_layout(False)
EXTRACTOR = f"pymupdf4llm {pymupdf4llm.__version__} text"
# 转换在独立进程中执行：pymupdf4llm 的转换持有 Python 解释器锁，放在执行器线程里会拖慢所有并发项
CONVERT_PROCESSES = max(2, (os.cpu_count() or 4) // 4)


class ConvertTimeout(Exception):
    pass


def _serve(conn):
    # 转换进程的主循环：逐个接收暂存文件路径，返回转换结论；父进程关闭管道时退出
    while True:
        try:
            path = conn.recv()
        except EOFError:
            return
        try:
            conn.send(("ok", _convert(path)))
        except Exception:
            conn.send(("error", traceback.format_exc()))


class _Converter:
    """常驻转换进程，首次用到时启动；超过时限的转换连同进程一起终止。"""

    def __init__(self):
        context = multiprocessing.get_context("spawn")
        self.conn, child = context.Pipe()
        self.process = context.Process(target=_serve, args=(child,), daemon=True)
        self.process.start()
        child.close()

    def convert(self, path, timeout):
        self.conn.send(path)
        if not self.conn.poll(timeout):
            raise ConvertTimeout(f"PDF 转换超过 {timeout} 秒")
        kind, value = self.conn.recv()
        if kind == "error":
            raise RuntimeError("PDF 转换进程出错:\n" + value)
        return value

    def kill(self):
        self.process.kill()
        self.process.join()
        self.conn.close()


class ConverterPool:
    """最多 size 个常驻转换进程。等待空闲进程的时间不计入转换时限；
    转换超时或出错的进程被终止，下次需要时重新启动。"""

    def __init__(self, size):
        self.size = size
        self.idle = []
        self.started = 0
        self.changed = threading.Condition()

    def _acquire(self):
        with self.changed:
            while not self.idle and self.started >= self.size:
                self.changed.wait()
            if self.idle:
                return self.idle.pop()
            self.started += 1
        try:
            return _Converter()
        except BaseException:
            self._discard()
            raise

    def _discard(self):
        with self.changed:
            self.started -= 1
            self.changed.notify()

    def convert(self, path, timeout):
        converter = self._acquire()
        try:
            result = converter.convert(path, timeout)
        except BaseException:
            converter.kill()
            self._discard()
            raise
        with self.changed:
            self.idle.append(converter)
            self.changed.notify()
        return result


CONVERTERS = ConverterPool(CONVERT_PROCESSES)


def _convert(path):
    """在转换进程中打开 PDF 并转为 Markdown；返回结论与证据，不访问网络。"""
    try:
        pdf = pymupdf.open(path, filetype="pdf")
    except (pymupdf.FileDataError, pymupdf.EmptyFileError) as exc:
        return {"kind": "invalid", "error": f"响应不是可解析的 PDF: {exc}"}
    with pdf:
        if pdf.needs_pass:
            return {"kind": "encrypted"}
        metadata = _metadata(pdf)
        text_chars = sum(len(page.get_text().strip()) for page in pdf)
        evidence = [f"pages:{pdf.page_count}", f"text_layer_chars:{text_chars}"]
        if text_chars == 0:
            return {"kind": "no_text_layer", "metadata": metadata, "evidence": evidence}
        return {"kind": "converted", "metadata": metadata, "evidence": evidence,
                "markdown": pymupdf4llm.to_markdown(pdf, show_progress=False)}


class DownloadTimeout(Exception):
    pass


def _download(url, timeout, headers):
    # 流式下载时 curl 的 timeout 不限制整个传输，按下载开始时间另设总时限
    deadline = time.monotonic() + timeout
    response = curl_requests.get(url, headers=headers, timeout=timeout, impersonate="chrome", allow_redirects=True, stream=True)
    chunks = []
    size = 0
    for chunk in response.iter_content():
        size += len(chunk)
        if size > MAX_PDF_BYTES:
            response.close()
            raise ValueError(f"PDF 超过 {MAX_PDF_BYTES} 字节")
        if time.monotonic() > deadline:
            response.close()
            raise DownloadTimeout(f"PDF 下载超过 {timeout} 秒（已收到 {size} 字节）")
        chunks.append(chunk)
    response.close()
    return response, b"".join(chunks)


def _not_pdf(result, payload):
    mime = result["response_type"] or ""
    failed = {**result, "status": "failed", "technical_reason": "not_pdf", "error": f"响应不是 PDF（{mime or '无类型'}）"}
    if classify.type_from_response(mime) is not None:
        return failed
    html_text, _ = decode_html(payload, mime)
    tree = classify.parse_html(html_text)
    if tree is None:
        return failed
    text = tree.text_content().strip()
    restrictions = classify.restrictions_from_html(tree, text, result["final_url"])
    title = (tree.findtext(".//title") or "").strip()
    evidence = ["response_not_pdf", "page_title:" + title[:200]]
    if restrictions:
        return {**result, "status": "restricted", "restrictions": restrictions, "evidence": evidence,
                "error": "返回的是受限页面，不是 PDF"}
    return {**failed, "evidence": evidence}


def _metadata(pdf):
    info = pdf.metadata or {}
    values = {"title": info.get("title"), "author": info.get("author"), "published": info.get("creationDate"), "page_count": pdf.page_count}
    return {key: value for key, value in values.items() if value}


def process(document, hits, staging_dir, timeout):
    """下载 PDF 并把文字层转为 Markdown。扫描件没有文字层时记为失败，不做 OCR。"""
    result = {"status": None, "body": None, "metadata": {}, "extractor": EXTRACTOR, "error": None, "technical_reason": None,
              "http_status": None, "final_url": document["fetch_url"],"response_type": None, "restrictions": [], "evidence": [],
              "etag": None, "last_modified": None}
    headers = {}
    # 已有正文由当前提取器生成时才发条件请求；提取器变化后需要重新下载并转换
    if document["body_hash"] and document["body_extractor"] == EXTRACTOR:
        if document["body_etag"]:
            headers["If-None-Match"] = document["body_etag"]
        if document["body_last_modified"]:
            headers["If-Modified-Since"] = document["body_last_modified"]
    try:
        response, payload = _download(document["fetch_url"], timeout, headers)
    except (Timeout, DownloadTimeout) as exc:
        return {**result, "status": "failed", "technical_reason": "timeout", "error": str(exc)}
    except RequestException as exc:
        return {**result, "status": "failed", "technical_reason": "network_error", "error": str(exc)}
    except ValueError as exc:
        return {**result, "status": "failed", "technical_reason": "too_large", "error": str(exc)}
    result.update(http_status=response.status_code, final_url=str(response.url), response_type=response.headers.get("content-type"),
                  etag=response.headers.get("etag"), last_modified=response.headers.get("last-modified"))
    if response.status_code == 304:
        return {**result, "status": "not_modified", "evidence": ["http_status:304"]}
    restrictions, technical = classify.restrictions_from_status(response.status_code)
    if restrictions or technical:
        return {**result, "status": "restricted" if restrictions else "failed", "restrictions": restrictions,
                "technical_reason": technical, "error": f"HTTP {response.status_code}"}
    if PDF_SIGNATURE not in payload[:1024]:
        # PyMuPDF 也能打开 HTML，必须先按文件签名确认是 PDF；验证页、登录页等交给限制分类
        return _not_pdf(result, payload)
    # 下载内容经暂存文件交给转换进程，避免大文件在进程间复制
    staging = Path(staging_dir) / f"pdf-{uuid.uuid4().hex}.pdf"
    staging.write_bytes(payload)
    try:
        converted = CONVERTERS.convert(str(staging), timeout)
    except ConvertTimeout as exc:
        return {**result, "status": "failed", "technical_reason": "timeout", "evidence": [f"pdf_bytes:{len(payload)}"], "error": str(exc)}
    finally:
        staging.unlink()
    if converted["kind"] == "invalid":
        return {**result, "status": "failed", "technical_reason": "not_pdf", "error": converted["error"]}
    if converted["kind"] == "encrypted":
        return {**result, "status": "failed", "technical_reason": "encrypted", "error": "PDF 需要密码"}
    result["metadata"] = converted["metadata"]
    result["evidence"] = [f"pdf_bytes:{len(payload)}"] + converted["evidence"]
    if converted["kind"] == "no_text_layer":
        return {**result, "status": "failed", "technical_reason": "no_text_layer", "error": "PDF 没有文字层"}
    markdown = converted["markdown"]
    if not markdown.strip():
        return {**result, "status": "failed", "technical_reason": "empty_extraction"}
    return {**result, "status": "succeeded", "body": markdown}
