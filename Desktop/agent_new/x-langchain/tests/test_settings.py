# -*- coding: utf-8 -*-
"""
配置管理模块测试

测试配置管理模块的功能是否正常。
"""

import os
import sys
from unittest import TestCase, mock

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.config import settings

Settings = settings.__class__


class TestSettings(TestCase):
    """
    测试配置管理模块
    """

    def test_settings_initialization(self):
        """
        测试配置类初始化是否正常
        """
        with mock.patch.dict('os.environ', {}, clear=True):
            settings = Settings()
            # 验证配置类是否成功初始化
            self.assertIsInstance(settings, Settings)
            # 验证默认配置值
            self.assertEqual(settings.TEMPERATURE, 0.0)

    def test_settings_with_env_vars(self):
        """
        测试从环境变量加载配置
        """
        with mock.patch.dict('os.environ', {
            'DEEPSEEK_API_KEY': 'test_deepseek_key',
            'DEEPSEEK_MODEL_NAME': 'test_deepseek_model',
            'DOUBAO_API_KEY': 'test_doubao_key',
            'DOUBAO_MODEL_NAME': 'test_doubao_model',
            'ALIYUN_API_KEY': 'test_aliyun_key',
            'ALIYUN_MODEL_NAME': 'test_aliyun_model',
            'AMAP_API_KEY': 'test_amap_key',
            'TEMPERATURE': '0.5',
            'DEBUG': 'false'
        }, clear=True):
            settings = Settings()
            self.assertEqual(settings.DEEPSEEK_API_KEY, 'test_deepseek_key')
            self.assertEqual(settings.DEEPSEEK_MODEL_NAME, 'test_deepseek_model')
            self.assertEqual(settings.DOUBAO_API_KEY, 'test_doubao_key')
            self.assertEqual(settings.DOUBAO_MODEL_NAME, 'test_doubao_model')
            self.assertEqual(settings.ALIYUN_API_KEY, 'test_aliyun_key')
            self.assertEqual(settings.ALIYUN_MODEL_NAME, 'test_aliyun_model')
            self.assertEqual(settings.AMAP_API_KEY, 'test_amap_key')
            self.assertEqual(settings.TEMPERATURE, 0.5)
            self.assertFalse(settings.DEBUG)

    def test_validate_model_config_deepseek(self):
        """
        测试验证 DeepSeek 模型配置
        """
        with mock.patch.dict('os.environ', {
            'DEEPSEEK_API_KEY': 'test_key',
            'DEEPSEEK_MODEL_NAME': 'test_model'
        }, clear=True):
            settings = Settings()
            self.assertTrue(settings.validate_model_config('deepseek'))

    def test_validate_model_config_doubao(self):
        """
        测试验证豆包模型配置
        """
        with mock.patch.dict('os.environ', {
            'DOUBAO_API_KEY': 'test_key',
            'DOUBAO_MODEL_NAME': 'test_model'
        }, clear=True):
            settings = Settings()
            self.assertTrue(settings.validate_model_config('doubao'))

    def test_validate_model_config_tongyi(self):
        """
        测试验证阿里云通义千问模型配置
        """
        with mock.patch.dict('os.environ', {
            'ALIYUN_API_KEY': 'test_key',
            'ALIYUN_MODEL_NAME': 'test_model'
        }, clear=True):
            settings = Settings()
            self.assertTrue(settings.validate_model_config('tongyi'))

    def test_validate_model_config_mock(self):
        """
        测试验证 mock 模型配置
        """
        with mock.patch.dict('os.environ', {}, clear=True):
            settings = Settings()
            self.assertTrue(settings.validate_model_config('mock'))

    def test_validate_model_config_unsupported(self):
        """
        测试验证不支持的模型配置
        """
        with mock.patch.dict('os.environ', {}, clear=True):
            settings = Settings()
            self.assertFalse(settings.validate_model_config('unsupported'))

    def test_invalid_temperature(self):
        """
        测试温度参数无效时的处理
        """
        with mock.patch.dict('os.environ', {'TEMPERATURE': 'invalid'}, clear=True):
            settings = Settings()
            self.assertEqual(settings.TEMPERATURE, 0.0)

    def test_temperature_various_formats(self):
        """
        测试各种温度参数格式
        """
        test_cases = [
            ('0.5', 0.5),
            ('1.0', 1.0),
            ('0', 0.0),
            ('invalid', 0.0),
            ('', 0.0),
        ]
        for temp_str, expected in test_cases:
            with mock.patch.dict('os.environ', {'TEMPERATURE': temp_str}, clear=True):
                settings = Settings()
                self.assertEqual(settings.TEMPERATURE, expected)

    def test_debug_various_formats(self):
        """
        测试各种 DEBUG 参数格式
        """
        test_cases = [
            ('true', True),
            ('True', True),
            ('TRUE', True),
            ('false', False),
            ('False', False),
            ('FALSE', False),
        ]
        for debug_str, expected in test_cases:
            with mock.patch.dict('os.environ', {'DEBUG': debug_str}, clear=True):
                settings = Settings()
                self.assertEqual(settings.DEBUG, expected)


if __name__ == '__main__':
    import unittest
    unittest.main()
