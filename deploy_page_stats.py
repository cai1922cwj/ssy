"""PythonAnywhere 数据库修复脚本
在 PythonAnywhere Bash Console 中运行此脚本来创建 page_views 表
"""
from app import app, db
from models import PageView

with app.app_context():
    # 检查表是否存在，不存在则创建
    db.create_all()
    print("page_views 表创建完成！")
    
    # 验证
    count = PageView.query.count()
    print(f"当前页面访问记录数: {count}")
