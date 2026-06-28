# -*- coding: utf-8 -*-
"""
常量模块

本模块定义了项目中使用的各种常量。
"""

from .streaming_modes import STREAM_MODE_UPDATES, STREAM_MODE_CUSTOM, STREAM_MODE_MESSAGES
from .develop import (
    # HTTP 内容类型
    JSON_CONTENT_TYPE,
    FILE_CONTENT_TYPE,
    FORM_URL_ENCODED_CONTENT_TYPE,
    MULTIPART_FORM_DATA_CONTENT_TYPE,
    # 单向加密算法（哈希算法）
    MD5,
    SHA1,
    SHA256,
    SHA512,
    SM3,
    # 对称加密算法
    AES,
    SM4,
    DES,
    THREE_DES,
    CHACHA20,
    RC4,
    # 非对称加密算法
    RSA,
    ECC,
    DSA,
    SM2,
    # 工作模式
    MODE_ECB,
    MODE_CBC,
    MODE_GCM,
    # 对称加密填充方式
    PKCS7_PADDING,
    ISO10126_PADDING,
    NO_PADDING,
    ZERO_PADDING,
    # 非对称加密填充方式
    PKCS1V15,
    OAEP,
    # 编码方式
    ENCODING_BASE64,
    ENCODING_HEX,
)

__all__ = [
    # 流式传输模式
    "STREAM_MODE_UPDATES",
    "STREAM_MODE_CUSTOM",
    "STREAM_MODE_MESSAGES",
    # HTTP 内容类型
    "JSON_CONTENT_TYPE",
    "FILE_CONTENT_TYPE",
    "FORM_URL_ENCODED_CONTENT_TYPE",
    "MULTIPART_FORM_DATA_CONTENT_TYPE",
    # 单向加密算法（哈希算法）
    "MD5",
    "SHA1",
    "SHA256",
    "SHA512",
    "SM3",
    # 对称加密算法
    "AES",
    "SM4",
    "DES",
    "THREE_DES",
    "CHACHA20",
    "RC4",
    # 非对称加密算法
    "RSA",
    "ECC",
    "DSA",
    "SM2",
    # 工作模式
    "MODE_ECB",
    "MODE_CBC",
    "MODE_GCM",
    # 对称加密填充方式
    "PKCS7_PADDING",
    "ISO10126_PADDING",
    "NO_PADDING",
    "ZERO_PADDING",
    # 非对称加密填充方式
    "PKCS1V15",
    "OAEP",
    # 编码方式
    "ENCODING_BASE64",
    "ENCODING_HEX",
]
