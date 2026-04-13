"""
WSGI config for 熵食源 on PythonAnywhere.

It exposes the WSGI callable as a module-level variable named ``application``.
"""

import os
import sys

# 添加项目路径到 sys.path
path = '/home/caisa/ssy'
if path not in sys.path:
    sys.path.insert(0, path)

# 切换到项目目录
os.chdir(path)

# 设置环境变量
os.environ['SECRET_KEY'] = 'entropy-food-source-secret-key-2024'

# 导入应用（config.py 会自动使用绝对路径定位数据库）
from app import app as application
