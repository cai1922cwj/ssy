"""
百度 AI 菜品识别服务
需要先在百度智能云创建应用获取 API Key 和 Secret Key
"""
import requests
import base64
import json
from flask import current_app

class BaiduFoodRecognition:
    """百度菜品识别 API"""
    
    def __init__(self, api_key=None, secret_key=None):
        self.api_key = api_key or current_app.config.get('BAIDU_API_KEY')
        self.secret_key = secret_key or current_app.config.get('BAIDU_SECRET_KEY')
        self.access_token = None
        
    def get_access_token(self):
        """获取百度 AI access token"""
        if self.access_token:
            return self.access_token
            
        url = "https://aip.baidubce.com/oauth/2.0/token"
        params = {
            "grant_type": "client_credentials",
            "client_id": self.api_key,
            "client_secret": self.secret_key
        }
        
        try:
            response = requests.post(url, params=params, timeout=10)
            result = response.json()
            
            # 检查是否有错误
            if 'error' in result:
                print(f"获取百度token错误: {result}")
                return None
                
            self.access_token = result.get('access_token')
            if self.access_token:
                print(f"成功获取百度token: {self.access_token[:20]}...")
                return self.access_token
            else:
                print(f"获取token失败，响应: {result}")
                return None
        except Exception as e:
            print(f"获取百度token失败: {e}")
            import traceback
            print(traceback.format_exc())
            return None
    
    def recognize_dish(self, image_data):
        """
        识别菜品
        image_data: base64编码的图片数据（不含data:image前缀）
        返回: 识别结果列表
        """
        access_token = self.get_access_token()
        print(f"access_token: {access_token[:30] if access_token else 'None'}...")
        if not access_token:
            print("无法获取access_token，跳过识别")
            return None
            
        url = f"https://aip.baidubce.com/rest/2.0/image-classify/v2/dish"
        params = {"access_token": access_token}
        
        # 图片数据
        data = {"image": image_data, "top_num": 5}
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        
        try:
            print(f"发送识别请求，图片数据长度: {len(image_data)}")
            response = requests.post(url, data=data, params=params, headers=headers, timeout=15)
            print(f"响应状态码: {response.status_code}")
            print(f"响应内容: {response.text[:500]}")
            
            result = response.json()
            
            # 检查错误
            if 'error_code' in result:
                print(f"百度API错误: {result.get('error_msg')}")
                return None
            
            if 'result' in result:
                # 不过滤，返回所有结果
                dishes = []
                for item in result['result']:
                    dishes.append({
                        'name': item.get('name', '未知'),
                        'confidence': round(item.get('probability', 0) * 100, 1),
                        'calorie': item.get('calorie', ''),
                        'has_calorie': item.get('has_calorie', False)
                    })
                print(f"识别到 {len(dishes)} 个菜品")
                return dishes
            return []
            
        except Exception as e:
            print(f"识别失败: {e}")
            import traceback
            print(traceback.format_exc())
            return None
    
    def recognize_ingredient(self, image_data):
        """
        识别果蔬/食材
        用于识别原材料而非菜品
        """
        access_token = self.get_access_token()
        if not access_token:
            return None
            
        url = f"https://aip.baidubce.com/rest/2.0/image-classify/v1/classify/ingredient"
        params = {"access_token": access_token}
        
        data = {"image": image_data, "top_num": 5}
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        
        try:
            response = requests.post(url, data=data, params=params, headers=headers, timeout=15)
            result = response.json()
            
            if 'result' in result:
                ingredients = []
                for item in result['result']:
                    if item.get('score', 0) > 0.3:
                        ingredients.append({
                            'name': item.get('name', '未知'),
                            'confidence': round(item.get('score', 0) * 100, 1)
                        })
                return ingredients
            return []
            
        except Exception as e:
            print(f"识别失败: {e}")
            return None


# 食物营养数据库（补充常见食物）
FOOD_NUTRITION_DB = {
    # 主食类
    '米饭': {'calories': 116, 'protein': 2.6, 'carbs': 25.9, 'fat': 0.3, 'category': '主食'},
    '白米饭': {'calories': 116, 'protein': 2.6, 'carbs': 25.9, 'fat': 0.3, 'category': '主食'},
    '糙米饭': {'calories': 111, 'protein': 2.6, 'carbs': 23.0, 'fat': 0.9, 'category': '主食'},
    '馒头': {'calories': 223, 'protein': 7.0, 'carbs': 47.0, 'fat': 1.1, 'category': '主食'},
    '花卷': {'calories': 214, 'protein': 6.4, 'carbs': 45.0, 'fat': 1.1, 'category': '主食'},
    '包子': {'calories': 227, 'protein': 7.5, 'carbs': 46.0, 'fat': 1.8, 'category': '主食'},
    '肉包': {'calories': 230, 'protein': 8.5, 'carbs': 42.0, 'fat': 4.2, 'category': '主食'},
    '菜包': {'calories': 180, 'protein': 5.5, 'carbs': 38.0, 'fat': 1.2, 'category': '主食'},
    '面条': {'calories': 137, 'protein': 4.5, 'carbs': 28.5, 'fat': 0.5, 'category': '主食'},
    '拉面': {'calories': 145, 'protein': 5.0, 'carbs': 30.0, 'fat': 0.8, 'category': '主食'},
    '刀削面': {'calories': 140, 'protein': 4.8, 'carbs': 29.0, 'fat': 0.6, 'category': '主食'},
    '意大利面': {'calories': 131, 'protein': 5.0, 'carbs': 25.0, 'fat': 1.1, 'category': '主食'},
    '面包': {'calories': 265, 'protein': 9.0, 'carbs': 49.0, 'fat': 3.2, 'category': '主食'},
    '全麦面包': {'calories': 247, 'protein': 13.0, 'carbs': 41.0, 'fat': 3.4, 'category': '主食'},
    '吐司': {'calories': 264, 'protein': 8.0, 'carbs': 49.0, 'fat': 3.2, 'category': '主食'},
    '三明治': {'calories': 250, 'protein': 10.0, 'carbs': 35.0, 'fat': 8.0, 'category': '主食'},
    '汉堡': {'calories': 295, 'protein': 13.0, 'carbs': 30.0, 'fat': 14.0, 'category': '主食'},
    '煎饼': {'calories': 289, 'protein': 6.0, 'carbs': 45.0, 'fat': 9.0, 'category': '主食'},
    '油条': {'calories': 388, 'protein': 6.5, 'carbs': 51.0, 'fat': 18.0, 'category': '主食'},
    '烧饼': {'calories': 268, 'protein': 7.0, 'carbs': 48.0, 'fat': 5.5, 'category': '主食'},
    '燕麦': {'calories': 389, 'protein': 16.9, 'carbs': 66.3, 'fat': 6.9, 'category': '主食'},
    '燕麦片': {'calories': 377, 'protein': 13.2, 'carbs': 68.0, 'fat': 6.5, 'category': '主食'},
    '玉米': {'calories': 86, 'protein': 3.2, 'carbs': 19.0, 'fat': 1.2, 'category': '主食'},
    '玉米棒': {'calories': 86, 'protein': 3.2, 'carbs': 19.0, 'fat': 1.2, 'category': '主食'},
    '红薯': {'calories': 86, 'protein': 1.6, 'carbs': 20.1, 'fat': 0.1, 'category': '主食'},
    '紫薯': {'calories': 82, 'protein': 1.3, 'carbs': 18.0, 'fat': 0.2, 'category': '主食'},
    '土豆': {'calories': 77, 'protein': 2.0, 'carbs': 17.5, 'fat': 0.1, 'category': '主食'},
    '小米粥': {'calories': 46, 'protein': 1.4, 'carbs': 9.3, 'fat': 0.3, 'category': '主食'},
    '大米粥': {'calories': 35, 'protein': 0.8, 'carbs': 7.8, 'fat': 0.1, 'category': '主食'},
    '八宝粥': {'calories': 85, 'protein': 2.5, 'carbs': 18.0, 'fat': 0.5, 'category': '主食'},
    '馄饨': {'calories': 150, 'protein': 6.0, 'carbs': 25.0, 'fat': 3.5, 'category': '主食'},
    '饺子': {'calories': 220, 'protein': 8.0, 'carbs': 35.0, 'fat': 5.5, 'category': '主食'},
    '水饺': {'calories': 220, 'protein': 8.0, 'carbs': 35.0, 'fat': 5.5, 'category': '主食'},
    '蒸饺': {'calories': 210, 'protein': 7.8, 'carbs': 33.0, 'fat': 5.2, 'category': '主食'},
    '煎饺': {'calories': 268, 'protein': 8.0, 'carbs': 32.0, 'fat': 12.0, 'category': '主食'},
    '春卷': {'calories': 250, 'protein': 5.0, 'carbs': 30.0, 'fat': 12.0, 'category': '主食'},
    '粽子': {'calories': 200, 'protein': 4.5, 'carbs': 40.0, 'fat': 2.5, 'category': '主食'},
    '汤圆': {'calories': 230, 'protein': 4.0, 'carbs': 48.0, 'fat': 2.0, 'category': '主食'},
    '年糕': {'calories': 154, 'protein': 3.3, 'carbs': 34.0, 'fat': 0.6, 'category': '主食'},
    '米粉': {'calories': 109, 'protein': 2.0, 'carbs': 25.0, 'fat': 0.3, 'category': '主食'},
    '米线': {'calories': 92, 'protein': 3.5, 'carbs': 18.0, 'fat': 0.5, 'category': '主食'},
    '河粉': {'calories': 120, 'protein': 2.5, 'carbs': 27.0, 'fat': 0.3, 'category': '主食'},
    '凉皮': {'calories': 117, 'protein': 3.5, 'carbs': 24.0, 'fat': 0.5, 'category': '主食'},
    '凉粉': {'calories': 37, 'protein': 0.2, 'carbs': 9.0, 'fat': 0.1, 'category': '主食'},
    '粉丝': {'calories': 338, 'protein': 0.8, 'carbs': 84.0, 'fat': 0.2, 'category': '主食'},
    '粉条': {'calories': 140, 'protein': 1.0, 'carbs': 35.0, 'fat': 0.2, 'category': '主食'},
    '紫薯': {'calories': 82, 'protein': 1.3, 'carbs': 18.0, 'fat': 0.2, 'category': '主食'},
    '芋头': {'calories': 56, 'protein': 1.3, 'carbs': 13.0, 'fat': 0.2, 'category': '主食'},
    '山药': {'calories': 57, 'protein': 1.9, 'carbs': 12.4, 'fat': 0.2, 'category': '主食'},
    '莲藕': {'calories': 47, 'protein': 1.2, 'carbs': 11.5, 'fat': 0.2, 'category': '主食'},
    '南瓜': {'calories': 26, 'protein': 1.0, 'carbs': 6.5, 'fat': 0.1, 'category': '主食'},
    '紫薯': {'calories': 82, 'protein': 1.3, 'carbs': 18.0, 'fat': 0.2, 'category': '主食'},
    
    # 蔬菜类
    '西兰花': {'calories': 34, 'protein': 2.8, 'carbs': 7.0, 'fat': 0.4, 'category': '蔬菜'},
    '清炒西兰花': {'calories': 54, 'protein': 3.0, 'carbs': 7.5, 'fat': 2.0, 'category': '蔬菜'},
    '西红柿': {'calories': 18, 'protein': 0.9, 'carbs': 3.9, 'fat': 0.2, 'category': '蔬菜'},
    '番茄': {'calories': 18, 'protein': 0.9, 'carbs': 3.9, 'fat': 0.2, 'category': '蔬菜'},
    '番茄炒蛋': {'calories': 85, 'protein': 5.5, 'carbs': 4.2, 'fat': 5.8, 'category': '蔬菜'},
    '黄瓜': {'calories': 16, 'protein': 0.8, 'carbs': 2.9, 'fat': 0.2, 'category': '蔬菜'},
    '胡萝卜': {'calories': 41, 'protein': 0.9, 'carbs': 9.6, 'fat': 0.2, 'category': '蔬菜'},
    '白菜': {'calories': 13, 'protein': 1.5, 'carbs': 2.2, 'fat': 0.2, 'category': '蔬菜'},
    '菠菜': {'calories': 23, 'protein': 2.9, 'carbs': 3.6, 'fat': 0.4, 'category': '蔬菜'},
    '芹菜': {'calories': 14, 'protein': 0.8, 'carbs': 3.0, 'fat': 0.1, 'category': '蔬菜'},
    '茄子': {'calories': 25, 'protein': 1.0, 'carbs': 6.0, 'fat': 0.1, 'category': '蔬菜'},
    '青椒': {'calories': 22, 'protein': 1.0, 'carbs': 5.0, 'fat': 0.2, 'category': '蔬菜'},
    '洋葱': {'calories': 40, 'protein': 1.1, 'carbs': 9.0, 'fat': 0.1, 'category': '蔬菜'},
    '大蒜': {'calories': 149, 'protein': 6.4, 'carbs': 33.1, 'fat': 0.5, 'category': '蔬菜'},
    '生姜': {'calories': 80, 'protein': 1.8, 'carbs': 17.8, 'fat': 0.8, 'category': '蔬菜'},
    '大葱': {'calories': 33, 'protein': 1.7, 'carbs': 6.5, 'fat': 0.3, 'category': '蔬菜'},
    '韭菜': {'calories': 30, 'protein': 2.4, 'carbs': 4.6, 'fat': 0.4, 'category': '蔬菜'},
    '冬瓜': {'calories': 12, 'protein': 0.4, 'carbs': 2.6, 'fat': 0.2, 'category': '蔬菜'},
    '南瓜': {'calories': 26, 'protein': 1.0, 'carbs': 6.5, 'fat': 0.1, 'category': '蔬菜'},
    '丝瓜': {'calories': 20, 'protein': 1.3, 'carbs': 4.0, 'fat': 0.2, 'category': '蔬菜'},
    '苦瓜': {'calories': 19, 'protein': 1.0, 'carbs': 4.3, 'fat': 0.1, 'category': '蔬菜'},
    '豆角': {'calories': 31, 'protein': 2.5, 'carbs': 6.0, 'fat': 0.3, 'category': '蔬菜'},
    '豆芽': {'calories': 44, 'protein': 4.5, 'carbs': 5.1, 'fat': 1.0, 'category': '蔬菜'},
    '豆腐': {'calories': 76, 'protein': 8.1, 'carbs': 1.9, 'fat': 4.8, 'category': '蔬菜'},
    '豆腐干': {'calories': 140, 'protein': 16.2, 'carbs': 5.0, 'fat': 6.0, 'category': '蔬菜'},
    '腐竹': {'calories': 461, 'protein': 44.6, 'carbs': 21.3, 'fat': 21.7, 'category': '蔬菜'},
    '木耳': {'calories': 27, 'protein': 1.5, 'carbs': 6.0, 'fat': 0.2, 'category': '蔬菜'},
    '香菇': {'calories': 26, 'protein': 2.2, 'carbs': 4.5, 'fat': 0.1, 'category': '蔬菜'},
    '金针菇': {'calories': 32, 'protein': 2.4, 'carbs': 6.0, 'fat': 0.4, 'category': '蔬菜'},
    '海带': {'calories': 13, 'protein': 1.2, 'carbs': 2.1, 'fat': 0.1, 'category': '蔬菜'},
    '紫菜': {'calories': 250, 'protein': 43.6, 'carbs': 44.1, 'fat': 1.1, 'category': '蔬菜'},
    '莲藕': {'calories': 47, 'protein': 1.2, 'carbs': 11.5, 'fat': 0.2, 'category': '蔬菜'},
    '山药': {'calories': 57, 'protein': 1.9, 'carbs': 12.4, 'fat': 0.2, 'category': '蔬菜'},
    '芋头': {'calories': 56, 'protein': 1.3, 'carbs': 13.0, 'fat': 0.2, 'category': '蔬菜'},
    '卷心菜': {'calories': 25, 'protein': 1.3, 'carbs': 5.4, 'fat': 0.2, 'category': '蔬菜'},
    '白菜花': {'calories': 25, 'protein': 1.9, 'carbs': 5.0, 'fat': 0.3, 'category': '蔬菜'},
    '生菜': {'calories': 15, 'protein': 1.4, 'carbs': 2.9, 'fat': 0.2, 'category': '蔬菜'},
    '油麦菜': {'calories': 15, 'protein': 1.4, 'carbs': 2.8, 'fat': 0.4, 'category': '蔬菜'},
    '空心菜': {'calories': 19, 'protein': 2.6, 'carbs': 3.6, 'fat': 0.3, 'category': '蔬菜'},
    '茼蒿': {'calories': 24, 'protein': 1.9, 'carbs': 3.9, 'fat': 0.3, 'category': '蔬菜'},
    '芥蓝': {'calories': 22, 'protein': 2.8, 'carbs': 3.6, 'fat': 0.4, 'category': '蔬菜'},
    '菜心': {'calories': 20, 'protein': 1.7, 'carbs': 3.6, 'fat': 0.3, 'category': '蔬菜'},
    '芦笋': {'calories': 20, 'protein': 2.2, 'carbs': 3.9, 'fat': 0.2, 'category': '蔬菜'},
    '竹笋': {'calories': 27, 'protein': 2.6, 'carbs': 5.1, 'fat': 0.2, 'category': '蔬菜'},
    '莴笋': {'calories': 15, 'protein': 1.0, 'carbs': 2.8, 'fat': 0.1, 'category': '蔬菜'},
    '蒜苗': {'calories': 37, 'protein': 2.1, 'carbs': 8.0, 'fat': 0.4, 'category': '蔬菜'},
    '香椿': {'calories': 47, 'protein': 1.7, 'carbs': 10.9, 'fat': 0.4, 'category': '蔬菜'},
    '荠菜': {'calories': 31, 'protein': 5.3, 'carbs': 4.7, 'fat': 0.4, 'category': '蔬菜'},
    '马齿苋': {'calories': 28, 'protein': 2.3, 'carbs': 5.0, 'fat': 0.5, 'category': '蔬菜'},
    '蕨菜': {'calories': 39, 'protein': 1.6, 'carbs': 9.0, 'fat': 0.4, 'category': '蔬菜'},
    '豌豆': {'calories': 81, 'protein': 5.4, 'carbs': 14.5, 'fat': 0.4, 'category': '蔬菜'},
    '毛豆': {'calories': 131, 'protein': 13.1, 'carbs': 10.5, 'fat': 5.0, 'category': '蔬菜'},
    '蚕豆': {'calories': 104, 'protein': 8.8, 'carbs': 16.5, 'fat': 0.4, 'category': '蔬菜'},
    '四季豆': {'calories': 31, 'protein': 2.0, 'carbs': 7.0, 'fat': 0.1, 'category': '蔬菜'},
    '荷兰豆': {'calories': 27, 'protein': 2.5, 'carbs': 4.9, 'fat': 0.3, 'category': '蔬菜'},
    '扁豆': {'calories': 37, 'protein': 2.5, 'carbs': 7.0, 'fat': 0.2, 'category': '蔬菜'},
    '豇豆': {'calories': 33, 'protein': 2.9, 'carbs': 6.9, 'fat': 0.3, 'category': '蔬菜'},
    '秋葵': {'calories': 33, 'protein': 2.0, 'carbs': 7.5, 'fat': 0.1, 'category': '蔬菜'},
    '西葫芦': {'calories': 19, 'protein': 1.2, 'carbs': 3.9, 'fat': 0.2, 'category': '蔬菜'},
    '佛手瓜': {'calories': 19, 'protein': 0.8, 'carbs': 4.5, 'fat': 0.1, 'category': '蔬菜'},
    '洋葱头': {'calories': 40, 'protein': 1.1, 'carbs': 9.0, 'fat': 0.1, 'category': '蔬菜'},
    '蒜苔': {'calories': 61, 'protein': 2.1, 'carbs': 15.4, 'fat': 0.4, 'category': '蔬菜'},
    '韭黄': {'calories': 24, 'protein': 2.4, 'carbs': 3.9, 'fat': 0.2, 'category': '蔬菜'},
    '蒜黄': {'calories': 29, 'protein': 2.6, 'carbs': 5.2, 'fat': 0.3, 'category': '蔬菜'},
    '韭苔': {'calories': 29, 'protein': 2.0, 'carbs': 6.0, 'fat': 0.3, 'category': '蔬菜'},
    '蒜苗': {'calories': 37, 'protein': 2.1, 'carbs': 8.0, 'fat': 0.4, 'category': '蔬菜'},
    '蒜薹': {'calories': 61, 'protein': 2.1, 'carbs': 15.4, 'fat': 0.4, 'category': '蔬菜'},
    '茭白': {'calories': 26, 'protein': 1.2, 'carbs': 5.9, 'fat': 0.2, 'category': '蔬菜'},
    '慈姑': {'calories': 94, 'protein': 4.6, 'carbs': 19.9, 'fat': 0.2, 'category': '蔬菜'},
    '荸荠': {'calories': 59, 'protein': 1.2, 'carbs': 14.2, 'fat': 0.2, 'category': '蔬菜'},
    '菱角': {'calories': 101, 'protein': 4.5, 'carbs': 21.4, 'fat': 0.1, 'category': '蔬菜'},
    '芡实': {'calories': 99, 'protein': 4.4, 'carbs': 21.4, 'fat': 0.3, 'category': '蔬菜'},
    '百合': {'calories': 162, 'protein': 3.2, 'carbs': 38.8, 'fat': 0.1, 'category': '蔬菜'},
    '银耳': {'calories': 200, 'protein': 10.0, 'carbs': 67.3, 'fat': 1.4, 'category': '蔬菜'},
    '黑木耳': {'calories': 27, 'protein': 1.5, 'carbs': 6.0, 'fat': 0.2, 'category': '蔬菜'},
    '平菇': {'calories': 24, 'protein': 1.9, 'carbs': 4.6, 'fat': 0.3, 'category': '蔬菜'},
    '草菇': {'calories': 27, 'protein': 2.7, 'carbs': 4.3, 'fat': 0.2, 'category': '蔬菜'},
    '杏鲍菇': {'calories': 35, 'protein': 1.3, 'carbs': 8.3, 'fat': 0.1, 'category': '蔬菜'},
    '鸡腿菇': {'calories': 26, 'protein': 2.5, 'carbs': 4.3, 'fat': 0.2, 'category': '蔬菜'},
    '茶树菇': {'calories': 35, 'protein': 2.1, 'carbs': 6.9, 'fat': 0.4, 'category': '蔬菜'},
    '猴头菇': {'calories': 13, 'protein': 2.0, 'carbs': 4.9, 'fat': 0.2, 'category': '蔬菜'},
    '竹荪': {'calories': 155, 'protein': 17.8, 'carbs': 60.3, 'fat': 3.1, 'category': '蔬菜'},
    '羊肚菌': {'calories': 295, 'protein': 26.9, 'carbs': 43.7, 'fat': 7.1, 'category': '蔬菜'},
    '牛肝菌': {'calories': 34, 'protein': 2.5, 'carbs': 6.0, 'fat': 0.3, 'category': '蔬菜'},
    '松茸': {'calories': 23, 'protein': 2.0, 'carbs': 3.0, 'fat': 0.4, 'category': '蔬菜'},
    '虫草花': {'calories': 35, 'protein': 2.5, 'carbs': 6.0, 'fat': 0.3, 'category': '蔬菜'},
    '灵芝': {'calories': 45, 'protein': 2.5, 'carbs': 8.0, 'fat': 0.5, 'category': '蔬菜'},
    '茯苓': {'calories': 16, 'protein': 1.2, 'carbs': 3.4, 'fat': 0.1, 'category': '蔬菜'},
    '天麻': {'calories': 35, 'protein': 2.0, 'carbs': 7.0, 'fat': 0.3, 'category': '蔬菜'},
    '当归': {'calories': 40, 'protein': 2.0, 'carbs': 8.0, 'fat': 0.5, 'category': '蔬菜'},
    
    # 肉类
    '猪肉': {'calories': 143, 'protein': 20.0, 'carbs': 0.0, 'fat': 6.2, 'category': '肉类'},
    '瘦肉': {'calories': 143, 'protein': 20.0, 'carbs': 0.0, 'fat': 6.2, 'category': '肉类'},
    '五花肉': {'calories': 349, 'protein': 13.2, 'carbs': 0.0, 'fat': 30.6, 'category': '肉类'},
    '猪肉馅': {'calories': 250, 'protein': 15.0, 'carbs': 0.0, 'fat': 20.0, 'category': '肉类'},
    '排骨': {'calories': 278, 'protein': 16.7, 'carbs': 0.0, 'fat': 23.1, 'category': '肉类'},
    '猪蹄': {'calories': 260, 'protein': 23.6, 'carbs': 0.0, 'fat': 18.8, 'category': '肉类'},
    '猪肝': {'calories': 129, 'protein': 19.3, 'carbs': 5.0, 'fat': 3.5, 'category': '肉类'},
    '猪血': {'calories': 55, 'protein': 12.2, 'carbs': 0.9, 'fat': 0.3, 'category': '肉类'},
    '香肠': {'calories': 508, 'protein': 18.0, 'carbs': 1.8, 'fat': 48.0, 'category': '肉类'},
    '火腿': {'calories': 212, 'protein': 16.0, 'carbs': 1.0, 'fat': 16.0, 'category': '肉类'},
    '腊肉': {'calories': 458, 'protein': 22.0, 'carbs': 2.0, 'fat': 40.0, 'category': '肉类'},
    '牛肉': {'calories': 125, 'protein': 20.0, 'carbs': 0.0, 'fat': 4.2, 'category': '肉类'},
    '牛腩': {'calories': 332, 'protein': 17.0, 'carbs': 0.0, 'fat': 28.0, 'category': '肉类'},
    '牛腱': {'calories': 130, 'protein': 22.0, 'carbs': 0.0, 'fat': 4.0, 'category': '肉类'},
    '牛排': {'calories': 271, 'protein': 26.0, 'carbs': 0.0, 'fat': 19.0, 'category': '肉类'},
    '牛百叶': {'calories': 72, 'protein': 14.0, 'carbs': 0.0, 'fat': 1.6, 'category': '肉类'},
    '羊肉': {'calories': 203, 'protein': 18.5, 'carbs': 0.0, 'fat': 14.1, 'category': '肉类'},
    '羊排': {'calories': 360, 'protein': 16.0, 'carbs': 0.0, 'fat': 32.0, 'category': '肉类'},
    '鸡肉': {'calories': 167, 'protein': 19.4, 'carbs': 0.0, 'fat': 9.4, 'category': '肉类'},
    '鸡胸肉': {'calories': 133, 'protein': 19.4, 'carbs': 0.0, 'fat': 5.0, 'category': '肉类'},
    '鸡腿': {'calories': 181, 'protein': 16.0, 'carbs': 0.0, 'fat': 13.0, 'category': '肉类'},
    '鸡翅': {'calories': 202, 'protein': 15.8, 'carbs': 0.0, 'fat': 15.0, 'category': '肉类'},
    '鸡爪': {'calories': 215, 'protein': 19.4, 'carbs': 0.0, 'fat': 15.0, 'category': '肉类'},
    '鸭肉': {'calories': 240, 'protein': 15.5, 'carbs': 0.0, 'fat': 19.7, 'category': '肉类'},
    '鸭腿': {'calories': 217, 'protein': 19.7, 'carbs': 0.0, 'fat': 15.2, 'category': '肉类'},
    '鸭翅': {'calories': 217, 'protein': 16.5, 'carbs': 0.0, 'fat': 16.5, 'category': '肉类'},
    '火腿肠': {'calories': 212, 'protein': 12.0, 'carbs': 2.0, 'fat': 17.0, 'category': '肉类'},
    '午餐肉': {'calories': 229, 'protein': 12.0, 'carbs': 3.0, 'fat': 19.0, 'category': '肉类'},
    '培根': {'calories': 541, 'protein': 37.0, 'carbs': 1.4, 'fat': 42.0, 'category': '肉类'},
    '肉丸': {'calories': 250, 'protein': 12.0, 'carbs': 5.0, 'fat': 20.0, 'category': '肉类'},
    '鱼丸': {'calories': 107, 'protein': 11.0, 'carbs': 10.0, 'fat': 2.5, 'category': '肉类'},
    '虾丸': {'calories': 95, 'protein': 12.0, 'carbs': 6.0, 'fat': 2.0, 'category': '肉类'},
    '贡丸': {'calories': 220, 'protein': 10.0, 'carbs': 8.0, 'fat': 16.0, 'category': '肉类'},
    
    # 海鲜类
    '虾': {'calories': 93, 'protein': 18.6, 'carbs': 0.8, 'fat': 0.8, 'category': '海鲜'},
    '虾仁': {'calories': 85, 'protein': 18.0, 'carbs': 0.0, 'fat': 0.5, 'category': '海鲜'},
    '基围虾': {'calories': 101, 'protein': 18.2, 'carbs': 1.5, 'fat': 1.4, 'category': '海鲜'},
    '对虾': {'calories': 93, 'protein': 18.6, 'carbs': 0.8, 'fat': 0.8, 'category': '海鲜'},
    '龙虾': {'calories': 90, 'protein': 19.0, 'carbs': 0.5, 'fat': 0.5, 'category': '海鲜'},
    '螃蟹': {'calories': 97, 'protein': 19.0, 'carbs': 0.0, 'fat': 1.5, 'category': '海鲜'},
    '大闸蟹': {'calories': 102, 'protein': 17.5, 'carbs': 2.3, 'fat': 2.6, 'category': '海鲜'},
    '梭子蟹': {'calories': 95, 'protein': 18.0, 'carbs': 0.0, 'fat': 2.0, 'category': '海鲜'},
    '鱼': {'calories': 100, 'protein': 18.0, 'carbs': 0.0, 'fat': 3.0, 'category': '海鲜'},
    '鲫鱼': {'calories': 108, 'protein': 17.1, 'carbs': 3.8, 'fat': 2.7, 'category': '海鲜'},
    '草鱼': {'calories': 113, 'protein': 16.6, 'carbs': 0.0, 'fat': 5.2, 'category': '海鲜'},
    '鲤鱼': {'calories': 109, 'protein': 17.6, 'carbs': 0.5, 'fat': 4.1, 'category': '海鲜'},
    '带鱼': {'calories': 127, 'protein': 17.7, 'carbs': 0.0, 'fat': 4.9, 'category': '海鲜'},
    '黄花鱼': {'calories': 97, 'protein': 17.7, 'carbs': 0.0, 'fat': 2.5, 'category': '海鲜'},
    '鲈鱼': {'calories': 105, 'protein': 18.6, 'carbs': 0.0, 'fat': 3.4, 'category': '海鲜'},
    '鳕鱼': {'calories': 78, 'protein': 17.8, 'carbs': 0.0, 'fat': 0.7, 'category': '海鲜'},
    '三文鱼': {'calories': 139, 'protein': 17.2, 'carbs': 0.0, 'fat': 7.8, 'category': '海鲜'},
    '金枪鱼': {'calories': 108, 'protein': 23.0, 'carbs': 0.0, 'fat': 1.0, 'category': '海鲜'},
    '鱿鱼': {'calories': 92, 'protein': 18.0, 'carbs': 2.0, 'fat': 1.5, 'category': '海鲜'},
    '墨鱼': {'calories': 82, 'protein': 15.0, 'carbs': 1.0, 'fat': 1.5, 'category': '海鲜'},
    '章鱼': {'calories': 81, 'protein': 14.9, 'carbs': 2.0, 'fat': 1.0, 'category': '海鲜'},
    '海参': {'calories': 71, 'protein': 16.5, 'carbs': 0.9, 'fat': 0.2, 'category': '海鲜'},
    '鲍鱼': {'calories': 84, 'protein': 12.6, 'carbs': 6.6, 'fat': 0.8, 'category': '海鲜'},
    '扇贝': {'calories': 84, 'protein': 15.0, 'carbs': 2.7, 'fat': 0.6, 'category': '海鲜'},
    '蛤蜊': {'calories': 62, 'protein': 10.1, 'carbs': 2.1, 'fat': 1.4, 'category': '海鲜'},
    '花蛤': {'calories': 62, 'protein': 10.1, 'carbs': 2.1, 'fat': 1.4, 'category': '海鲜'},
    '蛏子': {'calories': 40, 'protein': 7.3, 'carbs': 2.1, 'fat': 0.3, 'category': '海鲜'},
    '牡蛎': {'calories': 73, 'protein': 5.3, 'carbs': 10.3, 'fat': 2.0, 'category': '海鲜'},
    '生蚝': {'calories': 73, 'protein': 5.3, 'carbs': 10.3, 'fat': 2.0, 'category': '海鲜'},
    '海蜇': {'calories': 33, 'protein': 3.7, 'carbs': 3.8, 'fat': 0.3, 'category': '海鲜'},
    '海带': {'calories': 13, 'protein': 1.2, 'carbs': 2.1, 'fat': 0.1, 'category': '海鲜'},
    '紫菜': {'calories': 250, 'protein': 43.6, 'carbs': 44.1, 'fat': 1.1, 'category': '海鲜'},
    '虾皮': {'calories': 153, 'protein': 30.7, 'carbs': 2.5, 'fat': 2.2, 'category': '海鲜'},
    '虾米': {'calories': 198, 'protein': 43.7, 'carbs': 0.0, 'fat': 2.6, 'category': '海鲜'},
    '干贝': {'calories': 264, 'protein': 55.6, 'carbs': 5.1, 'fat': 2.4, 'category': '海鲜'},
    
    # 蛋类
    '鸡蛋': {'calories': 144, 'protein': 13.3, 'carbs': 2.8, 'fat': 8.8, 'category': '蛋类'},
    '蛋白': {'calories': 52, 'protein': 11.6, 'carbs': 0.7, 'fat': 0.1, 'category': '蛋类'},
    '蛋黄': {'calories': 328, 'protein': 15.2, 'carbs': 3.4, 'fat': 28.2, 'category': '蛋类'},
    '鸭蛋': {'calories': 180, 'protein': 12.6, 'carbs': 3.1, 'fat': 13.0, 'category': '蛋类'},
    '咸鸭蛋': {'calories': 190, 'protein': 12.7, 'carbs': 6.3, 'fat': 12.7, 'category': '蛋类'},
    '皮蛋': {'calories': 171, 'protein': 14.2, 'carbs': 4.5, 'fat': 10.7, 'category': '蛋类'},
    '鹌鹑蛋': {'calories': 160, 'protein': 12.8, 'carbs': 2.1, 'fat': 11.1, 'category': '蛋类'},
    '茶叶蛋': {'calories': 140, 'protein': 12.5, 'carbs': 3.0, 'fat': 8.5, 'category': '蛋类'},
    '荷包蛋': {'calories': 180, 'protein': 12.5, 'carbs': 1.5, 'fat': 14.0, 'category': '蛋类'},
    '煎蛋': {'calories': 180, 'protein': 12.5, 'carbs': 1.5, 'fat': 14.0, 'category': '蛋类'},
    '炒蛋': {'calories': 165, 'protein': 12.0, 'carbs': 2.0, 'fat': 12.0, 'category': '蛋类'},
    '煮蛋': {'calories': 144, 'protein': 13.3, 'carbs': 2.8, 'fat': 8.8, 'category': '蛋类'},
    '蒸蛋': {'calories': 120, 'protein': 10.0, 'carbs': 2.0, 'fat': 8.0, 'category': '蛋类'},
    
    # 水果类
    '苹果': {'calories': 52, 'protein': 0.3, 'carbs': 13.8, 'fat': 0.2, 'category': '水果'},
    '香蕉': {'calories': 89, 'protein': 1.1, 'carbs': 22.8, 'fat': 0.3, 'category': '水果'},
    '橙子': {'calories': 47, 'protein': 0.9, 'carbs': 11.8, 'fat': 0.1, 'category': '水果'},
    '橘子': {'calories': 53, 'protein': 0.8, 'carbs': 13.3, 'fat': 0.1, 'category': '水果'},
    '柚子': {'calories': 42, 'protein': 0.8, 'carbs': 10.5, 'fat': 0.1, 'category': '水果'},
    '葡萄': {'calories': 69, 'protein': 0.7, 'carbs': 18.1, 'fat': 0.2, 'category': '水果'},
    '提子': {'calories': 69, 'protein': 0.7, 'carbs': 18.1, 'fat': 0.2, 'category': '水果'},
    '草莓': {'calories': 32, 'protein': 0.7, 'carbs': 7.7, 'fat': 0.3, 'category': '水果'},
    '蓝莓': {'calories': 57, 'protein': 0.7, 'carbs': 14.5, 'fat': 0.3, 'category': '水果'},
    '西瓜': {'calories': 30, 'protein': 0.6, 'carbs': 7.6, 'fat': 0.2, 'category': '水果'},
    '哈密瓜': {'calories': 34, 'protein': 0.5, 'carbs': 8.2, 'fat': 0.2, 'category': '水果'},
    '香瓜': {'calories': 34, 'protein': 0.5, 'carbs': 8.2, 'fat': 0.2, 'category': '水果'},
    '梨': {'calories': 57, 'protein': 0.4, 'carbs': 15.5, 'fat': 0.1, 'category': '水果'},
    '雪梨': {'calories': 57, 'protein': 0.4, 'carbs': 15.5, 'fat': 0.1, 'category': '水果'},
    '桃子': {'calories': 39, 'protein': 0.9, 'carbs': 9.5, 'fat': 0.3, 'category': '水果'},
    '水蜜桃': {'calories': 39, 'protein': 0.9, 'carbs': 9.5, 'fat': 0.3, 'category': '水果'},
    '李子': {'calories': 46, 'protein': 0.7, 'carbs': 11.3, 'fat': 0.3, 'category': '水果'},
    '樱桃': {'calories': 63, 'protein': 1.1, 'carbs': 16.0, 'fat': 0.2, 'category': '水果'},
    '车厘子': {'calories': 63, 'protein': 1.1, 'carbs': 16.0, 'fat': 0.2, 'category': '水果'},
    '芒果': {'calories': 60, 'protein': 0.8, 'carbs': 15.0, 'fat': 0.4, 'category': '水果'},
    '菠萝': {'calories': 50, 'protein': 0.5, 'carbs': 13.1, 'fat': 0.1, 'category': '水果'},
    '榴莲': {'calories': 147, 'protein': 1.5, 'carbs': 27.1, 'fat': 5.3, 'category': '水果'},
    '火龙果': {'calories': 52, 'protein': 1.1, 'carbs': 13.0, 'fat': 0.4, 'category': '水果'},
    '猕猴桃': {'calories': 61, 'protein': 1.1, 'carbs': 14.5, 'fat': 0.5, 'category': '水果'},
    '奇异果': {'calories': 61, 'protein': 1.1, 'carbs': 14.5, 'fat': 0.5, 'category': '水果'},
    '柠檬': {'calories': 29, 'protein': 1.1, 'carbs': 9.3, 'fat': 0.3, 'category': '水果'},
    '百香果': {'calories': 97, 'protein': 2.2, 'carbs': 23.4, 'fat': 0.7, 'category': '水果'},
    '石榴': {'calories': 83, 'protein': 1.7, 'carbs': 18.7, 'fat': 0.4, 'category': '水果'},
    '柿子': {'calories': 71, 'protein': 0.4, 'carbs': 18.5, 'fat': 0.1, 'category': '水果'},
    '枣': {'calories': 79, 'protein': 1.2, 'carbs': 20.2, 'fat': 0.2, 'category': '水果'},
    '冬枣': {'calories': 105, 'protein': 1.8, 'carbs': 27.8, 'fat': 0.2, 'category': '水果'},
    '山楂': {'calories': 102, 'protein': 0.5, 'carbs': 25.1, 'fat': 0.6, 'category': '水果'},
    '椰子': {'calories': 354, 'protein': 3.3, 'carbs': 15.2, 'fat': 33.5, 'category': '水果'},
    '木瓜': {'calories': 43, 'protein': 0.5, 'carbs': 10.8, 'fat': 0.3, 'category': '水果'},
    '杨桃': {'calories': 31, 'protein': 0.6, 'carbs': 7.4, 'fat': 0.3, 'category': '水果'},
    '荔枝': {'calories': 66, 'protein': 0.8, 'carbs': 16.5, 'fat': 0.4, 'category': '水果'},
    '龙眼': {'calories': 71, 'protein': 1.2, 'carbs': 16.6, 'fat': 0.1, 'category': '水果'},
    '甘蔗': {'calories': 64, 'protein': 0.4, 'carbs': 16.0, 'fat': 0.1, 'category': '水果'},
    
    # 坚果类
    '核桃': {'calories': 654, 'protein': 15.2, 'carbs': 13.7, 'fat': 65.2, 'category': '坚果'},
    '杏仁': {'calories': 578, 'protein': 21.2, 'carbs': 21.0, 'fat': 49.4, 'category': '坚果'},
    '腰果': {'calories': 553, 'protein': 18.2, 'carbs': 30.2, 'fat': 43.9, 'category': '坚果'},
    '花生': {'calories': 567, 'protein': 24.8, 'carbs': 16.2, 'fat': 49.2, 'category': '坚果'},
    '瓜子': {'calories': 591, 'protein': 23.0, 'carbs': 17.0, 'fat': 49.0, 'category': '坚果'},
    '葵花籽': {'calories': 591, 'protein': 23.0, 'carbs': 17.0, 'fat': 49.0, 'category': '坚果'},
    '南瓜子': {'calories': 559, 'protein': 30.2, 'carbs': 10.7, 'fat': 49.1, 'category': '坚果'},
    '松子': {'calories': 673, 'protein': 13.1, 'carbs': 12.7, 'fat': 68.4, 'category': '坚果'},
    '开心果': {'calories': 562, 'protein': 20.6, 'carbs': 27.5, 'fat': 45.4, 'category': '坚果'},
    '夏威夷果': {'calories': 718, 'protein': 7.9, 'carbs': 13.8, 'fat': 75.8, 'category': '坚果'},
    '碧根果': {'calories': 691, 'protein': 9.2, 'carbs': 13.9, 'fat': 72.0, 'category': '坚果'},
    '板栗': {'calories': 185, 'protein': 4.2, 'carbs': 40.0, 'fat': 1.1, 'category': '坚果'},
    '榛子': {'calories': 628, 'protein': 15.0, 'carbs': 16.7, 'fat': 60.8, 'category': '坚果'},
    
    # 饮品类
    '牛奶': {'calories': 54, 'protein': 3.0, 'carbs': 4.7, 'fat': 3.2, 'category': '饮品'},
    '纯牛奶': {'calories': 54, 'protein': 3.0, 'carbs': 4.7, 'fat': 3.2, 'category': '饮品'},
    '酸奶': {'calories': 72, 'protein': 3.5, 'carbs': 9.0, 'fat': 2.7, 'category': '饮品'},
    '豆浆': {'calories': 31, 'protein': 2.4, 'carbs': 4.0, 'fat': 0.7, 'category': '饮品'},
    '豆奶': {'calories': 45, 'protein': 3.5, 'carbs': 5.0, 'fat': 1.5, 'category': '饮品'},
    '咖啡': {'calories': 2, 'protein': 0.1, 'carbs': 0.0, 'fat': 0.0, 'category': '饮品'},
    '拿铁': {'calories': 45, 'protein': 2.5, 'carbs': 4.0, 'fat': 2.0, 'category': '饮品'},
    '美式咖啡': {'calories': 2, 'protein': 0.1, 'carbs': 0.0, 'fat': 0.0, 'category': '饮品'},
    '奶茶': {'calories': 120, 'protein': 3.0, 'carbs': 20.0, 'fat': 3.5, 'category': '饮品'},
    '果汁': {'calories': 45, 'protein': 0.5, 'carbs': 11.0, 'fat': 0.1, 'category': '饮品'},
    '橙汁': {'calories': 45, 'protein': 0.7, 'carbs': 10.4, 'fat': 0.2, 'category': '饮品'},
    '苹果汁': {'calories': 46, 'protein': 0.1, 'carbs': 11.3, 'fat': 0.1, 'category': '饮品'},
    '可乐': {'calories': 42, 'protein': 0.0, 'carbs': 10.6, 'fat': 0.0, 'category': '饮品'},
    '雪碧': {'calories': 40, 'protein': 0.0, 'carbs': 10.0, 'fat': 0.0, 'category': '饮品'},
    '汽水': {'calories': 40, 'protein': 0.0, 'carbs': 10.0, 'fat': 0.0, 'category': '饮品'},
    '绿茶': {'calories': 1, 'protein': 0.1, 'carbs': 0.2, 'fat': 0.0, 'category': '饮品'},
    '红茶': {'calories': 1, 'protein': 0.1, 'carbs': 0.3, 'fat': 0.0, 'category': '饮品'},
    '乌龙茶': {'calories': 1, 'protein': 0.1, 'carbs': 0.2, 'fat': 0.0, 'category': '饮品'},
    '普洱茶': {'calories': 1, 'protein': 0.1, 'carbs': 0.2, 'fat': 0.0, 'category': '饮品'},
    '啤酒': {'calories': 43, 'protein': 0.5, 'carbs': 3.6, 'fat': 0.0, 'category': '饮品'},
    '红酒': {'calories': 85, 'protein': 0.1, 'carbs': 2.6, 'fat': 0.0, 'category': '饮品'},
    '白酒': {'calories': 295, 'protein': 0.0, 'carbs': 0.0, 'fat': 0.0, 'category': '饮品'},
    '蜂蜜水': {'calories': 64, 'protein': 0.1, 'carbs': 17.3, 'fat': 0.0, 'category': '饮品'},
    '椰子水': {'calories': 19, 'protein': 0.7, 'carbs': 3.7, 'fat': 0.2, 'category': '饮品'},
    '运动饮料': {'calories': 26, 'protein': 0.0, 'carbs': 6.5, 'fat': 0.0, 'category': '饮品'},
    '矿泉水': {'calories': 0, 'protein': 0.0, 'carbs': 0.0, 'fat': 0.0, 'category': '饮品'},
    '白开水': {'calories': 0, 'protein': 0.0, 'carbs': 0.0, 'fat': 0.0, 'category': '饮品'},
    
    # 常见中餐菜肴
    '红烧肉': {'calories': 470, 'protein': 15.0, 'carbs': 8.0, 'fat': 42.0, 'category': '菜肴'},
    '糖醋排骨': {'calories': 380, 'protein': 18.0, 'carbs': 25.0, 'fat': 24.0, 'category': '菜肴'},
    '红烧排骨': {'calories': 350, 'protein': 20.0, 'carbs': 5.0, 'fat': 26.0, 'category': '菜肴'},
    '清蒸鱼': {'calories': 120, 'protein': 20.0, 'carbs': 2.0, 'fat': 4.0, 'category': '菜肴'},
    '红烧鱼': {'calories': 180, 'protein': 18.0, 'carbs': 5.0, 'fat': 10.0, 'category': '菜肴'},
    '酸菜鱼': {'calories': 150, 'protein': 15.0, 'carbs': 5.0, 'fat': 8.0, 'category': '菜肴'},
    '水煮鱼': {'calories': 200, 'protein': 18.0, 'carbs': 3.0, 'fat': 13.0, 'category': '菜肴'},
    '水煮肉片': {'calories': 220, 'protein': 20.0, 'carbs': 4.0, 'fat': 14.0, 'category': '菜肴'},
    '水煮牛肉': {'calories': 210, 'protein': 22.0, 'carbs': 3.0, 'fat': 12.0, 'category': '菜肴'},
    '宫保鸡丁': {'calories': 220, 'protein': 18.0, 'carbs': 12.0, 'fat': 12.0, 'category': '菜肴'},
    '鱼香肉丝': {'calories': 180, 'protein': 12.0, 'carbs': 15.0, 'fat': 10.0, 'category': '菜肴'},
    '鱼香茄子': {'calories': 160, 'protein': 4.0, 'carbs': 18.0, 'fat': 9.0, 'category': '菜肴'},
    '麻婆豆腐': {'calories': 150, 'protein': 8.0, 'carbs': 8.0, 'fat': 10.0, 'category': '菜肴'},
    '回锅肉': {'calories': 350, 'protein': 14.0, 'carbs': 5.0, 'fat': 30.0, 'category': '菜肴'},
    '东坡肉': {'calories': 480, 'protein': 12.0, 'carbs': 6.0, 'fat': 45.0, 'category': '菜肴'},
    '梅菜扣肉': {'calories': 420, 'protein': 15.0, 'carbs': 10.0, 'fat': 35.0, 'category': '菜肴'},
    '粉蒸肉': {'calories': 380, 'protein': 12.0, 'carbs': 25.0, 'fat': 26.0, 'category': '菜肴'},
    '小炒肉': {'calories': 280, 'protein': 16.0, 'carbs': 6.0, 'fat': 22.0, 'category': '菜肴'},
    '木须肉': {'calories': 190, 'protein': 12.0, 'carbs': 10.0, 'fat': 12.0, 'category': '菜肴'},
    '京酱肉丝': {'calories': 240, 'protein': 16.0, 'carbs': 18.0, 'fat': 12.0, 'category': '菜肴'},
    '糖醋里脊': {'calories': 280, 'protein': 14.0, 'carbs': 28.0, 'fat': 12.0, 'category': '菜肴'},
    '可乐鸡翅': {'calories': 250, 'protein': 18.0, 'carbs': 15.0, 'fat': 14.0, 'category': '菜肴'},
    '红烧鸡翅': {'calories': 240, 'protein': 18.0, 'carbs': 8.0, 'fat': 15.0, 'category': '菜肴'},
    '烤鸡翅': {'calories': 260, 'protein': 20.0, 'carbs': 5.0, 'fat': 18.0, 'category': '菜肴'},
    '炸鸡翅': {'calories': 320, 'protein': 18.0, 'carbs': 15.0, 'fat': 22.0, 'category': '菜肴'},
    '白切鸡': {'calories': 165, 'protein': 25.0, 'carbs': 0.0, 'fat': 7.0, 'category': '菜肴'},
    '口水鸡': {'calories': 200, 'protein': 22.0, 'carbs': 3.0, 'fat': 12.0, 'category': '菜肴'},
    '辣子鸡': {'calories': 280, 'protein': 20.0, 'carbs': 8.0, 'fat': 19.0, 'category': '菜肴'},
    '盐焗鸡': {'calories': 180, 'protein': 24.0, 'carbs': 1.0, 'fat': 8.0, 'category': '菜肴'},
    '叫花鸡': {'calories': 220, 'protein': 22.0, 'carbs': 5.0, 'fat': 13.0, 'category': '菜肴'},
    '手撕鸡': {'calories': 175, 'protein': 23.0, 'carbs': 2.0, 'fat': 8.0, 'category': '菜肴'},
    '啤酒鸭': {'calories': 260, 'protein': 20.0, 'carbs': 5.0, 'fat': 18.0, 'category': '菜肴'},
    '烤鸭': {'calories': 330, 'protein': 19.0, 'carbs': 0.0, 'fat': 28.0, 'category': '菜肴'},
    '烧鹅': {'calories': 350, 'protein': 20.0, 'carbs': 0.0, 'fat': 30.0, 'category': '菜肴'},
    '叉烧': {'calories': 280, 'protein': 18.0, 'carbs': 12.0, 'fat': 18.0, 'category': '菜肴'},
    '腊肠': {'calories': 508, 'protein': 18.0, 'carbs': 1.8, 'fat': 48.0, 'category': '菜肴'},
    '腊肉炒饭': {'calories': 320, 'protein': 10.0, 'carbs': 45.0, 'fat': 12.0, 'category': '菜肴'},
    '扬州炒饭': {'calories': 280, 'protein': 12.0, 'carbs': 42.0, 'fat': 8.0, 'category': '菜肴'},
    '蛋炒饭': {'calories': 220, 'protein': 8.0, 'carbs': 35.0, 'fat': 6.0, 'category': '菜肴'},
    '炒面': {'calories': 250, 'protein': 8.0, 'carbs': 40.0, 'fat': 8.0, 'category': '菜肴'},
    '炒米粉': {'calories': 230, 'protein': 6.0, 'carbs': 42.0, 'fat': 6.0, 'category': '菜肴'},
    '炒河粉': {'calories': 260, 'protein': 7.0, 'carbs': 45.0, 'fat': 7.0, 'category': '菜肴'},
    '干炒牛河': {'calories': 320, 'protein': 12.0, 'carbs': 48.0, 'fat': 10.0, 'category': '菜肴'},
    '炸酱面': {'calories': 320, 'protein': 12.0, 'carbs': 50.0, 'fat': 9.0, 'category': '菜肴'},
    '担担面': {'calories': 350, 'protein': 14.0, 'carbs': 48.0, 'fat': 12.0, 'category': '菜肴'},
    '热干面': {'calories': 280, 'protein': 10.0, 'carbs': 52.0, 'fat': 4.0, 'category': '菜肴'},
    '兰州拉面': {'calories': 320, 'protein': 12.0, 'carbs': 55.0, 'fat': 6.0, 'category': '菜肴'},
    '重庆小面': {'calories': 340, 'protein': 12.0, 'carbs': 52.0, 'fat': 10.0, 'category': '菜肴'},
    '牛肉面': {'calories': 380, 'protein': 18.0, 'carbs': 50.0, 'fat': 12.0, 'category': '菜肴'},
    '排骨面': {'calories': 360, 'protein': 16.0, 'carbs': 48.0, 'fat': 12.0, 'category': '菜肴'},
    '云吞面': {'calories': 300, 'protein': 14.0, 'carbs': 48.0, 'fat': 6.0, 'category': '菜肴'},
    '阳春面': {'calories': 240, 'protein': 8.0, 'carbs': 45.0, 'fat': 4.0, 'category': '菜肴'},
    '葱油拌面': {'calories': 320, 'protein': 8.0, 'carbs': 48.0, 'fat': 12.0, 'category': '菜肴'},
    '西红柿鸡蛋面': {'calories': 220, 'protein': 10.0, 'carbs': 40.0, 'fat': 4.0, 'category': '菜肴'},
    '打卤面': {'calories': 280, 'protein': 12.0, 'carbs': 45.0, 'fat': 6.0, 'category': '菜肴'},
    '臊子面': {'calories': 300, 'protein': 14.0, 'carbs': 48.0, 'fat': 6.0, 'category': '菜肴'},
    '刀削面': {'calories': 290, 'protein': 10.0, 'carbs': 55.0, 'fat': 4.0, 'category': '菜肴'},
    '烩面': {'calories': 310, 'protein': 12.0, 'carbs': 52.0, 'fat': 6.0, 'category': '菜肴'},
    '焖面': {'calories': 340, 'protein': 12.0, 'carbs': 55.0, 'fat': 9.0, 'category': '菜肴'},
    '炒饼': {'calories': 280, 'protein': 8.0, 'carbs': 45.0, 'fat': 8.0, 'category': '菜肴'},
    '煎饼果子': {'calories': 320, 'protein': 10.0, 'carbs': 48.0, 'fat': 10.0, 'category': '菜肴'},
    '肉夹馍': {'calories': 350, 'protein': 15.0, 'carbs': 45.0, 'fat': 12.0, 'category': '菜肴'},
    '凉皮': {'calories': 150, 'protein': 4.0, 'carbs': 30.0, 'fat': 2.0, 'category': '菜肴'},
    '肉包子': {'calories': 230, 'protein': 8.5, 'carbs': 42.0, 'fat': 4.2, 'category': '菜肴'},
    '菜包子': {'calories': 180, 'protein': 5.5, 'carbs': 38.0, 'fat': 1.2, 'category': '菜肴'},
    '豆沙包': {'calories': 220, 'protein': 6.0, 'carbs': 45.0, 'fat': 2.0, 'category': '菜肴'},
    '奶黄包': {'calories': 240, 'protein': 6.5, 'carbs': 42.0, 'fat': 6.0, 'category': '菜肴'},
    '叉烧包': {'calories': 260, 'protein': 10.0, 'carbs': 40.0, 'fat': 7.0, 'category': '菜肴'},
    '小笼包': {'calories': 220, 'protein': 8.0, 'carbs': 35.0, 'fat': 6.0, 'category': '菜肴'},
    '生煎包': {'calories': 280, 'protein': 10.0, 'carbs': 38.0, 'fat': 10.0, 'category': '菜肴'},
    '灌汤包': {'calories': 240, 'protein': 9.0, 'carbs': 36.0, 'fat': 7.0, 'category': '菜肴'},
    '锅贴': {'calories': 260, 'protein': 10.0, 'carbs': 35.0, 'fat': 9.0, 'category': '菜肴'},
    '韭菜盒子': {'calories': 280, 'protein': 8.0, 'carbs': 40.0, 'fat': 10.0, 'category': '菜肴'},
    '葱油饼': {'calories': 320, 'protein': 6.0, 'carbs': 45.0, 'fat': 14.0, 'category': '菜肴'},
    '手抓饼': {'calories': 350, 'protein': 7.0, 'carbs': 42.0, 'fat': 18.0, 'category': '菜肴'},
    '鸡蛋灌饼': {'calories': 340, 'protein': 10.0, 'carbs': 40.0, 'fat': 16.0, 'category': '菜肴'},
    '酱香饼': {'calories': 360, 'protein': 8.0, 'carbs': 55.0, 'fat': 12.0, 'category': '菜肴'},
    '千层饼': {'calories': 340, 'protein': 7.0, 'carbs': 52.0, 'fat': 12.0, 'category': '菜肴'},
    '烧饼': {'calories': 300, 'protein': 8.0, 'carbs': 50.0, 'fat': 8.0, 'category': '菜肴'},
    '火烧': {'calories': 280, 'protein': 8.0, 'carbs': 48.0, 'fat': 7.0, 'category': '菜肴'},
    '驴打滚': {'calories': 320, 'protein': 6.0, 'carbs': 65.0, 'fat': 4.0, 'category': '菜肴'},
    '艾窝窝': {'calories': 280, 'protein': 5.0, 'carbs': 60.0, 'fat': 2.0, 'category': '菜肴'},
    '豌豆黄': {'calories': 240, 'protein': 8.0, 'carbs': 48.0, 'fat': 1.0, 'category': '菜肴'},
    '绿豆糕': {'calories': 350, 'protein': 8.0, 'carbs': 70.0, 'fat': 3.0, 'category': '菜肴'},
    '月饼': {'calories': 420, 'protein': 8.0, 'carbs': 65.0, 'fat': 16.0, 'category': '菜肴'},
    '蛋黄酥': {'calories': 450, 'protein': 8.0, 'carbs': 50.0, 'fat': 25.0, 'category': '菜肴'},
    '凤梨酥': {'calories': 480, 'protein': 6.0, 'carbs': 65.0, 'fat': 22.0, 'category': '菜肴'},
    '老婆饼': {'calories': 420, 'protein': 6.0, 'carbs': 60.0, 'fat': 18.0, 'category': '菜肴'},
    '桃酥': {'calories': 520, 'protein': 8.0, 'carbs': 60.0, 'fat': 28.0, 'category': '菜肴'},
    '蛋挞': {'calories': 320, 'protein': 6.0, 'carbs': 32.0, 'fat': 19.0, 'category': '菜肴'},
    '泡芙': {'calories': 340, 'protein': 6.0, 'carbs': 35.0, 'fat': 20.0, 'category': '菜肴'},
    '蛋糕': {'calories': 370, 'protein': 6.0, 'carbs': 55.0, 'fat': 14.0, 'category': '菜肴'},
    '奶油蛋糕': {'calories': 420, 'protein': 6.0, 'carbs': 50.0, 'fat': 22.0, 'category': '菜肴'},
    '芝士蛋糕': {'calories': 380, 'protein': 8.0, 'carbs': 35.0, 'fat': 24.0, 'category': '菜肴'},
    '提拉米苏': {'calories': 450, 'protein': 7.0, 'carbs': 45.0, 'fat': 28.0, 'category': '菜肴'},
    '慕斯蛋糕': {'calories': 400, 'protein': 6.0, 'carbs': 40.0, 'fat': 25.0, 'category': '菜肴'},
    '布丁': {'calories': 280, 'protein': 5.0, 'carbs': 40.0, 'fat': 11.0, 'category': '菜肴'},
    '双皮奶': {'calories': 180, 'protein': 6.0, 'carbs': 25.0, 'fat': 6.0, 'category': '菜肴'},
    '姜撞奶': {'calories': 160, 'protein': 5.0, 'carbs': 22.0, 'fat': 5.0, 'category': '菜肴'},
    '龟苓膏': {'calories': 80, 'protein': 2.0, 'carbs': 18.0, 'fat': 0.2, 'category': '菜肴'},
    '银耳羹': {'calories': 120, 'protein': 3.0, 'carbs': 25.0, 'fat': 0.5, 'category': '菜肴'},
    '汤圆': {'calories': 230, 'protein': 4.0, 'carbs': 48.0, 'fat': 2.0, 'category': '菜肴'},
    '元宵': {'calories': 230, 'protein': 4.0, 'carbs': 48.0, 'fat': 2.0, 'category': '菜肴'},
    '粽子': {'calories': 200, 'protein': 4.5, 'carbs': 40.0, 'fat': 2.5, 'category': '菜肴'},
    '肉粽': {'calories': 250, 'protein': 8.0, 'carbs': 40.0, 'fat': 7.0, 'category': '菜肴'},
    '蛋黄粽': {'calories': 280, 'protein': 7.0, 'carbs': 42.0, 'fat': 10.0, 'category': '菜肴'},
    '年糕': {'calories': 154, 'protein': 3.3, 'carbs': 34.0, 'fat': 0.6, 'category': '菜肴'},
    '炒年糕': {'calories': 220, 'protein': 5.0, 'carbs': 40.0, 'fat': 5.0, 'category': '菜肴'},
    '韩式年糕': {'calories': 240, 'protein': 5.0, 'carbs': 50.0, 'fat': 2.0, 'category': '菜肴'},
    '火锅': {'calories': 300, 'protein': 15.0, 'carbs': 20.0, 'fat': 18.0, 'category': '菜肴'},
    '麻辣火锅': {'calories': 350, 'protein': 15.0, 'carbs': 15.0, 'fat': 25.0, 'category': '菜肴'},
    '涮羊肉': {'calories': 280, 'protein': 22.0, 'carbs': 2.0, 'fat': 20.0, 'category': '菜肴'},
    '涮牛肉': {'calories': 250, 'protein': 24.0, 'carbs': 2.0, 'fat': 16.0, 'category': '菜肴'},
    '串串香': {'calories': 280, 'protein': 15.0, 'carbs': 15.0, 'fat': 18.0, 'category': '菜肴'},
    '麻辣烫': {'calories': 260, 'protein': 12.0, 'carbs': 20.0, 'fat': 15.0, 'category': '菜肴'},
    '冒菜': {'calories': 280, 'protein': 14.0, 'carbs': 18.0, 'fat': 16.0, 'category': '菜肴'},
    '砂锅': {'calories': 240, 'protein': 12.0, 'carbs': 25.0, 'fat': 10.0, 'category': '菜肴'},
    '煲仔饭': {'calories': 380, 'protein': 14.0, 'carbs': 55.0, 'fat': 12.0, 'category': '菜肴'},
    '腊味煲仔饭': {'calories': 420, 'protein': 16.0, 'carbs': 52.0, 'fat': 16.0, 'category': '菜肴'},
    '叉烧饭': {'calories': 400, 'protein': 18.0, 'carbs': 55.0, 'fat': 12.0, 'category': '菜肴'},
    '烧鹅饭': {'calories': 450, 'protein': 20.0, 'carbs': 50.0, 'fat': 20.0, 'category': '菜肴'},
    '鸡腿饭': {'calories': 380, 'protein': 22.0, 'carbs': 48.0, 'fat': 12.0, 'category': '菜肴'},
    '卤肉饭': {'calories': 420, 'protein': 16.0, 'carbs': 50.0, 'fat': 18.0, 'category': '菜肴'},
    '猪脚饭': {'calories': 480, 'protein': 20.0, 'carbs': 45.0, 'fat': 26.0, 'category': '菜肴'},
    '黄焖鸡米饭': {'calories': 380, 'protein': 22.0, 'carbs': 45.0, 'fat': 12.0, 'category': '菜肴'},
    '鸡排饭': {'calories': 450, 'protein': 25.0, 'carbs': 48.0, 'fat': 18.0, 'category': '菜肴'},
    '牛排饭': {'calories': 420, 'protein': 26.0, 'carbs': 45.0, 'fat': 16.0, 'category': '菜肴'},
    '猪排饭': {'calories': 440, 'protein': 22.0, 'carbs': 48.0, 'fat': 18.0, 'category': '菜肴'},
    '鳗鱼饭': {'calories': 380, 'protein': 20.0, 'carbs': 50.0, 'fat': 12.0, 'category': '菜肴'},
    '三文鱼饭': {'calories': 350, 'protein': 22.0, 'carbs': 48.0, 'fat': 10.0, 'category': '菜肴'},
    '寿司': {'calories': 180, 'protein': 6.0, 'carbs': 35.0, 'fat': 1.5, 'category': '菜肴'},
    '三文鱼寿司': {'calories': 160, 'protein': 8.0, 'carbs': 28.0, 'fat': 2.0, 'category': '菜肴'},
    '金枪鱼寿司': {'calories': 150, 'protein': 10.0, 'carbs': 25.0, 'fat': 1.5, 'category': '菜肴'},
    '鳗鱼寿司': {'calories': 200, 'protein': 8.0, 'carbs': 32.0, 'fat': 4.0, 'category': '菜肴'},
    '天妇罗': {'calories': 280, 'protein': 8.0, 'carbs': 30.0, 'fat': 15.0, 'category': '菜肴'},
    '炸猪排': {'calories': 380, 'protein': 20.0, 'carbs': 25.0, 'fat': 22.0, 'category': '菜肴'},
    '炸鸡排': {'calories': 360, 'protein': 22.0, 'carbs': 22.0, 'fat': 20.0, 'category': '菜肴'},
    '炸鱼排': {'calories': 320, 'protein': 18.0, 'carbs': 25.0, 'fat': 16.0, 'category': '菜肴'},
    '炸鱿鱼': {'calories': 280, 'protein': 15.0, 'carbs': 20.0, 'fat': 16.0, 'category': '菜肴'},
    '炸虾': {'calories': 260, 'protein': 14.0, 'carbs': 18.0, 'fat': 15.0, 'category': '菜肴'},
    '薯条': {'calories': 312, 'protein': 3.4, 'carbs': 41.0, 'fat': 15.0, 'category': '菜肴'},
    '薯片': {'calories': 536, 'protein': 7.0, 'carbs': 53.0, 'fat': 35.0, 'category': '菜肴'},
    '爆米花': {'calories': 387, 'protein': 12.9, 'carbs': 77.9, 'fat': 4.5, 'category': '菜肴'},
    '辣条': {'calories': 450, 'protein': 12.0, 'carbs': 50.0, 'fat': 25.0, 'category': '菜肴'},
    '豆腐干': {'calories': 140, 'protein': 16.2, 'carbs': 5.0, 'fat': 6.0, 'category': '菜肴'},
    '臭豆腐': {'calories': 180, 'protein': 12.0, 'carbs': 8.0, 'fat': 12.0, 'category': '菜肴'},
    '腐乳': {'calories': 150, 'protein': 12.0, 'carbs': 5.0, 'fat': 9.0, 'category': '菜肴'},
    '榨菜': {'calories': 30, 'protein': 2.0, 'carbs': 5.0, 'fat': 0.5, 'category': '菜肴'},
    '咸菜': {'calories': 25, 'protein': 1.5, 'carbs': 4.0, 'fat': 0.3, 'category': '菜肴'},
    '泡菜': {'calories': 20, 'protein': 1.0, 'carbs': 3.5, 'fat': 0.2, 'category': '菜肴'},
    '酸菜': {'calories': 18, 'protein': 1.2, 'carbs': 2.8, 'fat': 0.2, 'category': '菜肴'},
    '雪菜': {'calories': 22, 'protein': 1.5, 'carbs': 3.5, 'fat': 0.3, 'category': '菜肴'},
    '梅干菜': {'calories': 35, 'protein': 3.0, 'carbs': 5.0, 'fat': 0.5, 'category': '菜肴'},
    '橄榄菜': {'calories': 120, 'protein': 3.0, 'carbs': 8.0, 'fat': 9.0, 'category': '菜肴'},
    '老干妈': {'calories': 280, 'protein': 6.0, 'carbs': 15.0, 'fat': 23.0, 'category': '菜肴'},
    '辣椒酱': {'calories': 100, 'protein': 2.0, 'carbs': 15.0, 'fat': 4.0, 'category': '菜肴'},
    '豆瓣酱': {'calories': 120, 'protein': 8.0, 'carbs': 18.0, 'fat': 2.0, 'category': '菜肴'},
    '甜面酱': {'calories': 140, 'protein': 5.0, 'carbs': 28.0, 'fat': 1.0, 'category': '菜肴'},
    '芝麻酱': {'calories': 595, 'protein': 19.2, 'carbs': 21.0, 'fat': 52.0, 'category': '菜肴'},
    '花生酱': {'calories': 588, 'protein': 25.0, 'carbs': 20.0, 'fat': 50.0, 'category': '菜肴'},
    '番茄酱': {'calories': 85, 'protein': 2.0, 'carbs': 20.0, 'fat': 0.5, 'category': '菜肴'},
    '沙拉酱': {'calories': 680, 'protein': 1.0, 'carbs': 2.0, 'fat': 75.0, 'category': '菜肴'},
    '蛋黄酱': {'calories': 680, 'protein': 1.0, 'carbs': 2.0, 'fat': 75.0, 'category': '菜肴'},
    '芥末酱': {'calories': 120, 'protein': 5.0, 'carbs': 15.0, 'fat': 5.0, 'category': '菜肴'},
    '咖喱酱': {'calories': 150, 'protein': 4.0, 'carbs': 20.0, 'fat': 7.0, 'category': '菜肴'},
    '沙茶酱': {'calories': 180, 'protein': 6.0, 'carbs': 18.0, 'fat': 10.0, 'category': '菜肴'},
    '蚝油': {'calories': 110, 'protein': 4.0, 'carbs': 22.0, 'fat': 0.5, 'category': '菜肴'},
    '生抽': {'calories': 60, 'protein': 8.0, 'carbs': 8.0, 'fat': 0.0, 'category': '菜肴'},
    '老抽': {'calories': 80, 'protein': 8.0, 'carbs': 12.0, 'fat': 0.0, 'category': '菜肴'},
    '醋': {'calories': 31, 'protein': 0.3, 'carbs': 6.0, 'fat': 0.0, 'category': '菜肴'},
    '料酒': {'calories': 80, 'protein': 0.5, 'carbs': 8.0, 'fat': 0.0, 'category': '菜肴'},
    '香油': {'calories': 884, 'protein': 0.0, 'carbs': 0.0, 'fat': 100.0, 'category': '菜肴'},
    '花椒油': {'calories': 884, 'protein': 0.0, 'carbs': 0.0, 'fat': 100.0, 'category': '菜肴'},
    '辣椒油': {'calories': 900, 'protein': 0.0, 'carbs': 0.0, 'fat': 100.0, 'category': '菜肴'},
    '橄榄油': {'calories': 884, 'protein': 0.0, 'carbs': 0.0, 'fat': 100.0, 'category': '菜肴'},
    '花生油': {'calories': 884, 'protein': 0.0, 'carbs': 0.0, 'fat': 100.0, 'category': '菜肴'},
    '菜籽油': {'calories': 884, 'protein': 0.0, 'carbs': 0.0, 'fat': 100.0, 'category': '菜肴'},
    '玉米油': {'calories': 884, 'protein': 0.0, 'carbs': 0.0, 'fat': 100.0, 'category': '菜肴'},
    '大豆油': {'calories': 884, 'protein': 0.0, 'carbs': 0.0, 'fat': 100.0, 'category': '菜肴'},
    '葵花籽油': {'calories': 884, 'protein': 0.0, 'carbs': 0.0, 'fat': 100.0, 'category': '菜肴'},
    '黄油': {'calories': 717, 'protein': 0.9, 'carbs': 0.1, 'fat': 81.1, 'category': '菜肴'},
    '猪油': {'calories': 902, 'protein': 0.0, 'carbs': 0.0, 'fat': 100.0, 'category': '菜肴'},
    '牛油': {'calories': 902, 'protein': 0.0, 'carbs': 0.0, 'fat': 100.0, 'category': '菜肴'},
    '羊油': {'calories': 902, 'protein': 0.0, 'carbs': 0.0, 'fat': 100.0, 'category': '菜肴'},
    '鸡油': {'calories': 902, 'protein': 0.0, 'carbs': 0.0, 'fat': 100.0, 'category': '菜肴'},
    '鱼油': {'calories': 902, 'protein': 0.0, 'carbs': 0.0, 'fat': 100.0, 'category': '菜肴'},
    '奶油': {'calories': 350, 'protein': 2.0, 'carbs': 3.0, 'fat': 37.0, 'category': '菜肴'},
    '奶酪': {'calories': 350, 'protein': 25.0, 'carbs': 2.0, 'fat': 27.0, 'category': '菜肴'},
    '芝士': {'calories': 350, 'protein': 25.0, 'carbs': 2.0, 'fat': 27.0, 'category': '菜肴'},
    '炼乳': {'calories': 330, 'protein': 8.0, 'carbs': 55.0, 'fat': 8.0, 'category': '菜肴'},
    '奶粉': {'calories': 500, 'protein': 26.0, 'carbs': 38.0, 'fat': 27.0, 'category': '菜肴'},
    '蛋白粉': {'calories': 400, 'protein': 80.0, 'carbs': 8.0, 'fat': 5.0, 'category': '菜肴'},
    '代餐粉': {'calories': 380, 'protein': 25.0, 'carbs': 50.0, 'fat': 8.0, 'category': '菜肴'},
    '藕粉': {'calories': 350, 'protein': 2.0, 'carbs': 85.0, 'fat': 0.5, 'category': '菜肴'},
    '葛根粉': {'calories': 340, 'protein': 2.0, 'carbs': 82.0, 'fat': 0.5, 'category': '菜肴'},
    '芝麻糊': {'calories': 420, 'protein': 12.0, 'carbs': 60.0, 'fat': 16.0, 'category': '菜肴'},
    '核桃粉': {'calories': 450, 'protein': 15.0, 'carbs': 55.0, 'fat': 20.0, 'category': '菜肴'},
    '杏仁粉': {'calories': 580, 'protein': 22.0, 'carbs': 20.0, 'fat': 50.0, 'category': '菜肴'},
    '豆浆粉': {'calories': 380, 'protein': 35.0, 'carbs': 35.0, 'fat': 15.0, 'category': '菜肴'},
    '豆腐脑': {'calories': 45, 'protein': 4.0, 'carbs': 3.0, 'fat': 2.0, 'category': '菜肴'},
    '豆花': {'calories': 45, 'protein': 4.0, 'carbs': 3.0, 'fat': 2.0, 'category': '菜肴'},
    '凉粉': {'calories': 37, 'protein': 0.2, 'carbs': 9.0, 'fat': 0.1, 'category': '菜肴'},
    '冰粉': {'calories': 40, 'protein': 0.2, 'carbs': 10.0, 'fat': 0.1, 'category': '菜肴'},
    '仙草冻': {'calories': 35, 'protein': 0.5, 'carbs': 8.0, 'fat': 0.2, 'category': '菜肴'},
    '烧仙草': {'calories': 80, 'protein': 2.0, 'carbs': 15.0, 'fat': 1.5, 'category': '菜肴'},
    '布丁': {'calories': 120, 'protein': 3.0, 'carbs': 20.0, 'fat': 3.5, 'category': '菜肴'},
    '果冻': {'calories': 60, 'protein': 1.0, 'carbs': 14.0, 'fat': 0.0, 'category': '菜肴'},
    '棉花糖': {'calories': 340, 'protein': 2.0, 'carbs': 82.0, 'fat': 0.0, 'category': '菜肴'},
    '棒棒糖': {'calories': 400, 'protein': 0.0, 'carbs': 100.0, 'fat': 0.0, 'category': '菜肴'},
    '巧克力': {'calories': 546, 'protein': 4.9, 'carbs': 61.0, 'fat': 31.0, 'category': '菜肴'},
    '黑巧克力': {'calories': 598, 'protein': 7.8, 'carbs': 45.8, 'fat': 42.6, 'category': '菜肴'},
    '白巧克力': {'calories': 539, 'protein': 5.9, 'carbs': 59.2, 'fat': 32.1, 'category': '菜肴'},
    '牛奶巧克力': {'calories': 535, 'protein': 7.6, 'carbs': 59.4, 'fat': 29.7, 'category': '菜肴'},
    '夹心巧克力': {'calories': 550, 'protein': 6.0, 'carbs': 60.0, 'fat': 32.0, 'category': '菜肴'},
    '麦丽素': {'calories': 520, 'protein': 6.0, 'carbs': 65.0, 'fat': 26.0, 'category': '菜肴'},
    '士力架': {'calories': 500, 'protein': 9.0, 'carbs': 55.0, 'fat': 27.0, 'category': '菜肴'},
    '德芙巧克力': {'calories': 540, 'protein': 6.0, 'carbs': 58.0, 'fat': 31.0, 'category': '菜肴'},
    '费列罗': {'calories': 580, 'protein': 8.0, 'carbs': 45.0, 'fat': 42.0, 'category': '菜肴'},
    '口香糖': {'calories': 200, 'protein': 0.0, 'carbs': 70.0, 'fat': 0.0, 'category': '菜肴'},
    '薄荷糖': {'calories': 380, 'protein': 0.0, 'carbs': 95.0, 'fat': 0.0, 'category': '菜肴'},
    '话梅': {'calories': 280, 'protein': 2.0, 'carbs': 65.0, 'fat': 0.5, 'category': '菜肴'},
    '陈皮': {'calories': 290, 'protein': 4.0, 'carbs': 65.0, 'fat': 1.0, 'category': '菜肴'},
    '蜜饯': {'calories': 320, 'protein': 1.0, 'carbs': 78.0, 'fat': 0.5, 'category': '菜肴'},
    '果脯': {'calories': 310, 'protein': 1.0, 'carbs': 76.0, 'fat': 0.5, 'category': '菜肴'},
    '葡萄干': {'calories': 299, 'protein': 3.1, 'carbs': 79.2, 'fat': 0.5, 'category': '菜肴'},
    '蔓越莓干': {'calories': 308, 'protein': 0.2, 'carbs': 82.4, 'fat': 1.4, 'category': '菜肴'},
    '蓝莓干': {'calories': 320, 'protein': 2.5, 'carbs': 80.0, 'fat': 1.0, 'category': '菜肴'},
    '草莓干': {'calories': 325, 'protein': 3.0, 'carbs': 80.0, 'fat': 1.5, 'category': '菜肴'},
    '芒果干': {'calories': 319, 'protein': 2.5, 'carbs': 78.0, 'fat': 1.0, 'category': '菜肴'},
    '菠萝干': {'calories': 300, 'protein': 2.0, 'carbs': 75.0, 'fat': 1.0, 'category': '菜肴'},
    '香蕉干': {'calories': 350, 'protein': 3.5, 'carbs': 85.0, 'fat': 1.5, 'category': '菜肴'},
    '苹果干': {'calories': 280, 'protein': 1.5, 'carbs': 70.0, 'fat': 0.5, 'category': '菜肴'},
    '杏干': {'calories': 310, 'protein': 3.0, 'carbs': 75.0, 'fat': 0.5, 'category': '菜肴'},
    '桃干': {'calories': 290, 'protein': 2.5, 'carbs': 70.0, 'fat': 0.5, 'category': '菜肴'},
    '李子干': {'calories': 295, 'protein': 2.0, 'carbs': 72.0, 'fat': 0.5, 'category': '菜肴'},
    '柿饼': {'calories': 250, 'protein': 2.0, 'carbs': 62.0, 'fat': 0.5, 'category': '菜肴'},
    '红枣干': {'calories': 310, 'protein': 4.0, 'carbs': 75.0, 'fat': 1.0, 'category': '菜肴'},
    '桂圆干': {'calories': 280, 'protein': 5.0, 'carbs': 68.0, 'fat': 0.5, 'category': '菜肴'},
    '枸杞干': {'calories': 350, 'protein': 14.0, 'carbs': 68.0, 'fat': 2.0, 'category': '菜肴'},
    '山楂片': {'calories': 320, 'protein': 2.0, 'carbs': 78.0, 'fat': 1.0, 'category': '菜肴'},
    '山楂糕': {'calories': 280, 'protein': 1.5, 'carbs': 68.0, 'fat': 0.5, 'category': '菜肴'},
    '果丹皮': {'calories': 300, 'protein': 1.5, 'carbs': 72.0, 'fat': 0.5, 'category': '菜肴'},
    '阿胶糕': {'calories': 380, 'protein': 8.0, 'carbs': 70.0, 'fat': 8.0, 'category': '菜肴'},
    '芝麻糕': {'calories': 450, 'protein': 10.0, 'carbs': 55.0, 'fat': 22.0, 'category': '菜肴'},
    '花生糕': {'calories': 520, 'protein': 15.0, 'carbs': 50.0, 'fat': 30.0, 'category': '菜肴'},
    '核桃糕': {'calories': 480, 'protein': 12.0, 'carbs': 55.0, 'fat': 25.0, 'category': '菜肴'},
    '杏仁糕': {'calories': 500, 'protein': 14.0, 'carbs': 50.0, 'fat': 28.0, 'category': '菜肴'},
    '椰子糖': {'calories': 450, 'protein': 2.0, 'carbs': 85.0, 'fat': 12.0, 'category': '菜肴'},
    '榴莲糖': {'calories': 480, 'protein': 3.0, 'carbs': 80.0, 'fat': 18.0, 'category': '菜肴'},
    '大白兔奶糖': {'calories': 420, 'protein': 4.0, 'carbs': 85.0, 'fat': 8.0, 'category': '菜肴'},
    '牛轧糖': {'calories': 480, 'protein': 8.0, 'carbs': 70.0, 'fat': 20.0, 'category': '菜肴'},
    '雪花酥': {'calories': 450, 'protein': 6.0, 'carbs': 65.0, 'fat': 18.0, 'category': '菜肴'},
    '沙琪玛': {'calories': 460, 'protein': 8.0, 'carbs': 68.0, 'fat': 18.0, 'category': '菜肴'},
    '麻花': {'calories': 520, 'protein': 8.0, 'carbs': 60.0, 'fat': 28.0, 'category': '菜肴'},
    '馓子': {'calories': 540, 'protein': 10.0, 'carbs': 55.0, 'fat': 32.0, 'category': '菜肴'},
    '江米条': {'calories': 480, 'protein': 6.0, 'carbs': 70.0, 'fat': 20.0, 'category': '菜肴'},
    '萨其马': {'calories': 460, 'protein': 8.0, 'carbs': 68.0, 'fat': 18.0, 'category': '菜肴'},
    '龙须酥': {'calories': 420, 'protein': 6.0, 'carbs': 75.0, 'fat': 12.0, 'category': '菜肴'},
    '云片糕': {'calories': 380, 'protein': 5.0, 'carbs': 80.0, 'fat': 4.0, 'category': '菜肴'},
    '芡实糕': {'calories': 350, 'protein': 6.0, 'carbs': 75.0, 'fat': 2.0, 'category': '菜肴'},
    '桂花糕': {'calories': 340, 'protein': 5.0, 'carbs': 72.0, 'fat': 3.0, 'category': '菜肴'},
    '马蹄糕': {'calories': 280, 'protein': 4.0, 'carbs': 65.0, 'fat': 1.0, 'category': '菜肴'},
    '萝卜糕': {'calories': 180, 'protein': 5.0, 'carbs': 35.0, 'fat': 2.0, 'category': '菜肴'},
    '芋头糕': {'calories': 220, 'protein': 4.0, 'carbs': 45.0, 'fat': 3.0, 'category': '菜肴'},
    '年糕片': {'calories': 200, 'protein': 4.0, 'carbs': 45.0, 'fat': 1.0, 'category': '菜肴'},
    '糍粑': {'calories': 250, 'protein': 4.0, 'carbs': 55.0, 'fat': 2.0, 'category': '菜肴'},
    '青团': {'calories': 280, 'protein': 5.0, 'carbs': 58.0, 'fat': 3.0, 'category': '菜肴'},
    '清明果': {'calories': 260, 'protein': 5.0, 'carbs': 55.0, 'fat': 2.5, 'category': '菜肴'},
    '艾叶粑粑': {'calories': 240, 'protein': 4.0, 'carbs': 52.0, 'fat': 2.0, 'category': '菜肴'},
    '粽子叶': {'calories': 0, 'protein': 0.0, 'carbs': 0.0, 'fat': 0.0, 'category': '菜肴'},
    '荷叶': {'calories': 0, 'protein': 0.0, 'carbs': 0.0, 'fat': 0.0, 'category': '菜肴'},
    '玉米叶': {'calories': 0, 'protein': 0.0, 'carbs': 0.0, 'fat': 0.0, 'category': '菜肴'},
    '芭蕉叶': {'calories': 0, 'protein': 0.0, 'carbs': 0.0, 'fat': 0.0, 'category': '菜肴'},
    '粽叶': {'calories': 0, 'protein': 0.0, 'carbs': 0.0, 'fat': 0.0, 'category': '菜肴'},
    
    '黄芪': {'calories': 35, 'protein': 1.8, 'carbs': 7.0, 'fat': 0.3, 'category': '蔬菜'},
    '枸杞': {'calories': 258, 'protein': 13.9, 'carbs': 64.1, 'fat': 1.5, 'category': '蔬菜'},
    '红枣': {'calories': 276, 'protein': 3.2, 'carbs': 67.8, 'fat': 0.5, 'category': '蔬菜'},
    '桂圆': {'calories': 71, 'protein': 1.2, 'carbs': 16.6, 'fat': 0.1, 'category': '蔬菜'},
    '莲子': {'calories': 344, 'protein': 17.2, 'carbs': 64.5, 'fat': 2.0, 'category': '蔬菜'},
    '薏米': {'calories': 361, 'protein': 12.8, 'carbs': 71.1, 'fat': 3.3, 'category': '蔬菜'},
    '红豆': {'calories': 324, 'protein': 20.2, 'carbs': 63.4, 'fat': 0.6, 'category': '蔬菜'},
    '绿豆': {'calories': 316, 'protein': 21.6, 'carbs': 62.0, 'fat': 0.8, 'category': '蔬菜'},
    '黑豆': {'calories': 381, 'protein': 36.0, 'carbs': 33.6, 'fat': 15.9, 'category': '蔬菜'},
    '黄豆': {'calories': 390, 'protein': 35.0, 'carbs': 34.2, 'fat': 16.0, 'category': '蔬菜'},
    '豌豆': {'calories': 81, 'protein': 5.4, 'carbs': 14.5, 'fat': 0.4, 'category': '蔬菜'},
    '蚕豆': {'calories': 104, 'protein': 8.8, 'carbs': 16.5, 'fat': 0.4, 'category': '蔬菜'},
    '芸豆': {'calories': 315, 'protein': 23.4, 'carbs': 60.0, 'fat': 1.5, 'category': '蔬菜'},
    '花豆': {'calories': 328, 'protein': 19.1, 'carbs': 65.0, 'fat': 1.0, 'category': '蔬菜'},
    '鹰嘴豆': {'calories': 364, 'protein': 19.3, 'carbs': 60.7, 'fat': 6.0, 'category': '蔬菜'},
    '扁豆': {'calories': 37, 'protein': 2.5, 'carbs': 7.0, 'fat': 0.2, 'category': '蔬菜'},
    '四季豆': {'calories': 31, 'protein': 2.0, 'carbs': 7.0, 'fat': 0.1, 'category': '蔬菜'},
    '荷兰豆': {'calories': 27, 'protein': 2.5, 'carbs': 4.9, 'fat': 0.3, 'category': '蔬菜'},
    '豇豆': {'calories': 33, 'protein': 2.9, 'carbs': 6.9, 'fat': 0.3, 'category': '蔬菜'},
    '毛豆': {'calories': 131, 'protein': 13.1, 'carbs': 10.5, 'fat': 5.0, 'category': '蔬菜'},
    '青豆': {'calories': 81, 'protein': 5.4, 'carbs': 14.5, 'fat': 0.4, 'category': '蔬菜'},
    '甜豆': {'calories': 27, 'protein': 2.5, 'carbs': 4.9, 'fat': 0.3, 'category': '蔬菜'},
    '豆芽': {'calories': 44, 'protein': 4.5, 'carbs': 5.1, 'fat': 1.0, 'category': '蔬菜'},
    '绿豆芽': {'calories': 18, 'protein': 2.1, 'carbs': 2.9, 'fat': 0.1, 'category': '蔬菜'},
    '黄豆芽': {'calories': 44, 'protein': 4.5, 'carbs': 5.1, 'fat': 1.0, 'category': '蔬菜'},
    '黑豆芽': {'calories': 44, 'protein': 4.5, 'carbs': 5.1, 'fat': 1.0, 'category': '蔬菜'},
    '豌豆芽': {'calories': 44, 'protein': 4.5, 'carbs': 5.1, 'fat': 1.0, 'category': '蔬菜'},
    '萝卜芽': {'calories': 44, 'protein': 4.5, 'carbs': 5.1, 'fat': 1.0, 'category': '蔬菜'},
    '荞麦芽': {'calories': 44, 'protein': 4.5, 'carbs': 5.1, 'fat': 1.0, 'category': '蔬菜'},
    '香椿芽': {'calories': 47, 'protein': 1.7, 'carbs': 10.9, 'fat': 0.4, 'category': '蔬菜'},
    '蒜苗': {'calories': 37, 'protein': 2.1, 'carbs': 8.0, 'fat': 0.4, 'category': '蔬菜'},
    '蒜黄': {'calories': 29, 'protein': 2.6, 'carbs': 5.2, 'fat': 0.3, 'category': '蔬菜'},
    '韭黄': {'calories': 24, 'protein': 2.4, 'carbs': 3.9, 'fat': 0.2, 'category': '蔬菜'},
    '韭菜': {'calories': 30, 'protein': 2.4, 'carbs': 4.6, 'fat': 0.4, 'category': '蔬菜'},
    '韭苔': {'calories': 29, 'protein': 2.0, 'carbs': 6.0, 'fat': 0.3, 'category': '蔬菜'},
    '韭菜花': {'calories': 29, 'protein': 2.0, 'carbs': 6.0, 'fat': 0.3, 'category': '蔬菜'},
    '韭菜籽': {'calories': 29, 'protein': 2.0, 'carbs': 6.0, 'fat': 0.3, 'category': '蔬菜'},
    '大葱': {'calories': 33, 'protein': 1.7, 'carbs': 6.5, 'fat': 0.3, 'category': '蔬菜'},
    '小葱': {'calories': 33, 'protein': 1.7, 'carbs': 6.5, 'fat': 0.3, 'category': '蔬菜'},
    '洋葱': {'calories': 40, 'protein': 1.1, 'carbs': 9.0, 'fat': 0.1, 'category': '蔬菜'},
    '洋葱头': {'calories': 40, 'protein': 1.1, 'carbs': 9.0, 'fat': 0.1, 'category': '蔬菜'},
    '红葱头': {'calories': 40, 'protein': 1.1, 'carbs': 9.0, 'fat': 0.1, 'category': '蔬菜'},
    ' shallot ': {'calories': 40, 'protein': 1.1, 'carbs': 9.0, 'fat': 0.1, 'category': '蔬菜'},
    '韭葱': {'calories': 33, 'protein': 1.7, 'carbs': 6.5, 'fat': 0.3, 'category': '蔬菜'},
    '大蒜': {'calories': 149, 'protein': 6.4, 'carbs': 33.1, 'fat': 0.5, 'category': '蔬菜'},
    '生姜': {'calories': 80, 'protein': 1.8, 'carbs': 17.8, 'fat': 0.8, 'category': '蔬菜'},
    '姜黄': {'calories': 80, 'protein': 1.8, 'carbs': 17.8, 'fat': 0.8, 'category': '蔬菜'},
    '高良姜': {'calories': 80, 'protein': 1.8, 'carbs': 17.8, 'fat': 0.8, 'category': '蔬菜'},
    '芥末': {'calories': 80, 'protein': 1.8, 'carbs': 17.8, 'fat': 0.8, 'category': '蔬菜'},
    '辣根': {'calories': 80, 'protein': 1.8, 'carbs': 17.8, 'fat': 0.8, 'category': '蔬菜'},
    '小萝卜': {'calories': 16, 'protein': 0.7, 'carbs': 3.4, 'fat': 0.1, 'category': '蔬菜'},
    '白萝卜': {'calories': 18, 'protein': 0.6, 'carbs': 4.1, 'fat': 0.1, 'category': '蔬菜'},
    '芜菁': {'calories': 28, 'protein': 0.9, 'carbs': 6.4, 'fat': 0.1, 'category': '蔬菜'},
    '瑞典芜菁': {'calories': 38, 'protein': 1.2, 'carbs': 8.6, 'fat': 0.2, 'category': '蔬菜'},
    '欧防风': {'calories': 75, 'protein': 1.2, 'carbs': 18.0, 'fat': 0.3, 'category': '蔬菜'},
    '根芹': {'calories': 42, 'protein': 1.5, 'carbs': 9.2, 'fat': 0.3, 'category': '蔬菜'},
    '球茎甘蓝': {'calories': 27, 'protein': 1.7, 'carbs': 6.2, 'fat': 0.1, 'category': '蔬菜'},
    '茴香': {'calories': 31, 'protein': 1.2, 'carbs': 7.3, 'fat': 0.2, 'category': '蔬菜'},
    '芹菜': {'calories': 14, 'protein': 0.8, 'carbs': 3.0, 'fat': 0.1, 'category': '蔬菜'},
    '根用芹菜': {'calories': 42, 'protein': 1.5, 'carbs': 9.2, 'fat': 0.3, 'category': '蔬菜'},
    '大黄': {'calories': 21, 'protein': 0.9, 'carbs': 4.5, 'fat': 0.2, 'category': '蔬菜'},
    '芦笋': {'calories': 20, 'protein': 2.2, 'carbs': 3.9, 'fat': 0.2, 'category': '蔬菜'},
    '洋蓟': {'calories': 47, 'protein': 3.3, 'carbs': 10.5, 'fat': 0.2, 'category': '蔬菜'},
    '竹笋': {'calories': 27, 'protein': 2.6, 'carbs': 5.1, 'fat': 0.2, 'category': '蔬菜'},
    '莲藕': {'calories': 47, 'protein': 1.2, 'carbs': 11.5, 'fat': 0.2, 'category': '蔬菜'},
    '马蹄': {'calories': 59, 'protein': 1.2, 'carbs': 14.2, 'fat': 0.2, 'category': '蔬菜'},
    '芋头': {'calories': 56, 'protein': 1.3, 'carbs': 13.0, 'fat': 0.2, 'category': '蔬菜'},
    '山药': {'calories': 57, 'protein': 1.9, 'carbs': 12.4, 'fat': 0.2, 'category': '蔬菜'},
    '木薯': {'calories': 160, 'protein': 1.4, 'carbs': 38.1, 'fat': 0.3, 'category': '蔬菜'},
    '红薯': {'calories': 86, 'protein': 1.6, 'carbs': 20.1, 'fat': 0.1, 'category': '蔬菜'},
    '紫薯': {'calories': 82, 'protein': 1.3, 'carbs': 18.0, 'fat': 0.2, 'category': '蔬菜'},
    '凉薯': {'calories': 38, 'protein': 0.7, 'carbs': 8.8, 'fat': 0.1, 'category': '蔬菜'},
}


def get_food_nutrition(food_name):
    """
    根据食物名称获取营养数据
    优先从数据库查询，没有则返回默认值
    """
    # 直接匹配
    if food_name in FOOD_NUTRITION_DB:
        return FOOD_NUTRITION_DB[food_name]
    
    # 模糊匹配
    for name, nutrition in FOOD_NUTRITION_DB.items():
        if name in food_name or food_name in name:
            return nutrition
    
    # 返回默认值
    return {
        'calories': 100,
        'protein': 3,
        'carbs': 15,
        'fat': 2,
        'category': '其他'
    }
