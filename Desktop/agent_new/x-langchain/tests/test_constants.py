# -*- coding: utf-8 -*-
"""
常量模块测试

测试常量模块的功能是否正常。
"""

import os
import sys
from unittest import TestCase

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from constants.develop import (
    JSON_CONTENT_TYPE,
    FILE_CONTENT_TYPE,
    FORM_URL_ENCODED_CONTENT_TYPE,
    MULTIPART_FORM_DATA_CONTENT_TYPE,
    MD5, SHA1, SHA256, SHA512, SM3,
    AES, SM4, DES, THREE_DES, CHACHA20, RC4,
    RSA, ECC, DSA, SM2,
    MODE_ECB, MODE_CBC, MODE_GCM,
    PKCS7_PADDING, ISO10126_PADDING, NO_PADDING, ZERO_PADDING,
    PKCS1V15, OAEP,
    ENCODING_BASE64, ENCODING_HEX
)
from constants.streaming_modes import (
    STREAM_MODE_UPDATES,
    STREAM_MODE_CUSTOM,
    STREAM_MODE_MESSAGES,
    DEFAULT_STREAM_MODES
)


class TestConstants(TestCase):
    """
    测试常量模块
    """

    def test_http_content_types(self):
        """
        测试 HTTP 内容类型常量
        """
        self.assertEqual(JSON_CONTENT_TYPE, "application/json")
        self.assertEqual(FILE_CONTENT_TYPE, "application/octet-stream")
        self.assertEqual(FORM_URL_ENCODED_CONTENT_TYPE, "application/x-www-form-urlencoded")
        self.assertEqual(MULTIPART_FORM_DATA_CONTENT_TYPE, "multipart/form-data")

    def test_hash_algorithms(self):
        """
        测试哈希算法常量
        """
        self.assertEqual(MD5, "MD5")
        self.assertEqual(SHA1, "SHA1")
        self.assertEqual(SHA256, "SHA256")
        self.assertEqual(SHA512, "SHA512")
        self.assertEqual(SM3, "SM3")

    def test_symmetric_algorithms(self):
        """
        测试对称加密算法常量
        """
        self.assertEqual(AES, "AES")
        self.assertEqual(SM4, "SM4")
        self.assertEqual(DES, "DES")
        self.assertEqual(THREE_DES, "3DES")
        self.assertEqual(CHACHA20, "ChaCha20")
        self.assertEqual(RC4, "RC4")

    def test_asymmetric_algorithms(self):
        """
        测试非对称加密算法常量
        """
        self.assertEqual(RSA, "RSA")
        self.assertEqual(ECC, "ECC")
        self.assertEqual(DSA, "DSA")
        self.assertEqual(SM2, "SM2")

    def test_work_modes(self):
        """
        测试工作模式常量
        """
        self.assertEqual(MODE_ECB, "ECB")
        self.assertEqual(MODE_CBC, "CBC")
        self.assertEqual(MODE_GCM, "GCM")

    def test_padding_modes(self):
        """
        测试填充方式常量
        """
        self.assertEqual(PKCS7_PADDING, "PKCS7")
        self.assertEqual(ISO10126_PADDING, "ISO10126")
        self.assertEqual(NO_PADDING, "NoPadding")
        self.assertEqual(ZERO_PADDING, "ZeroPadding")

    def test_asymmetric_padding(self):
        """
        测试非对称加密填充方式常量
        """
        self.assertEqual(PKCS1V15, "PKCS1v15")
        self.assertEqual(OAEP, "OAEP")

    def test_encoding_modes(self):
        """
        测试编码方式常量
        """
        self.assertEqual(ENCODING_BASE64, "base64")
        self.assertEqual(ENCODING_HEX, "hex")

    def test_streaming_modes(self):
        """
        测试流式模式常量
        """
        self.assertEqual(STREAM_MODE_UPDATES, "updates")
        self.assertEqual(STREAM_MODE_CUSTOM, "custom")
        self.assertEqual(STREAM_MODE_MESSAGES, "messages")
        self.assertEqual(DEFAULT_STREAM_MODES, ["updates", "custom", "messages"])


if __name__ == '__main__':
    import unittest
    unittest.main()
