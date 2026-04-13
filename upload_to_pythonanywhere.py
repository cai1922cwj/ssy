#!/usr/bin/env python3
"""
生成 PythonAnywhere 文件上传指南
由于网络限制，需要手动上传以下文件
"""

files_to_upload = [
    {
        "local": "templates/base.html",
        "remote": "/home/caisa/ssy/templates/base.html",
        "desc": "基础模板（已添加缓存控制和版本号）"
    },
    {
        "local": "templates/index.html", 
        "remote": "/home/caisa/ssy/templates/index.html",
        "desc": "首页（移动端精简布局）"
    },
    {
        "local": "static/css/mobile.css",
        "remote": "/home/caisa/ssy/static/css/mobile.css", 
        "desc": "移动端样式文件"
    }
]

print("=" * 60)
print("PythonAnywhere 手动上传指南")
print("=" * 60)
print("\n请按以下步骤操作：\n")

print("1. 登录 https://www.pythonanywhere.com")
print("2. 点击顶部菜单 'Files'")
print("3. 进入对应目录，上传以下文件：\n")

for i, f in enumerate(files_to_upload, 1):
    print(f"   {i}. 本地文件: {f['local']}")
    print(f"      上传到: {f['remote']}")
    print(f"      说明: {f['desc']}\n")

print("4. 上传完成后，点击 'Web' 标签")
print("5. 点击 'Reload caisa.pythonanywhere.com'")
print("6. 手机上清除浏览器缓存后访问")
print("\n" + "=" * 60)
