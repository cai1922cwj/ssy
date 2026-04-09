#!/usr/bin/env python
"""
PythonAnywhere 部署配置
熵食源 - 在线食物营养分析APP

部署步骤:
1. 在 PythonAnywhere 创建账号
2. 打开 Bash 控制台
3. 克隆 GitHub 仓库: git clone https://github.com/yourusername/entropy-food.git
4. 进入项目目录: cd entropy-food
5. 创建虚拟环境: mkvirtualenv --python=/usr/bin/python3.11 entropy-food
6. 安装依赖: pip install -r requirements.txt
7. 配置 Web 应用
"""

import os
import sys

# 添加项目路径到 Python 路径
path = '/home/yourusername/entropy-food'
if path not in sys.path:
    sys.path.insert(0, path)

# 设置应用入口
os.environ.setdefault('FLASK_APP', 'app.py')
os.environ.setdefault('FLASK_ENV', 'production')

from app import app as application

if __name__ == '__main__':
    application.run()
