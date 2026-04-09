"""
WSGI config for 熵食源 on PythonAnywhere.

It exposes the WSGI callable as a module-level variable named ``application``.
"""

import os
import sys

# 添加项目路径
path = os.path.dirname(os.path.abspath(__file__))
if path not in sys.path:
    sys.path.insert(0, path)

from app import app as application
