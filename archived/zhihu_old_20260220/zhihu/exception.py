"""
知乎搜索模块 - 自定义异常

定义模块中使用的自定义异常类
"""


class ZhihuSearchError(Exception):
    """知乎搜索基础异常类"""
    pass


class ZhihuCookieError(ZhihuSearchError):
    """Cookie 相关错误"""
    pass


class ZhihuAuthError(ZhihuSearchError):
    """认证错误"""
    pass


class ZhihuRateLimitError(ZhihuSearchError):
    """请求频率限制错误"""
    pass


class ZhihuForbiddenError(ZhihuSearchError):
    """访问被禁止错误 (403)"""
    pass


class ZhihuNotFoundError(ZhihuSearchError):
    """内容未找到错误"""
    pass


class ZhihuParseError(ZhihuSearchError):
    """数据解析错误"""
    pass


class ZhihuNetworkError(ZhihuSearchError):
    """网络请求错误"""
    pass
