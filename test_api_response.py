# -*- coding: utf-8 -*-
"""测试API完整响应"""

import sys
sys.path.insert(0, '/home/caisa/ssy')

from app import app, db
from flask import json
from PIL import Image
import io
import base64

def test_api():
    with app.test_client() as client:
        # 模拟登录
        with client.session_transaction() as sess:
            sess['_user_id'] = '1'
        
        # 创建一个红色测试图片
        img = Image.new('RGB', (100, 100), color='red')
        buffer = io.BytesIO()
        img.save(buffer, format='JPEG')
        img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        
        # 发送识别请求
        response = client.post('/api/recognize-food', 
            json={'image': img_base64},
            content_type='application/json'
        )
        
        result = response.get_json()
        
        print("=" * 60)
        print("完整API响应:")
        print("=" * 60)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        print("=" * 60)
        
        # 检查每个结果的关键字段
        print("\n结果详情:")
        for i, r in enumerate(result.get('results', [])):
            print(f"\n{i+1}. {r.get('name', 'N/A')}")
            print(f"   - confidence: {r.get('confidence')}")
            print(f"   - source: {r.get('source')}")
            print(f"   - category: {r.get('category')}")
            print(f"   - calories: {r.get('calories')}")
            print(f"   - learned_count: {r.get('learned_count')}")
            print(f"   - is_archived: {r.get('is_archived')}")

if __name__ == '__main__':
    test_api()
