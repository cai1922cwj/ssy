# -*- coding: utf-8 -*-
"""
修复数据库 - 删除旧数据库并重新创建
"""
import os
import sys

# 删除旧的数据库文件
db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'entropy_food.db')
if os.path.exists(db_path):
    os.remove(db_path)
    print(f"已删除旧数据库: {db_path}")
else:
    print("数据库文件不存在")

# 重新创建所有表
from app import app
from models import db

with app.app_context():
    db.create_all()
    print("数据库表已重新创建")
    
    # 验证表结构
    from sqlalchemy import inspect
    inspector = inspect(db.engine)
    tables = inspector.get_table_names()
    print(f"\n现有表: {tables}")
    
    # 检查 users 表的列
    if 'users' in tables:
        columns = inspector.get_columns('users')
        column_names = [col['name'] for col in columns]
        print(f"\nusers 表列: {column_names}")
        
        if 'is_admin' in column_names:
            print("[OK] is_admin 列已存在")
        else:
            print("[ERROR] is_admin 列不存在")

print("\n数据库修复完成！")
