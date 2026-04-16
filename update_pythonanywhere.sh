#!/bin/bash
# PythonAnywhere 更新脚本
# 在 PythonAnywhere Bash 控制台中执行

cd ~/ssy

# 拉取最新代码
git pull origin master

# 激活虚拟环境
workon ssy

# 安装依赖（如有更新）
pip install -r requirements.txt

# 重启 Web 应用
touch /var/www/caisa_pythonanywhere_com_wsgi.py

echo "更新完成！"
