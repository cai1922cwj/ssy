# -*- coding: utf-8 -*-
"""测试本地图片识别"""

from local_image_recognition import recognize_food_local, extract_image_features
from PIL import Image
import io
import base64

# 创建测试图片 - 模拟全麦面包的颜色
test_colors = [
    ('全麦面包颜色', [160, 130, 90]),
    ('白面包颜色', [220, 190, 140]),
    ('米饭颜色', [240, 240, 230]),
    ('西红柿颜色', [220, 60, 40]),
    ('青菜颜色', [60, 140, 50]),
]

for name, color in test_colors:
    print(f"\n=== 测试 {name} {color} ===")
    img = Image.new('RGB', (100, 100), color=tuple(color))
    buf = io.BytesIO()
    img.save(buf, format='JPEG')
    img_str = base64.b64encode(buf.getvalue()).decode()
    
    # 提取特征
    features = extract_image_features(img_str)
    print(f"图片特征: 平均颜色={features['avg_color']}, 亮度={features['brightness']:.1f}")
    
    # 识别
    results = recognize_food_local(img_str)
    print("识别结果:")
    for r in results[:3]:
        print(f"  {r['name']}: {r['confidence']}% - {r['categories']}")
