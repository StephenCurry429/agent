#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
启动脚本 - 解决 Python 路径问题
"""

import sys
import os

# 加载 .env 文件（优先从外层目录加载）
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".env"))

# 获取当前脚本所在目录
current_dir = os.path.dirname(os.path.abspath(__file__))

# 添加项目 lib 目录到路径（包含依赖包）
lib_dir = os.path.join(current_dir, 'lib')
if lib_dir not in sys.path:
    sys.path.insert(0, lib_dir)

# 添加项目 src 目录到路径
src_dir = os.path.join(current_dir, 'src')
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

# 运行主程序
from main import main

if __name__ == "__main__":
    main()
