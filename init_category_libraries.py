# -*- coding: utf-8 -*-
"""
初始化类别库
运行此脚本创建默认的类别库
"""

import os
import sys

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app
from models import db, CategoryLibrary

def init_category_libraries():
    """初始化默认类别库"""
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
    
    with app.app_context():
        # 检查是否已有数据
        existing = CategoryLibrary.query.all()
        if existing:
            print(f"类别库已存在，共 {len(existing)} 个类别")
            return
        
        for cat_data in categories:
            category = CategoryLibrary(**cat_data)
            db.session.add(category)
        
        db.session.commit()
        print(f"成功创建 {len(categories)} 个类别库")

if __name__ == '__main__':
    init_category_libraries()
