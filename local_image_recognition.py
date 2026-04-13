# -*- coding: utf-8 -*-
"""
本地图片识别模块
基于图片特征（颜色直方图、纹理）进行简单匹配
"""

import base64
import io
from datetime import datetime
from PIL import Image
import numpy as np
from collections import Counter

# 食物特征数据库 - 基于典型食物的颜色特征
# 每个食物包含主色调、辅助色调和亮度范围
FOOD_FEATURES = {
    # ===== 主食类 =====
    '米饭': {'color': [240, 240, 230], 'color2': [255, 255, 250], 'brightness': [200, 255], 'categories': ['主食']},
    '面条': {'color': [245, 230, 180], 'color2': [255, 240, 200], 'brightness': [200, 255], 'categories': ['主食']},
    '馒头': {'color': [250, 245, 235], 'color2': [255, 252, 245], 'brightness': [230, 255], 'categories': ['主食']},
    '面包': {'color': [200, 160, 100], 'color2': [180, 140, 80], 'brightness': [140, 200], 'categories': ['主食']},
    '全麦面包': {'color': [160, 130, 90], 'color2': [140, 110, 70], 'brightness': [100, 170], 'categories': ['主食']},
    '吐司': {'color': [220, 190, 140], 'color2': [200, 170, 120], 'brightness': [160, 220], 'categories': ['主食']},
    '包子': {'color': [245, 240, 230], 'color2': [255, 250, 240], 'brightness': [220, 255], 'categories': ['主食']},
    '饺子': {'color': [250, 250, 245], 'color2': [240, 240, 235], 'brightness': [230, 255], 'categories': ['主食']},
    '粥': {'color': [240, 235, 220], 'color2': [250, 245, 230], 'brightness': [210, 250], 'categories': ['主食']},
    '饼干': {'color': [210, 170, 120], 'color2': [190, 150, 100], 'brightness': [150, 200], 'categories': ['主食']},
    '蛋糕': {'color': [250, 220, 180], 'color2': [240, 200, 160], 'brightness': [180, 240], 'categories': ['主食']},
    '三明治': {'color': [230, 210, 180], 'color2': [200, 180, 150], 'brightness': [170, 220], 'categories': ['主食']},
    
    # ===== 蔬菜类 =====
    '西红柿': {'color': [220, 60, 40], 'color2': [200, 50, 30], 'brightness': [80, 150], 'categories': ['蔬菜']},
    '胡萝卜': {'color': [240, 140, 30], 'color2': [255, 160, 50], 'brightness': [150, 220], 'categories': ['蔬菜']},
    '黄瓜': {'color': [100, 160, 60], 'color2': [80, 140, 40], 'brightness': [100, 160], 'categories': ['蔬菜']},
    '白菜': {'color': [240, 250, 230], 'color2': [220, 240, 210], 'brightness': [200, 255], 'categories': ['蔬菜']},
    '土豆': {'color': [230, 210, 150], 'color2': [210, 190, 130], 'brightness': [160, 220], 'categories': ['蔬菜', '主食']},
    '青菜': {'color': [60, 140, 50], 'color2': [40, 120, 30], 'brightness': [60, 120], 'categories': ['蔬菜']},
    '菠菜': {'color': [40, 120, 40], 'color2': [30, 100, 30], 'brightness': [50, 100], 'categories': ['蔬菜']},
    '西兰花': {'color': [80, 150, 60], 'color2': [60, 130, 40], 'brightness': [80, 140], 'categories': ['蔬菜']},
    '茄子': {'color': [100, 60, 120], 'color2': [80, 40, 100], 'brightness': [60, 100], 'categories': ['蔬菜']},
    '南瓜': {'color': [240, 160, 40], 'color2': [255, 180, 60], 'brightness': [160, 220], 'categories': ['蔬菜']},
    '玉米': {'color': [255, 220, 80], 'color2': [240, 200, 60], 'brightness': [180, 240], 'categories': ['蔬菜']},
    '洋葱': {'color': [240, 220, 200], 'color2': [220, 180, 160], 'brightness': [180, 230], 'categories': ['蔬菜']},
    '青椒': {'color': [80, 160, 60], 'color2': [60, 140, 40], 'brightness': [80, 140], 'categories': ['蔬菜']},
    '红椒': {'color': [220, 50, 40], 'color2': [200, 40, 30], 'brightness': [80, 150], 'categories': ['蔬菜']},
    '芹菜': {'color': [150, 200, 100], 'color2': [120, 180, 80], 'brightness': [140, 190], 'categories': ['蔬菜']},
    '生菜': {'color': [140, 200, 100], 'color2': [120, 180, 80], 'brightness': [140, 190], 'categories': ['蔬菜']},
    '蘑菇': {'color': [200, 190, 180], 'color2': [180, 170, 160], 'brightness': [160, 200], 'categories': ['蔬菜']},
    
    # ===== 肉类 =====
    '猪肉': {'color': [200, 120, 120], 'color2': [180, 100, 100], 'brightness': [120, 180], 'categories': ['肉类']},
    '鸡肉': {'color': [230, 200, 160], 'color2': [210, 180, 140], 'brightness': [170, 220], 'categories': ['肉类']},
    '牛肉': {'color': [160, 80, 60], 'color2': [140, 60, 40], 'brightness': [80, 140], 'categories': ['肉类']},
    '红烧肉': {'color': [140, 60, 40], 'color2': [120, 50, 30], 'brightness': [60, 120], 'categories': ['肉类', '菜肴']},
    '排骨': {'color': [180, 140, 100], 'color2': [160, 120, 80], 'brightness': [120, 170], 'categories': ['肉类']},
    '火腿肠': {'color': [220, 160, 140], 'color2': [200, 140, 120], 'brightness': [150, 200], 'categories': ['肉类']},
    '香肠': {'color': [200, 100, 80], 'color2': [180, 80, 60], 'brightness': [100, 160], 'categories': ['肉类']},
    '培根': {'color': [180, 120, 100], 'color2': [160, 100, 80], 'brightness': [120, 170], 'categories': ['肉类']},
    '牛排': {'color': [150, 90, 70], 'color2': [130, 70, 50], 'brightness': [80, 140], 'categories': ['肉类']},
    '鸡腿': {'color': [200, 160, 120], 'color2': [180, 140, 100], 'brightness': [140, 190], 'categories': ['肉类']},
    
    # ===== 蛋类 =====
    '鸡蛋': {'color': [250, 220, 150], 'color2': [255, 230, 170], 'brightness': [200, 255], 'categories': ['蛋类']},
    '煎蛋': {'color': [255, 200, 80], 'color2': [255, 180, 60], 'brightness': [180, 240], 'categories': ['蛋类']},
    '茶叶蛋': {'color': [160, 120, 80], 'color2': [140, 100, 60], 'brightness': [100, 150], 'categories': ['蛋类']},
    '水煮蛋': {'color': [240, 230, 200], 'color2': [255, 245, 220], 'brightness': [210, 250], 'categories': ['蛋类']},
    '炒蛋': {'color': [255, 220, 100], 'color2': [255, 200, 80], 'brightness': [200, 255], 'categories': ['蛋类']},
    
    # ===== 水果类 =====
    '苹果': {'color': [220, 60, 50], 'color2': [200, 80, 70], 'brightness': [100, 180], 'categories': ['水果']},
    '香蕉': {'color': [250, 230, 100], 'color2': [255, 240, 120], 'brightness': [200, 255], 'categories': ['水果']},
    '橙子': {'color': [255, 140, 30], 'color2': [255, 160, 50], 'brightness': [160, 220], 'categories': ['水果']},
    '西瓜': {'color': [240, 80, 70], 'color2': [255, 100, 90], 'brightness': [120, 200], 'categories': ['水果']},
    '葡萄': {'color': [120, 50, 120], 'color2': [100, 30, 100], 'brightness': [60, 120], 'categories': ['水果']},
    '草莓': {'color': [230, 60, 70], 'color2': [255, 80, 90], 'brightness': [100, 180], 'categories': ['水果']},
    '梨': {'color': [240, 230, 150], 'color2': [255, 245, 170], 'brightness': [200, 250], 'categories': ['水果']},
    '桃子': {'color': [255, 180, 150], 'color2': [255, 200, 170], 'brightness': [180, 230], 'categories': ['水果']},
    '芒果': {'color': [255, 200, 60], 'color2': [255, 220, 80], 'brightness': [200, 255], 'categories': ['水果']},
    '猕猴桃': {'color': [140, 180, 60], 'color2': [120, 160, 40], 'brightness': [120, 170], 'categories': ['水果']},
    '蓝莓': {'color': [80, 80, 160], 'color2': [60, 60, 140], 'brightness': [60, 100], 'categories': ['水果']},
    '樱桃': {'color': [200, 40, 50], 'color2': [180, 30, 40], 'brightness': [80, 140], 'categories': ['水果']},
    
    # ===== 海鲜类 =====
    '虾': {'color': [255, 140, 100], 'color2': [255, 160, 120], 'brightness': [160, 220], 'categories': ['海鲜']},
    '鱼': {'color': [200, 180, 140], 'color2': [180, 160, 120], 'brightness': [150, 200], 'categories': ['海鲜']},
    '螃蟹': {'color': [220, 100, 60], 'color2': [255, 120, 80], 'brightness': [120, 180], 'categories': ['海鲜']},
    '三文鱼': {'color': [255, 140, 120], 'color2': [255, 160, 140], 'brightness': [160, 220], 'categories': ['海鲜']},
    '鱿鱼': {'color': [240, 220, 200], 'color2': [255, 240, 220], 'brightness': [200, 250], 'categories': ['海鲜']},
    '贝类': {'color': [220, 200, 180], 'color2': [200, 180, 160], 'brightness': [180, 220], 'categories': ['海鲜']},
    
    # ===== 豆制品 =====
    '豆腐': {'color': [250, 250, 240], 'color2': [255, 255, 250], 'brightness': [230, 255], 'categories': ['蔬菜']},
    '豆浆': {'color': [245, 240, 220], 'color2': [255, 250, 230], 'brightness': [220, 255], 'categories': ['饮品']},
    '豆腐干': {'color': [200, 180, 140], 'color2': [180, 160, 120], 'brightness': [150, 200], 'categories': ['蔬菜']},
    '腐竹': {'color': [220, 200, 160], 'color2': [200, 180, 140], 'brightness': [170, 220], 'categories': ['蔬菜']},
    
    # ===== 饮品 =====
    '牛奶': {'color': [250, 250, 245], 'color2': [255, 255, 250], 'brightness': [240, 255], 'categories': ['饮品']},
    '咖啡': {'color': [100, 70, 50], 'color2': [80, 50, 30], 'brightness': [50, 100], 'categories': ['饮品']},
    '茶': {'color': [180, 160, 100], 'color2': [160, 140, 80], 'brightness': [130, 180], 'categories': ['饮品']},
    '果汁': {'color': [240, 160, 40], 'color2': [255, 180, 60], 'brightness': [160, 220], 'categories': ['饮品']},
    '可乐': {'color': [60, 40, 30], 'color2': [80, 50, 40], 'brightness': [30, 70], 'categories': ['饮品']},
    '奶茶': {'color': [200, 170, 130], 'color2': [180, 150, 110], 'brightness': [150, 200], 'categories': ['饮品']},
    '啤酒': {'color': [240, 200, 80], 'color2': [255, 220, 100], 'brightness': [180, 240], 'categories': ['饮品']},
    '红酒': {'color': [140, 40, 60], 'color2': [120, 30, 50], 'brightness': [50, 100], 'categories': ['饮品']},
    
    # ===== 常见菜肴 =====
    '炒饭': {'color': [230, 200, 120], 'color2': [210, 180, 100], 'brightness': [170, 220], 'categories': ['菜肴', '主食']},
    '炒面': {'color': [220, 180, 100], 'color2': [200, 160, 80], 'brightness': [160, 210], 'categories': ['菜肴', '主食']},
    '汉堡': {'color': [200, 160, 100], 'color2': [180, 140, 80], 'brightness': [140, 190], 'categories': ['菜肴']},
    '披萨': {'color': [220, 180, 120], 'color2': [200, 160, 100], 'brightness': [160, 210], 'categories': ['菜肴']},
    '寿司': {'color': [240, 240, 230], 'color2': [255, 255, 245], 'brightness': [220, 255], 'categories': ['菜肴']},
    '沙拉': {'color': [150, 180, 100], 'color2': [130, 160, 80], 'brightness': [140, 180], 'categories': ['菜肴', '蔬菜']},
    '汤': {'color': [220, 200, 160], 'color2': [240, 220, 180], 'brightness': [180, 230], 'categories': ['菜肴']},
    '火锅': {'color': [200, 80, 60], 'color2': [180, 60, 40], 'brightness': [80, 140], 'categories': ['菜肴']},
    '烧烤': {'color': [160, 100, 70], 'color2': [140, 80, 50], 'brightness': [80, 140], 'categories': ['菜肴']},
    '炸鸡': {'color': [220, 180, 100], 'color2': [255, 200, 120], 'brightness': [180, 240], 'categories': ['菜肴', '肉类']},
    '薯条': {'color': [255, 200, 80], 'color2': [255, 220, 100], 'brightness': [200, 255], 'categories': ['菜肴', '主食']},
    '意面': {'color': [240, 200, 120], 'color2': [220, 180, 100], 'brightness': [180, 230], 'categories': ['菜肴', '主食']},
    '咖喱饭': {'color': [220, 180, 100], 'color2': [200, 160, 80], 'brightness': [160, 210], 'categories': ['菜肴', '主食']},
    '麻辣烫': {'color': [200, 100, 60], 'color2': [180, 80, 40], 'brightness': [80, 150], 'categories': ['菜肴']},
    '酸菜鱼': {'color': [200, 180, 140], 'color2': [220, 200, 160], 'brightness': [170, 220], 'categories': ['菜肴', '海鲜']},
    '宫保鸡丁': {'color': [200, 120, 80], 'color2': [180, 100, 60], 'brightness': [100, 160], 'categories': ['菜肴', '肉类']},
    '麻婆豆腐': {'color': [180, 100, 80], 'color2': [160, 80, 60], 'brightness': [90, 150], 'categories': ['菜肴']},
    '糖醋排骨': {'color': [180, 120, 80], 'color2': [160, 100, 60], 'brightness': [100, 160], 'categories': ['菜肴', '肉类']},
    '清蒸鱼': {'color': [220, 200, 180], 'color2': [240, 220, 200], 'brightness': [200, 240], 'categories': ['菜肴', '海鲜']},
    '蛋炒饭': {'color': [240, 210, 130], 'color2': [255, 230, 150], 'brightness': [200, 250], 'categories': ['菜肴', '主食']},
    '面条汤': {'color': [230, 210, 170], 'color2': [250, 230, 190], 'brightness': [200, 240], 'categories': ['菜肴', '主食']},
    '煎饺': {'color': [240, 220, 180], 'color2': [255, 240, 200], 'brightness': [210, 250], 'categories': ['菜肴', '主食']},
    '春卷': {'color': [255, 200, 100], 'color2': [255, 220, 120], 'brightness': [200, 255], 'categories': ['菜肴']},
    '包子馅': {'color': [200, 160, 120], 'color2': [180, 140, 100], 'brightness': [140, 190], 'categories': ['菜肴']},
    
    # ===== 零食/坚果 =====
    '薯片': {'color': [255, 200, 80], 'color2': [255, 220, 100], 'brightness': [200, 255], 'categories': ['零食']},
    '巧克力': {'color': [120, 80, 60], 'color2': [100, 60, 40], 'brightness': [60, 120], 'categories': ['零食']},
    '坚果': {'color': [180, 140, 100], 'color2': [160, 120, 80], 'brightness': [130, 180], 'categories': ['坚果']},
    '花生': {'color': [200, 160, 120], 'color2': [180, 140, 100], 'brightness': [150, 200], 'categories': ['坚果']},
    '瓜子': {'color': [160, 140, 100], 'color2': [140, 120, 80], 'brightness': [120, 170], 'categories': ['坚果']},
    '杏仁': {'color': [200, 180, 140], 'color2': [180, 160, 120], 'brightness': [160, 200], 'categories': ['坚果']},
    '核桃': {'color': [160, 120, 80], 'color2': [140, 100, 60], 'brightness': [100, 150], 'categories': ['坚果']},
    '腰果': {'color': [220, 200, 160], 'color2': [200, 180, 140], 'brightness': [180, 220], 'categories': ['坚果']},
    '葡萄干': {'color': [120, 80, 60], 'color2': [100, 60, 40], 'brightness': [60, 120], 'categories': ['水果', '零食']},
    '红枣': {'color': [180, 60, 40], 'color2': [160, 40, 20], 'brightness': [80, 140], 'categories': ['水果', '零食']},
    
    # ===== 乳制品 =====
    '酸奶': {'color': [250, 245, 235], 'color2': [255, 250, 240], 'brightness': [230, 255], 'categories': ['饮品']},
    '奶酪': {'color': [255, 220, 150], 'color2': [255, 200, 120], 'brightness': [200, 255], 'categories': ['乳制品']},
    '黄油': {'color': [255, 230, 150], 'color2': [255, 240, 180], 'brightness': [220, 255], 'categories': ['乳制品']},
    '冰淇淋': {'color': [255, 240, 220], 'color2': [255, 250, 240], 'brightness': [220, 255], 'categories': ['零食']},
    
    # ===== 调味品 =====
    '酱油': {'color': [60, 40, 30], 'color2': [40, 20, 10], 'brightness': [20, 60], 'categories': ['调味品']},
    '醋': {'color': [180, 160, 140], 'color2': [200, 180, 160], 'brightness': [160, 200], 'categories': ['调味品']},
    '辣椒酱': {'color': [200, 60, 40], 'color2': [180, 40, 20], 'brightness': [80, 140], 'categories': ['调味品']},
    '番茄酱': {'color': [220, 60, 40], 'color2': [200, 40, 20], 'brightness': [80, 150], 'categories': ['调味品']},
    '沙拉酱': {'color': [255, 250, 240], 'color2': [250, 245, 235], 'brightness': [230, 255], 'categories': ['调味品']},
    '花生酱': {'color': [200, 160, 100], 'color2': [180, 140, 80], 'brightness': [140, 200], 'categories': ['调味品']},
    '果酱': {'color': [200, 100, 80], 'color2': [180, 80, 60], 'brightness': [100, 160], 'categories': ['调味品']},
    '蜂蜜': {'color': [255, 200, 80], 'color2': [255, 220, 100], 'brightness': [200, 255], 'categories': ['调味品']},
    '芝麻酱': {'color': [160, 140, 100], 'color2': [140, 120, 80], 'brightness': [120, 170], 'categories': ['调味品']},
}


def extract_image_features(image_data):
    """
    提取图片特征
    返回: 主色调RGB值
    """
    try:
        # 解码base64图片
        if ',' in image_data:
            image_data = image_data.split(',')[1]
        
        image_bytes = base64.b64decode(image_data)
        image = Image.open(io.BytesIO(image_bytes))
        
        # 转换为RGB
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # 缩小图片以加快处理
        image = image.resize((100, 100))
        
        # 转换为numpy数组
        img_array = np.array(image)
        
        # 计算平均颜色
        avg_color = np.mean(img_array, axis=(0, 1))
        
        # 计算主色调（使用K-means简化版）
        pixels = img_array.reshape(-1, 3)
        
        # 简单的颜色聚类 - 找到最常见的颜色
        pixels_list = [tuple(p) for p in pixels]
        color_counts = Counter(pixels_list)
        dominant_color = list(color_counts.most_common(1)[0][0])
        
        return {
            'avg_color': avg_color.tolist(),
            'dominant_color': dominant_color,
            'brightness': np.mean(avg_color)
        }
    except Exception as e:
        print(f"提取图片特征失败: {e}")
        return None


def color_distance(color1, color2):
    """计算两个颜色之间的欧氏距离"""
    return np.sqrt(sum((a - b) ** 2 for a, b in zip(color1, color2)))


def brightness_distance(b1, b2_range):
    """计算亮度距离，b2_range是[min, max]范围"""
    min_b, max_b = b2_range
    if min_b <= b1 <= max_b:
        return 0  # 在范围内，距离为0
    # 否则返回到最近边界的距离
    return min(abs(b1 - min_b), abs(b1 - max_b))


def recognize_food_local(image_data, top_n=5, user_id=None, db_session=None):
    """
    本地图片识别 - 改进版多特征匹配（支持机器学习）
    基于主色调、辅助色调、亮度特征匹配数据库中的食物
    
    参数:
        image_data: base64图片数据
        top_n: 返回结果数量
        user_id: 用户ID（用于查询该用户的历史确认数据）
        db_session: 数据库会话
    
    返回: 识别结果列表
    """
    features = extract_image_features(image_data)
    if not features:
        return None
    
    avg_color = features['avg_color']
    dominant_color = features['dominant_color']
    brightness = features['brightness']
    
    user_learned_matches = []  # 用户学习的食物
    builtin_matches = []       # 内置特征库的食物
    
    # 1. 首先匹配用户自己确认过的食物（如果有）
    if user_id and db_session:
        try:
            from models import FoodImageFeature
            user_features = db_session.query(FoodImageFeature).filter_by(user_id=user_id).all()
            
            for uf in user_features:
                uf_avg_color = [uf.avg_color_r, uf.avg_color_g, uf.avg_color_b]
                uf_dominant_color = [uf.dominant_color_r, uf.dominant_color_g, uf.dominant_color_b]
                
                # 计算与用户确认特征的相似度
                avg_dist = color_distance(avg_color, uf_avg_color)
                dominant_dist = color_distance(dominant_color, uf_dominant_color)
                bright_dist = abs(brightness - uf.brightness)
                
                total_score = avg_dist * 0.4 + dominant_dist * 0.3 + bright_dist * 0.3
                similarity = max(0, min(100, 100 - total_score / 3))
                
                # 用户确认过的食物给予大幅权重提升
                # 学习次数越多，置信度越高
                # 基础权重 + 学习次数加成（每次学习+10分，最多+50分）
                base_boost = 20  # 只要是用户学习过的，基础加20分
                count_boost = min(50, uf.confirmed_count * 10)  # 每次学习+10分
                raw_confidence = similarity + base_boost + count_boost
                # 允许超过100，这样学习次数多的可以排在前面
                final_confidence = round(raw_confidence, 1)
                
                user_learned_matches.append({
                    'name': uf.food_name,
                    'confidence': round(final_confidence, 1),
                    'categories': [uf.food_category] if uf.food_category else ['其他'],
                    'score': total_score,
                    'source': 'user_learned',
                    'confirmed_count': uf.confirmed_count
                })
        except Exception as e:
            print(f"查询用户特征失败: {e}")
    
    # 2. 匹配内置食物特征库
    for food_name, food_info in FOOD_FEATURES.items():
        food_color = food_info['color']
        food_color2 = food_info.get('color2', food_color)
        food_brightness = food_info.get('brightness', [100, 200])
        
        # 1. 主色调匹配（平均颜色 vs 食物主色）
        avg_to_main = color_distance(avg_color, food_color)
        
        # 2. 辅助色调匹配（平均颜色 vs 食物辅助色）
        avg_to_second = color_distance(avg_color, food_color2)
        
        # 3. 主导颜色匹配（图片主色 vs 食物主色）
        dominant_to_main = color_distance(dominant_color, food_color)
        
        # 4. 主导颜色匹配（图片主色 vs 食物辅助色）
        dominant_to_second = color_distance(dominant_color, food_color2)
        
        # 5. 亮度匹配
        bright_dist = brightness_distance(brightness, food_brightness)
        
        # 综合评分（越小越好）
        best_avg_match = min(avg_to_main, avg_to_second)
        best_dominant_match = min(dominant_to_main, dominant_to_second)
        
        total_score = (
            best_avg_match * 0.35 +
            best_dominant_match * 0.25 +
            bright_dist * 0.15
        )
        
        # 转换为相似度 (0-100)
        similarity = max(0, min(100, 100 - total_score / 2.5))
        
        # 内置特征的置信度打折，让用户学习的食物更容易排在前面
        similarity = similarity * 0.7  # 内置特征打7折
        
        # 根据类别给予额外加分
        category_bonus = 0
        if '主食' in food_info['categories']:
            category_bonus = 2
        
        final_confidence = min(100, similarity + category_bonus)
        
        builtin_matches.append({
            'name': food_name,
            'confidence': round(final_confidence, 1),
            'categories': food_info['categories'],
            'score': total_score,
            'source': 'builtin'
        })
    
    # 分别排序
    # 用户学习的按学习次数和置信度双重排序
    user_learned_matches.sort(key=lambda x: (x['confirmed_count'], x['confidence']), reverse=True)
    builtin_matches.sort(key=lambda x: x['confidence'], reverse=True)
    
    # 合并结果：用户学习的优先排在前面
    # 获取用户学习过的食物名称
    learned_names = {m['name'] for m in user_learned_matches}
    
    # 过滤掉内置特征中已学习的食物（避免重复）
    filtered_builtin = [m for m in builtin_matches if m['name'] not in learned_names]
    
    # 合并：用户学习的 + 内置的
    final_matches = user_learned_matches + filtered_builtin
    
    # 返回前N个结果
    return final_matches[:top_n]


def save_food_image_feature(image_data, food_name, food_category, user_id, db_session):
    """
    保存用户确认的食物图片特征到数据库
    
    参数:
        image_data: base64图片数据
        food_name: 食物名称
        food_category: 食物类别
        user_id: 用户ID
        db_session: 数据库会话
    
    返回: 是否保存成功
    """
    try:
        from models import FoodImageFeature
        
        features = extract_image_features(image_data)
        if not features:
            return False
        
        # 检查是否已存在相似的特征
        existing = db_session.query(FoodImageFeature).filter_by(
            user_id=user_id,
            food_name=food_name
        ).first()
        
        if existing:
            # 更新现有记录的确认次数和特征（取平均）
            existing.confirmed_count += 1
            existing.last_used = datetime.utcnow()
            
            # 更新颜色特征（移动平均）
            alpha = 0.3  # 新特征的权重
            existing.avg_color_r = existing.avg_color_r * (1 - alpha) + features['avg_color'][0] * alpha
            existing.avg_color_g = existing.avg_color_g * (1 - alpha) + features['avg_color'][1] * alpha
            existing.avg_color_b = existing.avg_color_b * (1 - alpha) + features['avg_color'][2] * alpha
            existing.dominant_color_r = existing.dominant_color_r * (1 - alpha) + features['dominant_color'][0] * alpha
            existing.dominant_color_g = existing.dominant_color_g * (1 - alpha) + features['dominant_color'][1] * alpha
            existing.dominant_color_b = existing.dominant_color_b * (1 - alpha) + features['dominant_color'][2] * alpha
            existing.brightness = existing.brightness * (1 - alpha) + features['brightness'] * alpha
        else:
            # 创建新记录
            new_feature = FoodImageFeature(
                user_id=user_id,
                food_name=food_name,
                food_category=food_category,
                avg_color_r=features['avg_color'][0],
                avg_color_g=features['avg_color'][1],
                avg_color_b=features['avg_color'][2],
                dominant_color_r=features['dominant_color'][0],
                dominant_color_g=features['dominant_color'][1],
                dominant_color_b=features['dominant_color'][2],
                brightness=features['brightness'],
                confirmed_count=1
            )
            db_session.add(new_feature)
        
        db_session.commit()
        return True
        
    except Exception as e:
        print(f"保存食物特征失败: {e}")
        import traceback
        print(traceback.format_exc())
        return False


def get_food_category_by_color(avg_color):
    """
    根据颜色判断食物类别
    """
    r, g, b = avg_color
    
    # 绿色 -> 蔬菜
    if g > r + 20 and g > b + 20:
        return '蔬菜'
    
    # 红色/棕色 -> 肉类
    if r > 150 and g < 150 and b < 150:
        return '肉类'
    
    # 黄色/米色 -> 主食
    if r > 200 and g > 180 and b < 200:
        return '主食'
    
    # 橙色 -> 水果/胡萝卜
    if r > 200 and g > 100 and b < 100:
        return '水果'
    
    # 白色/浅色 -> 主食/蛋类
    if r > 220 and g > 220 and b > 200:
        return '主食'
    
    return '其他'


# 测试代码
if __name__ == '__main__':
    # 创建一个测试图片
    test_img = Image.new('RGB', (100, 100), color=(220, 60, 40))  # 红色，像西红柿
    buffered = io.BytesIO()
    test_img.save(buffered, format="JPEG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    
    results = recognize_food_local(img_str)
    print("识别结果:")
    for r in results:
        print(f"  {r['name']}: {r['confidence']}% - {r['categories']}")
