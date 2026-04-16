#!/bin/bash
# 在 PythonAnywhere Bash 控制台执行以下命令：

cd ~/ssy

# 拉取最新代码（分支是 main）
git pull origin main

# 如果没有设置 upstream，先获取所有分支
git fetch origin

# 重置到最新版本（如果本地有冲突）
git reset --hard origin/main

# 确保 mobile.css 存在
ls -la static/css/

# 重启 Web 应用
touch /var/www/caisa_pythonanywhere_com_wsgi.py

echo "部署完成！"
