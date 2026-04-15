# -*- coding: utf-8 -*-
"""模拟识别流程测试"""

import sys
sys.path.insert(0, 'c:/ssy')

from app import app, db
from models import LearnedFood
from local_image_recognition import recognize_food_local, extract_image_features

def test_recognition():
    with app.app_context():
        # 模拟一个测试图片的base64数据（用本地数据库中现有的食物图片）
        # 先查询是否有样本
        from models import FoodImageSample
        samples = FoodImageSample.query.limit(1).all()
        
        if samples:
            print(f"找到 {len(samples)} 个图片样本")
            sample = samples[0]
            print(f"样本所属食物: {sample.learned_food.food_name if sample.learned_food else 'N/A'}")
        else:
            print("没有找到图片样本")
        
        # 测试特征提取
        print("\n=== 测试特征提取 ===")
        # 创建一个简单的测试图片
        from PIL import Image
        import io
        import base64
        
        # 创建100x100的红色图片
        img = Image.new('RGB', (100, 100), color='red')
        buffer = io.BytesIO()
        img.save(buffer, format='JPEG')
        img_bytes = buffer.getvalue()
        img_base64 = base64.b64encode(img_bytes).decode('utf-8')
        
        features = extract_image_features(img_base64)
        print(f"特征提取结果: {features}")
        
        if features:
            print(f"颜色提示: {features.get('hsv_hint')}")
            print(f"HSV: {features.get('hsv')}")
            print(f"亮度: {features.get('brightness')}")
        
        # 测试识别（使用user_id=1）
        print("\n=== 测试识别 (user_id=1) ===")
        results = recognize_food_local(img_base64, top_n=5, user_id=1, db_session=db.session)
        print(f"识别结果: {results}")
        
        # 测试识别（不使用user_id）
        print("\n=== 测试识别 (user_id=None) ===")
        results_no_user = recognize_food_local(img_base64, top_n=5, user_id=None, db_session=None)
        print(f"识别结果: {results_no_user}")
        
        # 检查学习库查询
        print("\n=== 直接查询学习库 ===")
        learned = LearnedFood.query.filter_by(user_id=1, is_active=True).all()
        print(f"用户1的学习食物数量: {len(learned)}")
        for l in learned[:5]:
            print(f"  - {l.food_name} (category_id={l.category_id})")

if __name__ == '__main__':
    test_recognition()
