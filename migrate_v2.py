# -*- coding: utf-8 -*-
"""
数据库迁移脚本 - 升级到新的学习系统
创建新的类别库表和学习食物表
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app
from models import db, CategoryLibrary, LearnedFood, FoodImageSample, FoodRecognitionLog

def migrate():
    """执行数据库迁移"""
    with app.app_context():
        print("开始数据库迁移...")
        
        # 创建新表
        db.create_all()
        print("[OK] 新表创建完成")
        
        # 初始化类别库
        categories = [
            {'name': '蔬菜', 'name_en': 'vegetables', 'description': '各类新鲜蔬菜，富含维生素和膳食纤维'},
            {'name': '肉类', 'name_en': 'meat', 'description': '猪牛羊鸡等畜禽肉类，主要蛋白质来源'},
            {'name': '海鲜', 'name_en': 'seafood', 'description': '鱼、虾、蟹、贝类等水产品，富含优质蛋白'},
            {'name': '水果', 'name_en': 'fruit', 'description': '各类新鲜水果，富含维生素和矿物质'},
            {'name': '主食', 'name_en': 'staple', 'description': '米饭、面条、面包等碳水化合物主食'},
            {'name': '蛋类', 'name_en': 'egg', 'description': '鸡蛋、鸭蛋等各种蛋类食品'},
            {'name': '豆类', 'name_en': 'beans', 'description': '黄豆、豆腐、豆浆等豆制品'},
            {'name': '饮品', 'name_en': 'beverage', 'description': '牛奶、咖啡、茶等各种饮料'},
            {'name': '坚果', 'name_en': 'nuts', 'description': '花生、核桃、杏仁等坚果零食'},
            {'name': '其他', 'name_en': 'others', 'description': '其他未分类食物'},
        ]
        
        existing = CategoryLibrary.query.all()
        if not existing:
            for cat_data in categories:
                category = CategoryLibrary(**cat_data)
                db.session.add(category)
            db.session.commit()
            print(f"[OK] 创建了 {len(categories)} 个类别库")
        else:
            print(f"[OK] 类别库已存在，共 {len(existing)} 个")
        
        print("\n迁移完成！")
        print("\n新的学习系统特性：")
        print("1. 手动纠正识别结果")
        print("2. 学习2-3次后自动归档到类别库")
        print("3. 识别时优先匹配已学习的食物")
        print("4. 同类别食物特征对比")

if __name__ == '__main__':
    migrate()
