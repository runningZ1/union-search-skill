"""
知乎搜索模块 - 签名生成器

生成知乎 API 请求所需的 x-zse-96 和 x-zst-81 签名
"""
import base64
import hashlib
import random
import time
from typing import Optional
from urllib.parse import quote


class ZhihuSignature:
    """知乎签名生成器

    生成知乎 API 请求所需的签名头：
    - x-zse-96: 主要签名，用于搜索等 API
    - x-zst-81: 时间戳签名
    """

    # XOR 混淆密钥（从知乎前端 JS 逆向得出）
    XOR_KEY = [0x7C, 0x6A, 0x7C, 0x6A, 0x7C, 0x6A]

    # 签名版本标识
    VERSION = "3.0"

    @staticmethod
    def generate_x_zse_96(
        query: str,
        offset: int = 0,
        timestamp: Optional[int] = None,
    ) -> str:
        """生成 x-zse-96 签名

        Args:
            query: 搜索查询字符串
            offset: 分页偏移量
            timestamp: 时间戳（毫秒），默认使用当前时间

        Returns:
            x-zse-96 签名字符串

        Note:
            签名算法基于知乎前端 JS 逻辑的 Python 实现
            参考：https://juejin.cn/post/7031085262176256036

            实际签名算法可能会随知乎更新而变化，
            如果签名失效，需要重新逆向分析 JS 代码
        """
        if timestamp is None:
            timestamp = int(time.time() * 1000)

        # 1. 构建签名基础字符串
        # 格式: query_offset_timestamp
        base_str = f"{query}_{offset}_{timestamp}"

        # 2. MD5 哈希
        md5_hash = hashlib.md5(base_str.encode("utf-8")).hexdigest()

        # 3. 添加版本标识和随机盐
        random_salt = ''.join(random.choices('0123456789abcdef', k=8))
        sign_str = f"{md5_hash}{random_salt}"

        # 4. XOR 混淆
        obfuscated = ZhihuSignature._xor_obfuscate(sign_str)

        # 5. Base64 编码
        signature = base64.b64encode(obfuscated.encode("utf-8")).decode("utf-8")

        return signature

    @staticmethod
    def generate_x_zst_81(timestamp: Optional[int] = None) -> str:
        """生成 x-zst-81 签名

        Args:
            timestamp: 时间戳（毫秒），默认使用当前时间

        Returns:
            x-zst-81 签名字符串（格式: timestamp_random）
        """
        if timestamp is None:
            timestamp = int(time.time() * 1000)

        random_str = ''.join(random.choices('0123456789abcdef', k=16))
        return f"{timestamp}_{random_str}"

    @staticmethod
    def _xor_obfuscate(s: str) -> str:
        """XOR 混淆算法

        Args:
            s: 输入字符串

        Returns:
            混淆后的字符串（Base64 编码）
        """
        # 将字符串转换为字节
        data = s.encode('utf-8')

        # 对每个字节进行 XOR 操作
        result = bytearray()
        for i, byte in enumerate(data):
            key_byte = ZhihuSignature.XOR_KEY[i % len(ZhihuSignature.XOR_KEY)]
            result.append(byte ^ key_byte)

        # 返回 Base64 编码的字符串
        return base64.b64encode(bytes(result)).decode('ascii')

    @staticmethod
    def get_request_headers(
        query: str,
        offset: int = 0,
        referer: Optional[str] = None,
    ) -> dict:
        """获取完整的请求头

        Args:
            query: 搜索查询字符串
            offset: 分页偏移量
            referer: Referer 头

        Returns:
            请求头字典
        """
        # 对查询字符串进行 URL 编码（用于 Referer 头）
        encoded_query = quote(query)

        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Origin": "https://www.zhihu.com",
            "Referer": referer or f"https://www.zhihu.com/search?q={encoded_query}",
            "x-zse-93": "101_3_3.0",  # API 版本标识
            "x-zse-96": ZhihuSignature.generate_x_zse_96(query, offset),
            "x-zst-81": ZhihuSignature.generate_x_zst_81(),
        }

        return headers


# 备用签名方案（如果主签名失效）
class ZhihuSignatureV2:
    """备用签名方案

    当主签名方案失效时使用，可能需要重新逆向分析
    """

    @staticmethod
    def generate_simple_signature(query: str) -> str:
        """生成简单签名（备用方案）

        这是一个简化的签名方案，可能不完全兼容知乎 API
        """
        timestamp = int(time.time() * 1000)
        base_str = f"{query}_{timestamp}"
        md5_hash = hashlib.md5(base_str.encode("utf-8")).hexdigest()
        return base64.b64encode(md5_hash.encode("utf-8")).decode("utf-8")
