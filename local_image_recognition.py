# -*- coding: utf-8 -*-
"""
智能食物图片识别系统 - 类别库对比版
核心逻辑：
1. 识别时优先对比用户已学习的类别库
2. 支持手动纠正并学习
3. 学习2-3次后自动归档到类别库
4. 同类别食物特征对比提高准确率
"""

import base64
import io
import json
import hashlib
from datetime import datetime
from PIL import Image
import numpy as np

# ============================================
# 预定义食物数据库 - 基础参考数据
# ============================================

FOOD_DATABASE = {
    '蔬菜': {
        '西红柿': {'hsv_hint': 'red', 'shape': 'round', 'typical_h': [0, 15, 345, 360]},
        '胡萝卜': {'hsv_hint': 'orange', 'shape': 'long', 'typical_h': [15, 45]},
        '黄瓜': {'hsv_hint': 'green', 'shape': 'long', 'typical_h': [75, 165]},
        '白菜': {'hsv_hint': 'white', 'shape': 'leaf', 'typical_h': None},
        '土豆': {'hsv_hint': 'yellow', 'shape': 'round', 'typical_h': [45, 75]},
        '青菜': {'hsv_hint': 'green', 'shape': 'leaf', 'typical_h': [75, 165]},
        '菠菜': {'hsv_hint': 'green', 'shape': 'leaf', 'typical_h': [75, 165]},
        '西兰花': {'hsv_hint': 'green', 'shape': 'bumpy', 'typical_h': [75, 165]},
        '茄子': {'hsv_hint': 'purple', 'shape': 'long', 'typical_h': [255, 285]},
        '南瓜': {'hsv_hint': 'orange', 'shape': 'round', 'typical_h': [15, 45]},
        '玉米': {'hsv_hint': 'yellow', 'shape': 'bumpy', 'typical_h': [45, 75]},
        '洋葱': {'hsv_hint': 'white', 'shape': 'round', 'typical_h': None},
        '青椒': {'hsv_hint': 'green', 'shape': 'round', 'typical_h': [75, 165]},
        '红椒': {'hsv_hint': 'red', 'shape': 'round', 'typical_h': [0, 15, 345, 360]},
        '芹菜': {'hsv_hint': 'green', 'shape': 'long', 'typical_h': [75, 165]},
        '生菜': {'hsv_hint': 'green', 'shape': 'leaf', 'typical_h': [75, 165]},
        '蘑菇': {'hsv_hint': 'white', 'shape': 'round', 'typical_h': None},
        '豆腐': {'hsv_hint': 'white', 'shape': 'square', 'typical_h': None},
        '蚕豆': {'hsv_hint': 'green', 'shape': 'oval', 'typical_h': [75, 165]},
    },
    
    '肉类': {
        '猪肉': {'hsv_hint': 'pink', 'shape': 'slice', 'typical_h': [345, 15]},
        '鸡肉': {'hsv_hint': 'beige', 'shape': 'slice', 'typical_h': [15, 45]},
        '牛肉': {'hsv_hint': 'red', 'shape': 'slice', 'typical_h': [0, 15, 345, 360]},
        '红烧肉': {'hsv_hint': 'brown', 'shape': 'chunk', 'typical_h': [15, 45]},
        '排骨': {'hsv_hint': 'beige', 'shape': 'bone', 'typical_h': [15, 45]},
        '火腿肠': {'hsv_hint': 'pink', 'shape': 'cylinder', 'typical_h': [345, 15]},
        '香肠': {'hsv_hint': 'red', 'shape': 'cylinder', 'typical_h': [0, 15, 345, 360]},
        '培根': {'hsv_hint': 'pink', 'shape': 'strip', 'typical_h': [345, 15]},
        '牛排': {'hsv_hint': 'red', 'shape': 'slice', 'typical_h': [0, 15, 345, 360]},
        '鸡腿': {'hsv_hint': 'beige', 'shape': 'drumstick', 'typical_h': [15, 45]},
        '鸡胸肉': {'hsv_hint': 'beige', 'shape': 'slice', 'typical_h': [15, 45]},
    },
    
    '海鲜': {
        '鱼': {'hsv_hint': 'gray', 'shape': 'fish', 'typical_h': None},
        '三文鱼': {'hsv_hint': 'orange', 'shape': 'slice', 'typical_h': [15, 45]},
        '虾': {'hsv_hint': 'pink', 'shape': 'curve', 'typical_h': [345, 15]},
        '螃蟹': {'hsv_hint': 'red', 'shape': 'round', 'typical_h': [0, 15, 345, 360]},
        '鱿鱼': {'hsv_hint': 'white', 'shape': 'strip', 'typical_h': None},
        '贝类': {'hsv_hint': 'beige', 'shape': 'round', 'typical_h': [15, 45]},
        '金枪鱼': {'hsv_hint': 'red', 'shape': 'slice', 'typical_h': [0, 15, 345, 360]},
        '带鱼': {'hsv_hint': 'gray', 'shape': 'long', 'typical_h': None},
        '黄花鱼': {'hsv_hint': 'yellow', 'shape': 'fish', 'typical_h': [45, 75]},
    },
    
    '水果': {
        '苹果': {'hsv_hint': 'red', 'shape': 'round', 'typical_h': [0, 15, 345, 360]},
        '香蕉': {'hsv_hint': 'yellow', 'shape': 'curve', 'typical_h': [45, 75]},
        '橙子': {'hsv_hint': 'orange', 'shape': 'round', 'typical_h': [15, 45]},
        '西瓜': {'hsv_hint': 'red', 'shape': 'slice', 'typical_h': [0, 15, 345, 360]},
        '葡萄': {'hsv_hint': 'purple', 'shape': 'round', 'typical_h': [255, 285]},
        '草莓': {'hsv_hint': 'red', 'shape': 'cone', 'typical_h': [0, 15, 345, 360]},
        '梨': {'hsv_hint': 'yellow', 'shape': 'pear', 'typical_h': [45, 75]},
        '桃子': {'hsv_hint': 'pink', 'shape': 'round', 'typical_h': [285, 345]},
        '芒果': {'hsv_hint': 'yellow', 'shape': 'oval', 'typical_h': [45, 75]},
        '猕猴桃': {'hsv_hint': 'green', 'shape': 'oval', 'typical_h': [75, 165]},
        '蓝莓': {'hsv_hint': 'blue', 'shape': 'round', 'typical_h': [195, 255]},
        '樱桃': {'hsv_hint': 'red', 'shape': 'round', 'typical_h': [0, 15, 345, 360]},
    },
    
    '主食': {
        '米饭': {'hsv_hint': 'white', 'shape': 'grain', 'typical_h': None},
        '面条': {'hsv_hint': 'yellow', 'shape': 'long', 'typical_h': [45, 75]},
        '馒头': {'hsv_hint': 'white', 'shape': 'round', 'typical_h': None},
        '面包': {'hsv_hint': 'brown', 'shape': 'square', 'typical_h': [15, 45]},
        '全麦面包': {'hsv_hint': 'brown', 'shape': 'square', 'typical_h': [15, 45]},
        '吐司': {'hsv_hint': 'yellow', 'shape': 'square', 'typical_h': [45, 75]},
        '包子': {'hsv_hint': 'white', 'shape': 'round', 'typical_h': None},
        '饺子': {'hsv_hint': 'white', 'shape': 'crescent', 'typical_h': None},
        '粥': {'hsv_hint': 'white', 'shape': 'liquid', 'typical_h': None},
        '饼干': {'hsv_hint': 'brown', 'shape': 'round', 'typical_h': [15, 45]},
        '蛋糕': {'hsv_hint': 'yellow', 'shape': 'round', 'typical_h': [45, 75]},
        '三明治': {'hsv_hint': 'yellow', 'shape': 'square', 'typical_h': [45, 75]},
        '炒饭': {'hsv_hint': 'yellow', 'shape': 'grain', 'typical_h': [45, 75]},
        '炒面': {'hsv_hint': 'brown', 'shape': 'long', 'typical_h': [15, 45]},
        '汉堡': {'hsv_hint': 'brown', 'shape': 'round', 'typical_h': [15, 45]},
        '披萨': {'hsv_hint': 'yellow', 'shape': 'round', 'typical_h': [45, 75]},
        '寿司': {'hsv_hint': 'white', 'shape': 'roll', 'typical_h': None},
        '意面': {'hsv_hint': 'yellow', 'shape': 'long', 'typical_h': [45, 75]},
        '咖喱饭': {'hsv_hint': 'yellow', 'shape': 'grain', 'typical_h': [45, 75]},
        '蛋炒饭': {'hsv_hint': 'yellow', 'shape': 'grain', 'typical_h': [45, 75]},
        '面条汤': {'hsv_hint': 'yellow', 'shape': 'long', 'typical_h': [45, 75]},
        '煎饺': {'hsv_hint': 'yellow', 'shape': 'crescent', 'typical_h': [45, 75]},
        '春卷': {'hsv_hint': 'yellow', 'shape': 'cylinder', 'typical_h': [45, 75]},
        '薯条': {'hsv_hint': 'yellow', 'shape': 'long', 'typical_h': [45, 75]},
    },
    
    '蛋类': {
        '鸡蛋': {'hsv_hint': 'beige', 'shape': 'oval', 'typical_h': [15, 45]},
        '煎蛋': {'hsv_hint': 'yellow', 'shape': 'round', 'typical_h': [45, 75]},
        '茶叶蛋': {'hsv_hint': 'brown', 'shape': 'oval', 'typical_h': [15, 45]},
        '水煮蛋': {'hsv_hint': 'white', 'shape': 'oval', 'typical_h': None},
        '炒蛋': {'hsv_hint': 'yellow', 'shape': 'fluffy', 'typical_h': [45, 75]},
        '皮蛋': {'hsv_hint': 'black', 'shape': 'oval', 'typical_h': None},
        '咸鸭蛋': {'hsv_hint': 'beige', 'shape': 'oval', 'typical_h': [15, 45]},
    },
    
    '豆类': {
        '黄豆': {'hsv_hint': 'yellow', 'shape': 'round', 'typical_h': [45, 75]},
        '绿豆': {'hsv_hint': 'green', 'shape': 'round', 'typical_h': [75, 165]},
        '红豆': {'hsv_hint': 'red', 'shape': 'round', 'typical_h': [0, 15, 345, 360]},
        '黑豆': {'hsv_hint': 'black', 'shape': 'round', 'typical_h': None},
        '豆腐': {'hsv_hint': 'white', 'shape': 'square', 'typical_h': None},
        '豆浆': {'hsv_hint': 'white', 'shape': 'liquid', 'typical_h': None},
        '腐竹': {'hsv_hint': 'yellow', 'shape': 'strip', 'typical_h': [45, 75]},
        '豆腐干': {'hsv_hint': 'beige', 'shape': 'square', 'typical_h': [15, 45]},
    },
    
    '饮品': {
        '牛奶': {'hsv_hint': 'white', 'shape': 'liquid', 'typical_h': None},
        '咖啡': {'hsv_hint': 'brown', 'shape': 'liquid', 'typical_h': [15, 45]},
        '茶': {'hsv_hint': 'brown', 'shape': 'liquid', 'typical_h': [15, 75]},
        '果汁': {'hsv_hint': 'orange', 'shape': 'liquid', 'typical_h': [15, 75]},
        '可乐': {'hsv_hint': 'black', 'shape': 'liquid', 'typical_h': None},
        '奶茶': {'hsv_hint': 'brown', 'shape': 'liquid', 'typical_h': [15, 45]},
        '啤酒': {'hsv_hint': 'yellow', 'shape': 'liquid', 'typical_h': [45, 75]},
        '红酒': {'hsv_hint': 'red', 'shape': 'liquid', 'typical_h': [0, 15, 345, 360]},
        '豆浆': {'hsv_hint': 'white', 'shape': 'liquid', 'typical_h': None},
        '酸奶': {'hsv_hint': 'white', 'shape': 'creamy', 'typical_h': None},
    },
    
    '坚果': {
        '坚果': {'hsv_hint': 'brown', 'shape': 'round', 'typical_h': [15, 45]},
        '花生': {'hsv_hint': 'brown', 'shape': 'oval', 'typical_h': [15, 45]},
        '瓜子': {'hsv_hint': 'brown', 'shape': 'strip', 'typical_h': [15, 45]},
        '杏仁': {'hsv_hint': 'beige', 'shape': 'oval', 'typical_h': [15, 45]},
        '核桃': {'hsv_hint': 'brown', 'shape': 'brain', 'typical_h': [15, 45]},
        '腰果': {'hsv_hint': 'beige', 'shape': 'curve', 'typical_h': [15, 45]},
        '薯片': {'hsv_hint': 'yellow', 'shape': 'round', 'typical_h': [45, 75]},
        '巧克力': {'hsv_hint': 'brown', 'shape': 'square', 'typical_h': [15, 45]},
    },
}

# 类别库名称映射
CATEGORY_NAMES = {
    '蔬菜': 'vegetables',
    '肉类': 'meat',
    '海鲜': 'seafood',
    '水果': 'fruit',
    '主食': 'staple',
    '蛋类': 'egg',
    '豆类': 'beans',
    '饮品': 'beverage',
    '坚果': 'nuts',
    '其他': 'other',
}


def rgb_to_hsv(r, g, b):
    """RGB转HSV颜色空间"""
    r, g, b = r/255.0, g/255.0, b/255.0
    mx = max(r, g, b)
    mn = min(r, g, b)
    df = mx-mn
    if mx == mn:
        h = 0
    elif mx == r:
        h = (60 * ((g-b)/df) + 360) % 360
    elif mx == g:
        h = (60 * ((b-r)/df) + 120) % 360
    else:
        h = (60 * ((r-g)/df) + 240) % 360
    if mx == 0:
        s = 0
    else:
        s = df/mx
    v = mx
    return (h, s, v)


def get_hsv_hint(hsv):
    """根据HSV值获取颜色提示"""
    h, s, v = hsv
    
    # 低饱和度认为是白色/灰色/黑色
    if s < 0.15:
        if v > 0.8:
            return 'white'
        elif v < 0.3:
            return 'black'
        else:
            return 'gray'
    
    # 根据色相判断
    if 0 <= h < 15 or 345 <= h < 360:
        return 'red'
    elif 15 <= h < 45:
        if s > 0.6:
            return 'orange'
        else:
            return 'beige'
    elif 45 <= h < 75:
        return 'yellow'
    elif 75 <= h < 165:
        return 'green'
    elif 165 <= h < 195:
        return 'cyan'
    elif 195 <= h < 255:
        return 'blue'
    elif 255 <= h < 285:
        return 'purple'
    elif 285 <= h < 345:
        return 'pink'
    
    return 'unknown'


def extract_image_features(image_data):
    """提取图片特征"""
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
        
        # 1. 基础颜色特征
        avg_color = np.mean(img_array, axis=(0, 1))
        
        # 2. HSV颜色特征
        hsv_color = rgb_to_hsv(avg_color[0], avg_color[1], avg_color[2])
        
        # 3. 颜色直方图（分区域统计）
        h, w = img_array.shape[:2]
        region_colors = []
        for i in range(3):
            for j in range(3):
                region = img_array[i*h//3:(i+1)*h//3, j*w//3:(j+1)*w//3]
                region_avg = np.mean(region, axis=(0, 1))
                region_hsv = rgb_to_hsv(region_avg[0], region_avg[1], region_avg[2])
                region_colors.append({
                    'rgb': region_avg.tolist(),
                    'hsv': region_hsv
                })
        
        # 4. 边缘特征
        gray = np.mean(img_array, axis=2)
        grad_x = np.abs(np.diff(gray, axis=1, append=gray[:, -1:]))
        grad_y = np.abs(np.diff(gray, axis=0, append=gray[-1:, :]))
        edge_strength = np.mean(grad_x + grad_y)
        edge_density = np.sum((grad_x + grad_y) > 20) / (h * w)
        
        # 5. 颜色分布集中度
        pixels = img_array.reshape(-1, 3)
        color_variance = np.std(pixels, axis=0).mean()
        
        # 6. 计算图片哈希
        img_hash = compute_image_hash(image)
        
        return {
            'avg_color': avg_color.tolist(),
            'hsv': hsv_color,
            'hsv_hint': get_hsv_hint(hsv_color),
            'region_colors': region_colors,
            'brightness': np.mean(avg_color),
            'edge_strength': edge_strength,
            'edge_density': edge_density,
            'color_variance': color_variance,
            'image_hash': img_hash
        }
    except Exception as e:
        print(f"提取图片特征失败: {e}")
        import traceback
        print(traceback.format_exc())
        return None


def compute_image_hash(image, hash_size=8):
    """计算图片的平均哈希"""
    try:
        # 转换为灰度并缩小
        small = image.convert('L').resize((hash_size, hash_size), Image.Resampling.LANCZOS)
        pixels = list(small.getdata())
        avg = sum(pixels) / len(pixels)
        # 生成哈希
        bits = ''.join('1' if p > avg else '0' for p in pixels)
        return hex(int(bits, 2))[2:].zfill(16)
    except:
        return None


def hsv_distance(hsv1, hsv2):
    """计算HSV颜色距离"""
    h1, s1, v1 = hsv1
    h2, s2, v2 = hsv2
    
    # 色相距离（考虑环形）
    h_diff = min(abs(h1 - h2), 360 - abs(h1 - h2))
    # 饱和度和明度距离（归一化到0-100）
    s_diff = abs(s1 - s2) * 100
    v_diff = abs(v1 - v2) * 100
    
    # 加权距离（降低色相权重，提高明度权重）
    return (h_diff * 0.4 + s_diff * 0.2 + v_diff * 0.4)


def calculate_similarity(features1, features2):
    """计算两个特征之间的相似度（0-100）"""
    # HSV距离
    hsv_dist = hsv_distance(features1['hsv'], features2['hsv'])
    hsv_score = max(0, 100 - hsv_dist)
    
    # 亮度距离
    bright_diff = abs(features1['brightness'] - features2['brightness'])
    bright_score = max(0, 100 - bright_diff)
    
    # 边缘强度距离
    edge_diff = abs(features1['edge_strength'] - features2['edge_strength'])
    edge_score = max(0, 100 - edge_diff / 2)
    
    # 综合得分
    similarity = hsv_score * 0.5 + bright_score * 0.3 + edge_score * 0.2
    
    return similarity


def recognize_food_local(image_data, top_n=5, user_id=None, db_session=None):
    """
    本地图片识别 - 智能类别库对比版
    
    识别流程：
    1. 提取图片特征
    2. 优先匹配用户已学习的类别库
    3. 同类别内精细对比
    4. 返回最可能的食物列表
    """
    features = extract_image_features(image_data)
    if not features:
        return None
    
    all_matches = []
    
    # ========== 第一步：匹配用户已学习的类别库 ==========
    if user_id and db_session:
        try:
            from models import LearnedFood, FoodImageSample
            
            # 获取用户所有已学习的食物
            learned_foods = db_session.query(LearnedFood).filter_by(
                user_id=user_id, 
                is_active=True
            ).all()
            
            print(f"[识别调试] 找到 {len(learned_foods)} 个已学习食物")
            
            for learned in learned_foods:
                # 计算与已学习食物的平均特征相似度
                learned_features = {
                    'hsv': [learned.avg_hsv_h, learned.avg_hsv_s, learned.avg_hsv_v],
                    'brightness': learned.avg_brightness,
                    'edge_strength': learned.avg_edge_strength,
                    'color_variance': learned.avg_color_variance
                }
                
                similarity = calculate_similarity(features, learned_features)
                
                # 检查是否已归档（样本数>=2即为已归档）
                is_archived = learned.sample_count >= 2
                
                # 根据学习次数给予加成（学习次数越多，加成越高）
                # 已归档的食物获得额外加成
                learn_boost = min(learned.confirmed_count * 5, 25)
                if is_archived:
                    learn_boost += 15  # 已归档食物额外+15分
                
                final_confidence = min(95, similarity + learn_boost)
                
                # 降低阈值，让更多学习过的食物参与匹配
                # 已归档的食物使用更低的阈值
                if is_archived:
                    threshold = 10  # 已归档食物阈值更低
                else:
                    threshold = max(15, 30 - learned.confirmed_count * 3)
                
                print(f"[识别调试] {learned.food_name}: 相似度={similarity:.1f}, 加成={learn_boost}, 最终={final_confidence:.1f}, 阈值={threshold}, 归档={is_archived}")
                
                # 强制将已归档的学习食物加入结果（确保学习过的食物能被看到）
                if final_confidence >= threshold or is_archived:
                    # 获取类别名称
                    category_name = '其他'
                    if learned.category:
                        category_name = learned.category.name
                    
                    all_matches.append({
                        'name': learned.food_name,
                        'confidence': round(final_confidence, 1),
                        'category': category_name,
                        'source': 'learned_library',
                        'learned_count': learned.confirmed_count,
                        'sample_count': learned.sample_count,
                        'is_archived': is_archived
                    })
            
        except Exception as e:
            print(f"查询学习库失败: {e}")
    
    # ========== 第二步：匹配预定义数据库 ==========
    for category, foods in FOOD_DATABASE.items():
        for food_name, food_info in foods.items():
            # 检查是否已经在学习库结果中
            if any(m['name'] == food_name for m in all_matches):
                continue
            
            # 计算基于HSV的匹配度
            hsv_hint = features['hsv_hint']
            food_hint = food_info.get('hsv_hint', '')
            
            score = 0
            
            # 颜色提示匹配
            if hsv_hint == food_hint:
                score += 50
            elif hsv_hint in ['beige', 'white'] and food_hint in ['beige', 'white']:
                score += 30
            elif hsv_hint in ['red', 'pink', 'orange'] and food_hint in ['red', 'pink', 'orange']:
                score += 25
            elif hsv_hint in ['yellow', 'orange'] and food_hint in ['yellow', 'orange']:
                score += 25
            elif hsv_hint in ['green', 'yellow'] and food_hint in ['green', 'yellow']:
                score += 20
            
            # HSV色相范围匹配
            typical_h = food_info.get('typical_h')
            if typical_h and len(typical_h) >= 2:
                h = features['hsv'][0]
                for i in range(0, len(typical_h), 2):
                    if typical_h[i] <= h <= typical_h[i+1]:
                        score += 25
                        break
            
            # 亮度匹配
            if food_hint == 'white' and features['brightness'] > 180:
                score += 15
            elif food_hint == 'black' and features['brightness'] < 80:
                score += 15
            elif food_hint in ['brown', 'beige'] and 80 <= features['brightness'] <= 180:
                score += 10
            
            if score >= 30:
                all_matches.append({
                    'name': food_name,
                    'confidence': round(min(85, score), 1),
                    'category': category,
                    'source': 'database'
                })
    
    # ========== 第三步：排序和筛选 ==========
    # 优先排序：已归档学习库 > 普通学习库 > 数据库，然后按置信度
    def sort_key(x):
        # 已归档的学习库结果最优先（给予50分加成）
        if x.get('source') == 'learned_library' and x.get('is_archived'):
            source_bonus = 50
        # 普通学习库结果优先（给予30分加成）
        elif x.get('source') == 'learned_library':
            source_bonus = 30
        else:
            source_bonus = 0
        return x['confidence'] + source_bonus
    
    all_matches.sort(key=sort_key, reverse=True)
    
    print(f"[识别调试] 排序后结果: {[(m['name'], m['confidence'], m.get('source'), m.get('is_archived')) for m in all_matches[:5]]}")
    
    # 去重
    seen = set()
    unique_matches = []
    for m in all_matches:
        if m['name'] not in seen:
            seen.add(m['name'])
            unique_matches.append(m)
    
    # 如果没有识别结果，添加默认选项作为兜底
    if len(unique_matches) == 0:
        defaults = [
            {'name': '米饭', 'confidence': 25, 'category': '主食', 'source': 'default'},
            {'name': '青菜', 'confidence': 25, 'category': '蔬菜', 'source': 'default'},
            {'name': '鸡肉', 'confidence': 25, 'category': '肉类', 'source': 'default'},
        ]
        for d in defaults:
            if d['name'] not in seen:
                unique_matches.append(d)
                seen.add(d['name'])
    
    return unique_matches[:top_n]


def save_food_sample(image_data, food_name, category_name, user_id, db_session):
    """
    保存食物学习样本
    
    流程：
    1. 提取图片特征
    2. 查找或创建类别库
    3. 查找或创建已学习食物
    4. 保存样本
    5. 更新食物平均特征
    6. 如果样本数>=2，自动归档到类别库
    """
    try:
        from models import CategoryLibrary, LearnedFood, FoodImageSample
        
        # 提取特征
        features = extract_image_features(image_data)
        if not features:
            return {'success': False, 'message': '无法提取图片特征'}
        
        # 查找或创建类别库
        category = db_session.query(CategoryLibrary).filter_by(name=category_name).first()
        if not category:
            category = CategoryLibrary(
                name=category_name,
                name_en=CATEGORY_NAMES.get(category_name, ''),
                description=f'{category_name}类食物的归档库'
            )
            db_session.add(category)
            db_session.flush()
        
        # 标准化食物名称
        food_name_normalized = food_name.strip().lower()
        
        # 查找或创建已学习食物
        learned = db_session.query(LearnedFood).filter_by(
            user_id=user_id,
            food_name_normalized=food_name_normalized
        ).first()
        
        if not learned:
            learned = LearnedFood(
                user_id=user_id,
                category_id=category.id,
                food_name=food_name.strip(),
                food_name_normalized=food_name_normalized,
                avg_hsv_h=features['hsv'][0],
                avg_hsv_s=features['hsv'][1],
                avg_hsv_v=features['hsv'][2],
                avg_brightness=features['brightness'],
                avg_edge_strength=features['edge_strength'],
                avg_color_variance=features['color_variance'],
                min_hsv_h=features['hsv'][0],
                max_hsv_h=features['hsv'][0],
                min_brightness=features['brightness'],
                max_brightness=features['brightness'],
                sample_count=0,
                confirmed_count=0
            )
            db_session.add(learned)
            db_session.flush()
        
        # 保存样本
        sample = FoodImageSample(
            learned_food_id=learned.id,
            user_id=user_id,
            hsv_h=features['hsv'][0],
            hsv_s=features['hsv'][1],
            hsv_v=features['hsv'][2],
            brightness=features['brightness'],
            edge_strength=features['edge_strength'],
            edge_density=features['edge_density'],
            color_variance=features['color_variance'],
            image_hash=features['image_hash'],
            is_confirmed=True
        )
        sample.set_region_colors([r['hsv'] for r in features['region_colors']])
        db_session.add(sample)
        
        # 更新学习食物的统计
        learned.sample_count += 1
        learned.confirmed_count += 1
        learned.updated_at = datetime.utcnow()
        
        # 更新平均特征（移动平均）
        alpha = 0.3  # 学习率
        learned.avg_hsv_h = learned.avg_hsv_h * (1 - alpha) + features['hsv'][0] * alpha
        learned.avg_hsv_s = learned.avg_hsv_s * (1 - alpha) + features['hsv'][1] * alpha
        learned.avg_hsv_v = learned.avg_hsv_v * (1 - alpha) + features['hsv'][2] * alpha
        learned.avg_brightness = learned.avg_brightness * (1 - alpha) + features['brightness'] * alpha
        learned.avg_edge_strength = learned.avg_edge_strength * (1 - alpha) + features['edge_strength'] * alpha
        learned.avg_color_variance = learned.avg_color_variance * (1 - alpha) + features['color_variance'] * alpha
        
        # 更新范围
        learned.min_hsv_h = min(learned.min_hsv_h, features['hsv'][0])
        learned.max_hsv_h = max(learned.max_hsv_h, features['hsv'][0])
        learned.min_brightness = min(learned.min_brightness, features['brightness'])
        learned.max_brightness = max(learned.max_brightness, features['brightness'])
        
        # 更新类别库统计
        category.food_count = db_session.query(LearnedFood).filter_by(
            category_id=category.id,
            is_active=True
        ).count()
        category.updated_at = datetime.utcnow()
        
        db_session.commit()
        
        return {
            'success': True,
            'message': f'已学习: {food_name}',
            'food_id': learned.id,
            'sample_count': learned.sample_count,
            'confirmed_count': learned.confirmed_count,
            'is_archived': learned.sample_count >= 2
        }
        
    except Exception as e:
        db_session.rollback()
        print(f"保存学习样本失败: {e}")
        import traceback
        print(traceback.format_exc())
        return {'success': False, 'message': f'保存失败: {str(e)}'}


def get_user_learned_foods(user_id, db_session, category_id=None):
    """获取用户已学习的食物列表"""
    try:
        from models import LearnedFood
        
        query = db_session.query(LearnedFood).filter_by(
            user_id=user_id,
            is_active=True
        )
        
        if category_id:
            query = query.filter_by(category_id=category_id)
        
        foods = query.order_by(LearnedFood.updated_at.desc()).all()
        
        return [food.to_dict() for food in foods]
        
    except Exception as e:
        print(f"获取学习库失败: {e}")
        return []


def get_category_libraries(db_session):
    """获取所有类别库"""
    try:
        from models import CategoryLibrary
        
        categories = db_session.query(CategoryLibrary).all()
        return [cat.to_dict() for cat in categories]
        
    except Exception as e:
        print(f"获取类别库失败: {e}")
        return []


# 测试代码
if __name__ == '__main__':
    # 创建一个模拟三文鱼的图片（橙粉色）
    test_img = Image.new('RGB', (150, 150), color=(255, 140, 120))
    buffered = io.BytesIO()
    test_img.save(buffered, format="JPEG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    
    results = recognize_food_local(img_str)
    print("识别结果:")
    for r in results:
        print(f"  {r['name']}: {r['confidence']}% - {r.get('category', '未知')}")
