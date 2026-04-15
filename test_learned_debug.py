# -*- coding: utf-8 -*-
"""测试学习库识别问题"""

import sys
sys.path.insert(0, 'c:/ssy')

from app import app, db
from models import LearnedFood, CategoryLibrary

def test_learned_foods():
    with app.app_context():
        # 查询用户1的所有学习食物
        user_id = 1
        learned_foods = LearnedFood.query.filter_by(
            user_id=user_id, 
            is_active=True
        ).all()
        
        print(f"=== 用户 {user_id} 的学习食物 ===")
        print(f"总共学习过: {len(learned_foods)} 种食物\n")
        
        for food in learned_foods:
            print(f"食物名称: {food.food_name}")
            print(f"  - 样本数量: {food.sample_count}")
            print(f"  - 确认次数: {food.confirmed_count}")
            print(f"  - 类别ID: {food.category_id}")
            print(f"  - 类别: {food.category.name if food.category else 'N/A'}")
            print(f"  - HSV: ({food.avg_hsv_h:.1f}, {food.avg_hsv_s:.1f}, {food.avg_hsv_v:.1f})")
            print(f"  - 亮度: {food.avg_brightness:.1f}")
            print(f"  - 边缘强度: {food.avg_edge_strength:.1f}")
            print(f"  - 颜色方差: {food.avg_color_variance:.1f}")
            print()
        
        # 检查类别库
        categories = CategoryLibrary.query.all()
        print(f"=== 类别库 ===")
        for cat in categories:
            print(f"{cat.id}: {cat.name} (包含 {cat.food_count} 种食物)")

if __name__ == '__main__':
    test_learned_foods()
