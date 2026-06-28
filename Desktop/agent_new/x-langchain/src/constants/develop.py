# -*- coding: utf-8 -*-
"""
开发相关常量

本模块定义了开发过程中常用的常量，包括：
- HTTP 内容类型
- 加密算法
- 工作模式
- 填充方式
- 编码方式
"""

from typing import Final

# HTTP 内容类型
JSON_CONTENT_TYPE: Final[str] = "application/json"
FILE_CONTENT_TYPE: Final[str] = "application/octet-stream"
FORM_URL_ENCODED_CONTENT_TYPE: Final[str] = "application/x-www-form-urlencoded"
MULTIPART_FORM_DATA_CONTENT_TYPE: Final[str] = "multipart/form-data"

# 加密算法

# 单向加密算法（哈希算法）
MD5: Final[str] = "MD5"
SHA1: Final[str] = "SHA1"
SHA256: Final[str] = "SHA256"
SHA512: Final[str] = "SHA512"
SM3: Final[str] = "SM3"

# 对称加密算法
AES: Final[str] = "AES"
SM4: Final[str] = "SM4"
DES: Final[str] = "DES"
THREE_DES: Final[str] = "3DES"
CHACHA20: Final[str] = "ChaCha20"
RC4: Final[str] = "RC4"

# 非对称加密算法
RSA: Final[str] = "RSA"
ECC: Final[str] = "ECC"
DSA: Final[str] = "DSA"
SM2: Final[str] = "SM2"

# 工作模式常量
MODE_ECB: Final[str] = "ECB"
MODE_CBC: Final[str] = "CBC"
MODE_GCM: Final[str] = "GCM"

# 填充方式常量

# 对称加密中的块加密填充方式
PKCS7_PADDING: Final[str] = "PKCS7"
ISO10126_PADDING: Final[str] = "ISO10126"
NO_PADDING: Final[str] = "NoPadding"
ZERO_PADDING: Final[str] = "ZeroPadding"

# 非对称加密填充方式
PKCS1V15: Final[str] = "PKCS1v15"
OAEP: Final[str] = "OAEP"

# 编码方式常量
ENCODING_BASE64: Final[str] = "base64"
ENCODING_HEX: Final[str] = "hex"
