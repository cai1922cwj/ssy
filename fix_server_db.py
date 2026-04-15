#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
服务器数据库修复脚本 - 完整版
在 PythonAnywhere 服务器上执行，创建缺失的表和类别库
"""
import sys
import os

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# 手动创建应用上下文
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///entropy_food.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# 定义模型
class CategoryLibrary(db.Model):
    __tablename__ = 'category_libraries'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    name_en = db.Column(db.String(50))
    description = db.Column(db.Text)
    keywords = db.Column(db.Text)
    avg_hsv_h = db.Column(db.Float, default=0)
    avg_hsv_s = db.Column(db.Float, default=0)
    avg_hsv_v = db.Column(db.Float, default=0)
    food_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class LearnedFood(db.Model):
    __tablename__ = 'learned_foods'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category_libraries.id'), nullable=False)
    food_name = db.Column(db.String(100), nullable=False)
    food_name_normalized = db.Column(db.String(100))
    sample_count = db.Column(db.Integer, default=1)
    confirmed_count = db.Column(db.Integer, default=1)
    avg_hsv_h = db.Column(db.Float, default=0)
    avg_hsv_s = db.Column(db.Float, default=0)
    avg_hsv_v = db.Column(db.Float, default=0)
    avg_brightness = db.Column(db.Float, default=0)
    avg_edge_strength = db.Column(db.Float, default=0)
    avg_color_variance = db.Column(db.Float, default=0)
    min_hsv_h = db.Column(db.Float, default=0)
    max_hsv_h = db.Column(db.Float, default=360)
    min_brightness = db.Column(db.Float, default=0)
    max_brightness = db.Column(db.Float, default=255)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class FoodImageSample(db.Model):
    __tablename__ = 'food_image_samples'
    id = db.Column(db.Integer, primary_key=True)
    learned_food_id = db.Column(db.Integer, db.ForeignKey('learned_foods.id'), nullable=False)
    user_id = db.Column(db.Integer, nullable=False)
    hsv_h = db.Column(db.Float, nullable=False)
    hsv_s = db.Column(db.Float, nullable=False)
    hsv_v = db.Column(db.Float, nullable=False)
    brightness = db.Column(db.Float, nullable=False)
    edge_strength = db.Column(db.Float, default=0)
    edge_density = db.Column(db.Float, default=0)
    color_variance = db.Column(db.Float, default=0)
    region_colors = db.Column(db.Text)
    image_hash = db.Column(db.String(64))
    is_confirmed = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class FoodRecognitionLog(db.Model):
    __tablename__ = 'food_recognition_logs'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    image_hash = db.Column(db.String(64))
    recognized_food = db.Column(db.String(100))
    confidence = db.Column(db.Float)
    is_correct = db.Column(db.Boolean)
    user_corrected_name = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

print("=" * 50)
print("服务器数据库修复工具")
print("=" * 50)

with app.app_context():
    print("\n1. 删除旧表（如果结构不正确）...")
    # 删除可能结构不正确的表
    db.session.execute(db.text("DROP TABLE IF EXISTS food_image_samples"))
    db.session.execute(db.text("DROP TABLE IF EXISTS learned_foods"))
    db.session.execute(db.text("DROP TABLE IF EXISTS category_libraries"))
    db.session.execute(db.text("DROP TABLE IF EXISTS food_recognition_logs"))
    db.session.commit()
    print("   [OK] 旧表已删除")
    
    print("\n2. 创建所有新表...")
    db.create_all()
    print("   [OK] 表创建完成")
    
    print("\n3. 初始化类别库...")
    
    # 定义所有类别
    categories = [
        {'name': '蔬菜', 'name_en': 'vegetables', 'description': '各类新鲜蔬菜，富含维生素和膳食纤维', 
         'keywords': '青菜,白菜,菠菜,芹菜,黄瓜,西红柿,茄子,豆角,青椒,萝卜,土豆,南瓜,冬瓜,丝瓜,苦瓜,生菜,油麦菜,空心菜,苋菜,韭菜,葱,姜,蒜,洋葱,西兰花,花菜,莴笋,竹笋,香菇,蘑菇,木耳'},
        {'name': '肉类', 'name_en': 'meat', 'description': '猪牛羊鸡等畜禽肉类，主要蛋白质来源',
         'keywords': '猪肉,牛肉,羊肉,鸡肉,鸭肉,鹅肉,火腿,培根,香肠,排骨,五花肉,里脊,牛腩,牛排,羊排,鸡腿,鸡翅,鸡胸肉'},
        {'name': '海鲜', 'name_en': 'seafood', 'description': '鱼、虾、蟹、贝类等水产品，富含优质蛋白',
         'keywords': '鱼,虾,蟹,贝,鱿鱼,章鱼,海参,鲍鱼,龙虾,对虾,基围虾,带鱼,黄花鱼,鲫鱼,鲤鱼,三文鱼,金枪鱼,鳕鱼,扇贝,蛤蜊,牡蛎,生蚝'},
        {'name': '水果', 'name_en': 'fruit', 'description': '各类新鲜水果，富含维生素和矿物质',
         'keywords': '苹果,香蕉,橙子,橘子,柚子,葡萄,西瓜,哈密瓜,草莓,蓝莓,樱桃,桃子,梨子,李子,杏子,柿子,石榴,芒果,菠萝,榴莲,火龙果,猕猴桃,柠檬'},
        {'name': '主食', 'name_en': 'staple', 'description': '米饭、面条、面包等碳水化合物主食',
         'keywords': '米饭,面条,馒头,包子,饺子,馄饨,粥,米粉,河粉,拉面,刀削面,意大利面,面包,吐司,三明治,汉堡,披萨,煎饼,油条,烧饼,玉米,红薯,紫薯,土豆泥'},
        {'name': '蛋类', 'name_en': 'egg', 'description': '鸡蛋、鸭蛋等各种蛋类食品',
         'keywords': '鸡蛋,鸭蛋,鹅蛋,鹌鹑蛋,皮蛋,咸蛋,荷包蛋,煎蛋,炒蛋,蒸蛋,茶叶蛋,卤蛋'},
        {'name': '豆类', 'name_en': 'beans', 'description': '黄豆、豆腐、豆浆等豆制品',
         'keywords': '黄豆,黑豆,红豆,绿豆,豌豆,蚕豆,豆腐,豆腐干,豆腐皮,腐竹,豆浆,豆奶,豆芽,毛豆,四季豆,荷兰豆'},
        {'name': '饮品', 'name_en': 'beverage', 'description': '牛奶、咖啡、茶等各种饮料',
         'keywords': '牛奶,酸奶,豆浆,咖啡,茶,绿茶,红茶,乌龙茶,奶茶,果汁,可乐,雪碧,汽水,啤酒,红酒,白酒,蜂蜜水,柠檬水'},
        {'name': '坚果', 'name_en': 'nuts', 'description': '花生、核桃、杏仁等坚果零食',
         'keywords': '花生,核桃,杏仁,腰果,开心果,瓜子,松子,榛子,夏威夷果,碧根果,巴旦木,葡萄干,红枣,枸杞,桂圆,莲子'},
        {'name': '其他', 'name_en': 'other', 'description': '其他未分类食物',
         'keywords': '零食,糖果,巧克力,饼干,蛋糕,面包,薯片,辣条,果冻,布丁,冰淇淋,雪糕,甜点,酱料,调料,油,盐,酱,醋'}
    ]
    
    for cat_data in categories:
        cat = CategoryLibrary(**cat_data)
        db.session.add(cat)
        print(f"   [NEW] 创建类别: {cat_data['name']}")
    
    db.session.commit()
    print(f"\n   [OK] 共创建 {len(categories)} 个类别")
    
    # 显示所有类别
    print("\n4. 验证所有类别...")
    existing = CategoryLibrary.query.all()
    for c in existing:
        print(f"   - {c.name} (ID: {c.id})")
    
    print("\n5. 验证表结构...")
    from sqlalchemy import inspect
    inspector = inspect(db.engine)
    tables = inspector.get_table_names()
    
    required_tables = [
        'category_libraries',
        'learned_foods', 
        'food_image_samples',
        'food_recognition_logs'
    ]
    
    all_ok = True
    for table in required_tables:
        if table in tables:
            cols = [c['name'] for c in inspector.get_columns(table)]
            print(f"   [OK] {table} ({len(cols)} 列)")
        else:
            print(f"   [FAIL] {table} 缺失!")
            all_ok = False
    
    print("\n" + "=" * 50)
    if all_ok and len(existing) == 10:
        print("数据库修复完成！")
        print("请刷新网页重新测试学习功能。")
    else:
        print(f"警告: 只有 {len(existing)} 个类别，应该有 10 个")
    print("=" * 50)
