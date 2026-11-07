import importlib

# 预处理模块的接入位置，键为内容类型（video、podcast、pdf），值为模块路径；模块在执行器首次用到时才加载。
# 模块提供 process(document: dict, hits: list[dict], staging_dir: pathlib.Path, timeout: int) -> dict
# document 是 documents 表的整行（含 url、body_hash、body_etag、body_last_modified），hits 是该资料的全部搜索命中。
# 返回字段：
#   status          succeeded / partial / restricted / failed / not_modified
#   body            Markdown 正文；partial 时为取得的部分；其他状态为 None
#   extractor       模块名与版本，必填
#   metadata        dict，例如标题、作者、页数；没有时为 {}
#   technical_reason、error、http_status、final_url、response_type、restrictions、evidence、etag、last_modified  可选
# 未注册模块的视频和播客记为 pending_preprocess，保留搜索命中的原始元数据，不发起网络请求。
PREPROCESSORS = {
    "pdf": "library.preprocessors.pdf",
}


def load(content_type):
    return importlib.import_module(PREPROCESSORS[content_type]).process
