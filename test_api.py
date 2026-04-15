#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试学习API
"""
import sys
sys.path.insert(0, '/home/caisa/ssy')

from app import app
from models import db, CategoryLibrary
import base64

# 创建一个简单的测试图片 (1x1像素的PNG)
test_image_base64 = 'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=='

with app.app_context():
    print("=" * 50)
    print("测试学习API")
    print("=" * 50)
    
    # 1. 检查类别
    print("\n1. 检查类别库...")
    categories = CategoryLibrary.query.all()
    print(f"   找到 {len(categories)} 个类别")
    
    # 2. 测试save_food_sample函数
    print("\n2. 测试save_food_sample函数...")
    try:
        from local_image_recognition import save_food_sample
        
        result = save_food_sample(
            test_image_base64,
            '测试蚕豆',
            '豆类',
            1,  # user_id
            db.session
        )
        
        print(f"   结果: {result}")
        
        if result['success']:
            print("   [OK] 学习成功!")
        else:
            print(f"   [FAIL] 学习失败: {result.get('message', '未知错误')}")
    except Exception as e:
        print(f"   [ERROR] {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 50)
    print("测试完成")
    print("=" * 50)
