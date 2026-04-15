#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试学习功能
"""
import sys
sys.path.insert(0, '/home/caisa/ssy')

from app import app
from models import db, CategoryLibrary, LearnedFood, FoodImageSample

with app.app_context():
    print("=" * 50)
    print("测试学习功能")
    print("=" * 50)
    
    # 1. 检查类别库
    print("\n1. 检查类别库...")
    categories = CategoryLibrary.query.all()
    print(f"   找到 {len(categories)} 个类别")
    for c in categories:
        print(f"      - {c.name} (ID: {c.id})")
    
    # 2. 检查表结构
    print("\n2. 检查表结构...")
    from sqlalchemy import inspect
    inspector = inspect(db.engine)
    tables = inspector.get_table_names()
    for t in ['category_libraries', 'learned_foods', 'food_image_samples']:
        if t in tables:
            cols = [c['name'] for c in inspector.get_columns(t)]
            print(f"   [OK] {t}: {', '.join(cols[:5])}...")
        else:
            print(f"   [FAIL] {t} 不存在!")
    
    # 3. 测试插入
    print("\n3. 测试插入数据...")
    try:
        # 查找豆类
        category = CategoryLibrary.query.filter_by(name='豆类').first()
        if category:
            print(f"   找到类别: {category.name} (ID: {category.id})")
            
            # 创建测试学习记录
            test_learned = LearnedFood(
                user_id=1,
                category_id=category.id,
                food_name='测试蚕豆',
                food_name_normalized='测试蚕豆',
                sample_count=1,
                confirmed_count=1
            )
            db.session.add(test_learned)
            db.session.flush()
            print(f"   创建学习记录 ID: {test_learned.id}")
            
            # 创建测试样本
            test_sample = FoodImageSample(
                learned_food_id=test_learned.id,
                user_id=1,
                hsv_h=100.0,
                hsv_s=0.5,
                hsv_v=0.8,
                brightness=150.0,
                edge_strength=0.3,
                edge_density=0.2,
                color_variance=0.1,
                image_hash='test_hash_123'
            )
            db.session.add(test_sample)
            print(f"   创建样本记录")
            
            # 提交
            db.session.commit()
            print("   [OK] 数据提交成功")
            
            # 清理测试数据
            db.session.delete(test_sample)
            db.session.delete(test_learned)
            db.session.commit()
            print("   [OK] 测试数据已清理")
        else:
            print("   [FAIL] 找不到'豆类'类别")
    except Exception as e:
        db.session.rollback()
        print(f"   [FAIL] 错误: {e}")
        import traceback
        print(traceback.format_exc())
    
    print("\n" + "=" * 50)
    print("测试完成")
    print("=" * 50)
