# -*- coding: utf-8 -*-
"""
本地图片识别模块 - 智能分类版本
结合颜色+纹理特征，先分类别再匹配具体食物
"""

import base64
import io
from datetime import datetime
from PIL import Image, ImageFilter
import numpy as np
from collections import Counter

# ============================================
# 食物数据库 - 按类别组织
# ============================================

FOOD_DATABASE = {
    '蔬菜': {
        '西红柿': {'color': [220, 60, 40], 'brightness': [80, 150], 'texture': 'smooth'},
        '胡萝卜': {'color': [240, 140, 30], 'brightness': [150, 220], 'texture': 'smooth'},
        '黄瓜': {'color': [100, 160, 60], 'brightness': [100, 160], 'texture': 'bumpy'},
        '白菜': {'color': [240, 250, 230], 'brightness': [200, 255], 'texture': 'leafy'},
        '土豆': {'color': [230, 210, 150], 'brightness': [160, 220], 'texture': 'smooth'},
        '青菜': {'color': [60, 140, 50], 'brightness': [60, 120], 'texture': 'leafy'},
        '菠菜': {'color': [40, 120, 40], 'brightness': [50, 100], 'texture': 'leafy'},
        '西兰花': {'color': [80, 150, 60], 'brightness': [80, 140], 'texture': 'bumpy'},
        '茄子': {'color': [100, 60, 120], 'brightness': [60, 100], 'texture': 'smooth'},
        '南瓜': {'color': [240, 160, 40], 'brightness': [160, 220], 'texture': 'smooth'},
        '玉米': {'color': [255, 220, 80], 'brightness': [180, 240], 'texture': 'bumpy'},
        '洋葱': {'color': [240, 220, 200], 'brightness': [180, 230], 'texture': 'layered'},
        '青椒': {'color': [80, 160, 60], 'brightness': [80, 140], 'texture': 'smooth'},
        '红椒': {'color': [220, 50, 40], 'brightness': [80, 150], 'texture': 'smooth'},
        '芹菜': {'color': [150, 200, 100], 'brightness': [140, 190], 'texture': 'fibrous'},
        '生菜': {'color': [140, 200, 100], 'brightness': [140, 190], 'texture': 'leafy'},
        '蘑菇': {'color': [200, 190, 180], 'brightness': [160, 200], 'texture': 'bumpy'},
        '豆腐': {'color': [250, 250, 240], 'brightness': [230, 255], 'texture': 'smooth'},
    },
    
    '肉类': {
        '猪肉': {'color': [200, 120, 120], 'brightness': [120, 180], 'texture': 'smooth'},
        '鸡肉': {'color': [230, 200, 160], 'brightness': [170, 220], 'texture': 'smooth'},
        '牛肉': {'color': [160, 80, 60], 'brightness': [80, 140], 'texture': 'fibrous'},
        '红烧肉': {'color': [140, 60, 40], 'brightness': [60, 120], 'texture': 'smooth'},
        '排骨': {'color': [180, 140, 100], 'brightness': [120, 170], 'texture': 'bony'},
        '火腿肠': {'color': [220, 160, 140], 'brightness': [150, 200], 'texture': 'smooth'},
        '香肠': {'color': [200, 100, 80], 'brightness': [100, 160], 'texture': 'smooth'},
        '培根': {'color': [180, 120, 100], 'brightness': [120, 170], 'texture': 'layered'},
        '牛排': {'color': [150, 90, 70], 'brightness': [80, 140], 'texture': 'fibrous'},
        '鸡腿': {'color': [200, 160, 120], 'brightness': [140, 190], 'texture': 'smooth'},
    },
    
    '海鲜': {
        '鱼': {'color': [200, 180, 140], 'brightness': [150, 200], 'texture': 'scaly'},
        '虾': {'color': [255, 140, 100], 'brightness': [160, 220], 'texture': 'segmented'},
        '螃蟹': {'color': [220, 100, 60], 'brightness': [120, 180], 'texture': 'hard'},
        '三文鱼': {'color': [255, 140, 120], 'brightness': [160, 220], 'texture': 'layered'},
        '鱿鱼': {'color': [240, 220, 200], 'brightness': [200, 250], 'texture': 'smooth'},
        '贝类': {'color': [220, 200, 180], 'brightness': [180, 220], 'texture': 'smooth'},
    },
    
    '水果': {
        '苹果': {'color': [220, 60, 50], 'brightness': [100, 180], 'texture': 'smooth'},
        '香蕉': {'color': [250, 230, 100], 'brightness': [200, 255], 'texture': 'smooth'},
        '橙子': {'color': [255, 140, 30], 'brightness': [160, 220], 'texture': 'bumpy'},
        '西瓜': {'color': [240, 80, 70], 'brightness': [120, 200], 'texture': 'smooth'},
        '葡萄': {'color': [120, 50, 120], 'brightness': [60, 120], 'texture': 'bumpy'},
        '草莓': {'color': [230, 60, 70], 'brightness': [100, 180], 'texture': 'bumpy'},
        '梨': {'color': [240, 230, 150], 'brightness': [200, 250], 'texture': 'smooth'},
        '桃子': {'color': [255, 180, 150], 'brightness': [180, 230], 'texture': 'fuzzy'},
        '芒果': {'color': [255, 200, 60], 'brightness': [200, 255], 'texture': 'smooth'},
        '猕猴桃': {'color': [140, 180, 60], 'brightness': [120, 170], 'texture': 'fuzzy'},
        '蓝莓': {'color': [80, 80, 160], 'brightness': [60, 100], 'texture': 'smooth'},
        '樱桃': {'color': [200, 40, 50], 'brightness': [80, 140], 'texture': 'smooth'},
    },
    
    '主食': {
        '米饭': {'color': [240, 240, 230], 'brightness': [200, 255], 'texture': 'grainy'},
        '面条': {'color': [245, 230, 180], 'brightness': [200, 255], 'texture': 'long'},
        '馒头': {'color': [250, 245, 235], 'brightness': [230, 255], 'texture': 'smooth'},
        '面包': {'color': [200, 160, 100], 'brightness': [140, 200], 'texture': 'porous'},
        '全麦面包': {'color': [160, 130, 90], 'brightness': [100, 170], 'texture': 'porous'},
        '吐司': {'color': [220, 190, 140], 'brightness': [160, 220], 'texture': 'porous'},
        '包子': {'color': [245, 240, 230], 'brightness': [220, 255], 'texture': 'smooth'},
        '饺子': {'color': [250, 250, 245], 'brightness': [230, 255], 'texture': 'smooth'},
        '粥': {'color': [240, 235, 220], 'brightness': [210, 250], 'texture': 'liquid'},
        '饼干': {'color': [210, 170, 120], 'brightness': [150, 200], 'texture': 'porous'},
        '蛋糕': {'color': [250, 220, 180], 'brightness': [180, 240], 'texture': 'porous'},
        '三明治': {'color': [230, 210, 180], 'brightness': [170, 220], 'texture': 'layered'},
        '炒饭': {'color': [230, 200, 120], 'brightness': [170, 220], 'texture': 'grainy'},
        '炒面': {'color': [220, 180, 100], 'brightness': [160, 210], 'texture': 'long'},
        '汉堡': {'color': [200, 160, 100], 'brightness': [140, 190], 'texture': 'layered'},
        '披萨': {'color': [220, 180, 120], 'brightness': [160, 210], 'texture': 'layered'},
        '寿司': {'color': [240, 240, 230], 'brightness': [220, 255], 'texture': 'grainy'},
        '意面': {'color': [240, 200, 120], 'brightness': [180, 230], 'texture': 'long'},
        '咖喱饭': {'color': [220, 180, 100], 'brightness': [160, 210], 'texture': 'grainy'},
        '蛋炒饭': {'color': [240, 210, 130], 'brightness': [200, 250], 'texture': 'grainy'},
        '面条汤': {'color': [230, 210, 170], 'brightness': [200, 240], 'texture': 'long'},
        '煎饺': {'color': [240, 220, 180], 'brightness': [210, 250], 'texture': 'smooth'},
        '春卷': {'color': [255, 200, 100], 'brightness': [200, 255], 'texture': 'crispy'},
        '薯条': {'color': [255, 200, 80], 'brightness': [200, 255], 'texture': 'long'},
    },
    
    '蛋类': {
        '鸡蛋': {'color': [250, 220, 150], 'brightness': [200, 255], 'texture': 'smooth'},
        '煎蛋': {'color': [255, 200, 80], 'brightness': [180, 240], 'texture': 'smooth'},
        '茶叶蛋': {'color': [160, 120, 80], 'brightness': [100, 150], 'texture': 'smooth'},
        '水煮蛋': {'color': [240, 230, 200], 'brightness': [210, 250], 'texture': 'smooth'},
        '炒蛋': {'color': [255, 220, 100], 'brightness': [200, 255], 'texture': 'fluffy'},
    },
    
    '饮品': {
        '牛奶': {'color': [250, 250, 245], 'brightness': [240, 255], 'texture': 'liquid'},
        '咖啡': {'color': [100, 70, 50], 'brightness': [50, 100], 'texture': 'liquid'},
        '茶': {'color': [180, 160, 100], 'brightness': [130, 180], 'texture': 'liquid'},
        '果汁': {'color': [240, 160, 40], 'brightness': [160, 220], 'texture': 'liquid'},
        '可乐': {'color': [60, 40, 30], 'brightness': [30, 70], 'texture': 'liquid'},
        '奶茶': {'color': [200, 170, 130], 'brightness': [150, 200], 'texture': 'liquid'},
        '啤酒': {'color': [240, 200, 80], 'brightness': [180, 240], 'texture': 'liquid'},
        '红酒': {'color': [140, 40, 60], 'brightness': [50, 100], 'texture': 'liquid'},
        '豆浆': {'color': [245, 240, 220], 'brightness': [220, 255], 'texture': 'liquid'},
        '酸奶': {'color': [250, 245, 235], 'brightness': [230, 255], 'texture': 'creamy'},
    },
    
    '坚果': {
        '坚果': {'color': [180, 140, 100], 'brightness': [130, 180], 'texture': 'rough'},
        '花生': {'color': [200, 160, 120], 'brightness': [150, 200], 'texture': 'rough'},
        '瓜子': {'color': [160, 140, 100], 'brightness': [120, 170], 'texture': 'smooth'},
        '杏仁': {'color': [200, 180, 140], 'brightness': [160, 200], 'texture': 'smooth'},
        '核桃': {'color': [160, 120, 80], 'brightness': [100, 150], 'texture': 'rough'},
        '腰果': {'color': [220, 200, 160], 'brightness': [180, 220], 'texture': 'smooth'},
        '薯片': {'color': [255, 200, 80], 'brightness': [200, 255], 'texture': 'crispy'},
        '巧克力': {'color': [120, 80, 60], 'brightness': [60, 120], 'texture': 'smooth'},
    },
}

# 类别关键词映射
CATEGORY_KEYWORDS = {
    '蔬菜': ['菜', '瓜', '茄', '菇', '椒', '笋', '豆', '卜', '葱', '蒜', '姜', '芹', '菠', '苋'],
    '肉类': ['肉', '鸡', '猪', '牛', '羊', '排', '肠', '腿', '翅', '胸'],
    '海鲜': ['鱼', '虾', '蟹', '贝', '鱿', '鲍', '龙', '带', '鲈', '鲤'],
    '水果': ['果', '瓜', '莓', '桃', '梨', '苹', '橙', '蕉', '柿', '柚', '柠', '芒', '荔'],
    '主食': ['饭', '面', '包', '馒', '饺', '粥', '饼', '条', '粉', '糕', '团', '包', '卷'],
    '蛋类': ['蛋'],
    '饮品': ['奶', '茶', '咖', '酒', '汁', '浆', '饮', '汤', '水'],
    '坚果': ['果', '仁', '桃', '杏', '瓜'],
}


def extract_image_features(image_data):
    """提取图片特征（颜色+纹理）"""
    try:
        if ',' in image_data:
            image_data = image_data.split(',')[1]
        
        image_bytes = base64.b64decode(image_data)
        image = Image.open(io.BytesIO(image_bytes))
        
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # 缩小图片以加快处理
        image = image.resize((150, 150))
        img_array = np.array(image)
        
        # 1. 颜色特征
        avg_color = np.mean(img_array, axis=(0, 1))
        
        pixels = img_array.reshape(-1, 3)
        pixels_list = [tuple(p) for p in pixels]
        color_counts = Counter(pixels_list)
        dominant_color = list(color_counts.most_common(1)[0][0])
        
        # 颜色标准差（反映颜色丰富度）
        std_color = np.std(img_array, axis=(0, 1))
        
        # 2. 纹理特征 - 使用边缘检测
        gray = np.mean(img_array, axis=2)
        
        # 计算梯度（边缘强度）
        grad_x = np.abs(np.diff(gray, axis=1, append=gray[:, -1:]))
        grad_y = np.abs(np.diff(gray, axis=0, append=gray[-1:, :]))
        edge_strength = np.mean(grad_x + grad_y)
        
        # 纹理复杂度（局部方差）- 使用纯numpy实现
        # 计算5x5局部窗口的方差
        padded = np.pad(gray, 2, mode='edge')
        local_vars = []
        for i in range(2, padded.shape[0] - 2):
            for j in range(2, padded.shape[1] - 2):
                window = padded[i-2:i+3, j-2:j+3]
                local_vars.append(np.var(window))
        texture_complexity = np.mean(local_vars)
        
        return {
            'avg_color': avg_color.tolist(),
            'dominant_color': dominant_color,
            'std_color': std_color.tolist(),
            'brightness': np.mean(avg_color),
            'edge_strength': edge_strength,
            'texture_complexity': texture_complexity,
            'color_variance': np.mean(std_color)
        }
    except Exception as e:
        print(f"提取图片特征失败: {e}")
        return None


def detect_texture_type(features):
    """
    根据特征判断纹理类型
    """
    edge = features['edge_strength']
    complexity = features['texture_complexity']
    variance = features['color_variance']
    brightness = features['brightness']
    
    # 鱼鳞特征：中等边缘强度 + 中等复杂度
    # 鱼鳞有规律的纹理，复杂度不会太高也不会太低
    if 8 < edge < 50 and 30 < complexity < 300:
        # 检查是否有规律的重复纹理
        if 50 < complexity < 200:
            return 'scaly'
        return 'textured'
    
    # 条状纹理（面条、薯条）- 高边缘+特定复杂度
    if edge > 20 and 60 < complexity < 150:
        return 'long'
    
    # 粗糙纹理（坚果）
    if complexity > 120 and edge > 15 and variance > 30:
        return 'rough'
    
    # 颗粒状（米饭等）- 高复杂度+中高边缘
    if complexity > 100 and edge > 10:
        return 'grainy'
    
    # 多孔状（面包等）
    if 60 < complexity < 150 and variance > 25:
        return 'porous'
    
    # 叶状（蔬菜）- 高颜色变化+中等边缘
    if variance > 35 and 5 < edge < 25:
        return 'leafy'
    
    # 蓬松状（炒蛋）
    if complexity > 80 and edge < 15 and brightness > 200:
        return 'fluffy'
    
    # 分层状（三明治、培根）
    if 40 < complexity < 100 and 10 < edge < 30:
        return 'layered'
    
    # 酥脆状（薯片、春卷）
    if complexity > 100 and edge > 20 and brightness > 180:
        return 'crispy'
    
    # 液体状（粥、汤、饮品）
    if edge < 10 and complexity < 50 and brightness > 150:
        return 'liquid'
    
    # 奶油状（酸奶）
    if edge < 12 and complexity < 60 and brightness > 220:
        return 'creamy'
    
    # 光滑表面（默认）
    if edge < 15 and complexity < 80:
        return 'smooth'
    
    return 'textured'  # 默认为有纹理


def color_distance(color1, color2):
    """计算颜色欧氏距离"""
    return np.sqrt(sum((a - b) ** 2 for a, b in zip(color1, color2)))


def smart_category_detection(features, texture_type):
    """
    智能类别检测 - 结合颜色和纹理
    为每个类别定义精准的颜色特征
    """
    avg_color = features['avg_color']
    brightness = features['brightness']
    variance = features['color_variance']
    
    scores = {}
    
    r, g, b = avg_color
    
    # ========== 1. 海鲜检测（最优先）==========
    # 鱼的颜色特征：灰白/灰褐色，R和G接近，R略大于G，B较低
    is_fish_color = (120 <= r <= 220 and 100 <= g <= 200 and 80 <= b <= 160 and 
                     abs(r - g) < 40 and r > g > b)
    # 虾蟹的颜色：偏红/橙色
    is_shrimp_color = (r > 180 and g > 80 and g < 160 and b < 100 and r > g)
    
    if is_fish_color or is_shrimp_color:
        scores['海鲜'] = scores.get('海鲜', 0) + 85
        scores['肉类'] = scores.get('肉类', 0) + 25
    
    # 鱼鳞纹理是海鲜的强特征
    if texture_type == 'scaly' or texture_type == 'textured':
        scores['海鲜'] = scores.get('海鲜', 0) + 75
    
    # ========== 2. 蔬菜检测 ==========
    # 深绿色蔬菜：G很高，R和B较低
    is_dark_green = (g > 80 and g > r + 30 and g > b + 30 and r < 150)
    # 浅绿色蔬菜：G高，整体亮度高
    is_light_green = (g > 150 and g > r + 20 and g > b + 10 and brightness > 180)
    # 白色蔬菜（白菜、萝卜）：高亮度，RGB接近
    is_white_veg = (r > 200 and g > 200 and b > 180 and abs(int(r) - int(g)) < 30)
    
    if is_dark_green or is_light_green:
        scores['蔬菜'] = scores.get('蔬菜', 0) + 85
        scores['水果'] = scores.get('水果', 0) + 15
    elif is_white_veg and brightness > 200:
        scores['蔬菜'] = scores.get('蔬菜', 0) + 70
        scores['主食'] = scores.get('主食', 0) + 30
    
    # 叶状纹理是蔬菜的强特征
    if texture_type == 'leafy':
        scores['蔬菜'] = scores.get('蔬菜', 0) + 70
    
    # ========== 3. 肉类检测 ==========
    # 生肉：偏粉红色/红色，R高，G和B中等
    is_raw_meat = (r > 150 and 80 < g < 160 and 60 < b < 120 and r > g > b)
    # 熟肉/红烧肉：深红色/棕色，整体偏暗
    is_cooked_meat = (100 < r < 180 and 50 < g < 120 and 30 < b < 100 and r > g > b)
    # 鸡肉：浅粉色/米色
    is_chicken = (200 < r < 240 and 160 < g < 210 and 100 < b < 170)
    
    if is_raw_meat or is_cooked_meat:
        scores['肉类'] = scores.get('肉类', 0) + 85
        scores['海鲜'] = scores.get('海鲜', 0) + 20
    elif is_chicken:
        scores['肉类'] = scores.get('肉类', 0) + 80
    
    # ========== 4. 水果检测 ==========
    # 红色水果：苹果、草莓、西瓜
    is_red_fruit = (r > 180 and g < 120 and b < 100 and r - g > 60)
    # 橙色/黄色水果：橙子、香蕉、芒果
    is_orange_fruit = (r > 200 and 100 < g < 220 and b < 80 and r > g > b)
    # 黄色水果：香蕉、梨
    is_yellow_fruit = (r > 220 and g > 200 and b < 150 and abs(int(r) - int(g)) < 50)
    # 紫色水果：葡萄
    is_purple_fruit = (r > 60 and r < 150 and g > 40 and g < 120 and b > 80 and b > g)
    
    if is_red_fruit:
        scores['水果'] = scores.get('水果', 0) + 85
    elif is_orange_fruit:
        scores['水果'] = scores.get('水果', 0) + 80
    elif is_yellow_fruit:
        scores['水果'] = scores.get('水果', 0) + 75
        scores['主食'] = scores.get('主食', 0) + 20
    elif is_purple_fruit:
        scores['水果'] = scores.get('水果', 0) + 80
    
    # ========== 5. 主食检测 ==========
    # 米饭/馒头：白色/米白色，颗粒状或光滑
    is_rice = (r > 220 and g > 215 and b > 190 and abs(int(r) - int(g)) < 20 and 
               texture_type in ['grainy', 'smooth'])
    # 面条/面包：黄色/米色，多孔状或条状
    is_noodle = (200 < r < 250 and 160 < g < 230 and 80 < b < 180 and 
                 texture_type in ['porous', 'long'])
    # 煎饼/饼干：金黄色，较暗
    is_pancake = (180 < r < 240 and 140 < g < 200 and 60 < b < 140)
    
    if is_rice:
        scores['主食'] = scores.get('主食', 0) + 85
        scores['蛋类'] = scores.get('蛋类', 0) + 20
    elif is_noodle:
        scores['主食'] = scores.get('主食', 0) + 80
    elif is_pancake:
        scores['主食'] = scores.get('主食', 0) + 75
    
    # 颗粒状纹理是主食的强特征（米饭）
    if texture_type == 'grainy':
        scores['主食'] = scores.get('主食', 0) + 30
    elif texture_type == 'porous':
        scores['主食'] = scores.get('主食', 0) + 25
    elif texture_type == 'long':
        scores['主食'] = scores.get('主食', 0) + 20
    
    # ========== 6. 蛋类检测 ==========
    # 鸡蛋：黄色/金黄色，光滑
    is_egg = (230 < r < 255 and 180 < g < 240 and 60 < b < 180 and 
              texture_type == 'smooth' and brightness > 180)
    
    if is_egg:
        scores['蛋类'] = scores.get('蛋类', 0) + 85
        scores['主食'] = scores.get('主食', 0) + 20
    
    # ========== 7. 饮品检测 ==========
    # 深色饮品：咖啡、可乐、茶
    is_dark_drink = (brightness < 120 and r < 150 and g < 130 and b < 110)
    # 浅色饮品：牛奶、豆浆
    is_light_drink = (r > 230 and g > 225 and b > 210 and brightness > 220)
    # 黄色饮品：果汁、啤酒
    is_yellow_drink = (r > 200 and g > 160 and b < 100 and brightness > 150)
    
    if is_dark_drink:
        scores['饮品'] = scores.get('饮品', 0) + 80
    elif is_light_drink:
        scores['饮品'] = scores.get('饮品', 0) + 75
        scores['主食'] = scores.get('主食', 0) + 15
    elif is_yellow_drink:
        scores['饮品'] = scores.get('饮品', 0) + 70
        scores['水果'] = scores.get('水果', 0) + 20
    
    # 液体纹理
    if texture_type == 'liquid':
        scores['饮品'] = scores.get('饮品', 0) + 25
        scores['主食'] = scores.get('主食', 0) + 10
    
    # ========== 8. 坚果检测 ==========
    # 棕色系：各种坚果
    is_nut = (120 < r < 200 and 80 < g < 160 and 40 < b < 120 and 
              r > g > b and texture_type in ['rough', 'smooth'])
    
    if is_nut:
        scores['坚果'] = scores.get('坚果', 0) + 80
        scores['肉类'] = scores.get('肉类', 0) + 20
    
    # 确保所有类别都有基础分数（至少10分）
    for cat in FOOD_DATABASE.keys():
        if cat not in scores:
            scores[cat] = 10
    
    # 排序返回
    return sorted(scores.items(), key=lambda x: x[1], reverse=True)


def match_food_in_category(features, category, top_n=3):
    """
    在指定类别内匹配具体食物
    """
    if category not in FOOD_DATABASE:
        return []
    
    avg_color = features['avg_color']
    brightness = features['brightness']
    texture_type = detect_texture_type(features)
    
    matches = []
    foods = FOOD_DATABASE[category]
    
    for food_name, food_info in foods.items():
        food_color = food_info['color']
        food_brightness = food_info.get('brightness', [100, 200])
        food_texture = food_info.get('texture', 'unknown')
        
        # 颜色距离
        color_dist = color_distance(avg_color, food_color)
        color_score = max(0, 100 - color_dist / 2)
        
        # 亮度匹配
        bright_min, bright_max = food_brightness
        if bright_min <= brightness <= bright_max:
            bright_score = 100
        else:
            bright_score = max(0, 100 - min(abs(brightness - bright_min), 
                                           abs(brightness - bright_max)))
        
        # 纹理匹配加分
        texture_bonus = 0
        if texture_type != 'unknown' and food_texture == texture_type:
            texture_bonus = 15
        
        # 综合分数
        total_score = color_score * 0.5 + bright_score * 0.3 + texture_bonus
        
        matches.append({
            'name': food_name,
            'confidence': round(min(90, total_score), 1),
            'category': category,
            'color_score': round(color_score, 1),
            'texture_match': food_texture == texture_type
        })
    
    matches.sort(key=lambda x: x['confidence'], reverse=True)
    return matches[:top_n]


def recognize_food_local(image_data, top_n=5, user_id=None, db_session=None):
    """
    本地图片识别 - 智能版本
    """
    features = extract_image_features(image_data)
    if not features:
        return None
    
    # 检测纹理类型
    texture_type = detect_texture_type(features)
    
    # 智能类别检测
    category_scores = smart_category_detection(features, texture_type)
    
    all_matches = []
    
    # 在前3个类别中匹配食物
    for category, cat_score in category_scores[:3]:
        foods = match_food_in_category(features, category, top_n=3)
        
        for food in foods:
            # 结合类别置信度
            combined = food['confidence'] * 0.7 + cat_score * 0.3
            food['confidence'] = round(min(85, combined), 1)
            food['source'] = 'smart_match'
            all_matches.append(food)
    
    # 匹配用户学习过的食物
    # 获取当前图片最可能的类别（第一个类别的分数）
    top_category = category_scores[0][0] if category_scores else None
    top_cat_score = category_scores[0][1] if category_scores else 0
    
    if user_id and db_session:
        try:
            from models import FoodImageFeature
            user_features = db_session.query(FoodImageFeature).filter_by(user_id=user_id).all()
            
            for uf in user_features:
                uf_avg_color = [uf.avg_color_r, uf.avg_color_g, uf.avg_color_b]
                
                avg_dist = color_distance(features['avg_color'], uf_avg_color)
                bright_dist = abs(features['brightness'] - uf.brightness)
                
                similarity = max(0, 100 - (avg_dist * 0.6 + bright_dist * 0.4) / 2)
                
                # 如果当前图片明显属于某个类别（分数>60），且用户学习的食物不属于该类别
                # 则大幅降低该学习记录的权重
                category_penalty = 0
                if top_cat_score > 60 and uf.food_category != top_category:
                    # 不同类别的学习记录，置信度打5折
                    category_penalty = similarity * 0.5
                
                # 用户学习的给予小幅加成（最多10分）
                count_boost = min(10, uf.confirmed_count * 2)
                final_confidence = min(80, similarity - category_penalty + count_boost)
                
                # 只有当置信度足够高时才加入结果（至少40分）
                if final_confidence >= 40:
                    existing = next((m for m in all_matches if m['name'] == uf.food_name), None)
                    if existing:
                        if final_confidence > existing['confidence']:
                            existing['confidence'] = round(final_confidence, 1)
                            existing['source'] = 'user_learned'
                            existing['confirmed_count'] = uf.confirmed_count
                    else:
                        all_matches.append({
                            'name': uf.food_name,
                            'confidence': round(final_confidence, 1),
                            'category': uf.food_category or '其他',
                            'source': 'user_learned',
                            'confirmed_count': uf.confirmed_count
                        })
        except Exception as e:
            print(f"查询用户特征失败: {e}")
    
    # 排序：只按置信度排序，不再强制用户学习的排前面
    # 用户学习的优势已经通过置信度加成体现了
    all_matches.sort(key=lambda x: x['confidence'], reverse=True)
    
    # 去重
    seen = set()
    unique_matches = []
    for m in all_matches:
        if m['name'] not in seen:
            seen.add(m['name'])
            unique_matches.append(m)
    
    return unique_matches[:top_n]


def save_food_image_feature(image_data, food_name, food_category, user_id, db_session):
    """保存用户确认的食物图片特征"""
    try:
        from models import FoodImageFeature
        
        features = extract_image_features(image_data)
        if not features:
            return False
        
        existing = db_session.query(FoodImageFeature).filter_by(
            user_id=user_id,
            food_name=food_name
        ).first()
        
        if existing:
            existing.confirmed_count += 1
            existing.last_used = datetime.utcnow()
            
            alpha = 0.3
            existing.avg_color_r = existing.avg_color_r * (1 - alpha) + features['avg_color'][0] * alpha
            existing.avg_color_g = existing.avg_color_g * (1 - alpha) + features['avg_color'][1] * alpha
            existing.avg_color_b = existing.avg_color_b * (1 - alpha) + features['avg_color'][2] * alpha
            existing.dominant_color_r = existing.dominant_color_r * (1 - alpha) + features['dominant_color'][0] * alpha
            existing.dominant_color_g = existing.dominant_color_g * (1 - alpha) + features['dominant_color'][1] * alpha
            existing.dominant_color_b = existing.dominant_color_b * (1 - alpha) + features['dominant_color'][2] * alpha
            existing.brightness = existing.brightness * (1 - alpha) + features['brightness'] * alpha
        else:
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


# 测试代码
if __name__ == '__main__':
    # 创建一个模拟鱼的图片（灰褐色）
    test_img = Image.new('RGB', (150, 150), color=(180, 170, 140))
    buffered = io.BytesIO()
    test_img.save(buffered, format="JPEG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    
    results = recognize_food_local(img_str)
    print("识别结果:")
    for r in results:
        print(f"  {r['name']}: {r['confidence']}% - {r.get('category', '未知')}")
