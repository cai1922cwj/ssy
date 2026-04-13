# -*- coding: utf-8 -*-
"""
数据库迁移脚本 - 添加食物图片特征表
"""

from app import app
from models import db

with app.app_context():
    # 创建新表
    db.create_all()
    print("数据库表已更新")
    
    # 检查表是否存在
    from sqlalchemy import inspect
    inspector = inspect(db.engine)
    tables = inspector.get_table_names()
    
    if 'food_image_features' in tables:
        print("[OK] food_image_features 表创建成功")
    else:
        print("[ERROR] food_image_features 表未找到")
