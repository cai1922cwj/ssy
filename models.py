from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime, date, timedelta, timezone
from werkzeug.security import generate_password_hash, check_password_hash
import json

db = SQLAlchemy()

# 北京时区
BJ_TZ = timezone(timedelta(hours=8))

def now_bj():
    """获取北京时间"""
    return datetime.now(BJ_TZ)

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: now_bj())
    
    # 个人资料
    age = db.Column(db.Integer, default=25)
    gender = db.Column(db.String(10), default='male')  # male, female
    height = db.Column(db.Float, default=170.0)  # cm
    weight = db.Column(db.Float, default=65.0)  # kg
    activity_level = db.Column(db.String(20), default='moderate')  # sedentary, light, moderate, active, very_active
    goal = db.Column(db.String(20), default='maintain')  # lose, maintain, gain
    
    # 目标设置
    target_calories = db.Column(db.Float, default=2000)
    target_protein = db.Column(db.Float, default=100)
    target_carbs = db.Column(db.Float, default=250)
    target_fat = db.Column(db.Float, default=65)
    
    # 权限
    is_admin = db.Column(db.Boolean, default=False)
    
    # 关系
    food_records = db.relationship('FoodRecord', backref='user', lazy=True, cascade='all, delete-orphan')
    exercise_records = db.relationship('ExerciseRecord', backref='user', lazy=True, cascade='all, delete-orphan')
    weight_records = db.relationship('WeightRecord', backref='user', lazy=True, cascade='all, delete-orphan')
    sleep_records = db.relationship('SleepRecord', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def get_bmi(self):
        if self.height > 0:
            return round(self.weight / ((self.height/100) ** 2), 1)
        return 0
    
    def get_bmr(self):
        # Mifflin-St Jeor Equation
        if self.gender == 'male':
            bmr = 10 * self.weight + 6.25 * self.height - 5 * self.age + 5
        else:
            bmr = 10 * self.weight + 6.25 * self.height - 5 * self.age - 161
        return round(bmr, 1)
    
    def get_tdee(self):
        activity_multipliers = {
            'sedentary': 1.2,
            'light': 1.375,
            'moderate': 1.55,
            'active': 1.725,
            'very_active': 1.9
        }
        multiplier = activity_multipliers.get(self.activity_level, 1.55)
        return round(self.get_bmr() * multiplier, 1)
    
    def calculate_life_expectancy_bonus(self):
        """计算健康生活可增加的寿命年数"""
        bonus = 0.0
        
        # BMI健康范围(18.5-24.9)
        bmi = self.get_bmi()
        if 18.5 <= bmi <= 24.9:
            bonus += 2.5
        elif bmi < 18.5 or bmi > 30:
            bonus += 0.5
        else:
            bonus += 1.5
        
        # 运动习惯
        recent_exercises = ExerciseRecord.query.filter_by(user_id=self.id).filter(
            ExerciseRecord.date >= date.today().replace(day=1)
        ).count()
        if recent_exercises >= 12:  # 每周3次
            bonus += 3.0
        elif recent_exercises >= 8:
            bonus += 2.0
        elif recent_exercises >= 4:
            bonus += 1.0
        
        # 饮食记录完整性
        recent_foods = FoodRecord.query.filter_by(user_id=self.id).filter(
            FoodRecord.date >= date.today().replace(day=1)
        ).count()
        if recent_foods >= 60:  # 每天2次记录
            bonus += 1.5
        
        return round(bonus, 1)

class Food(db.Model):
    __tablename__ = 'foods'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    name_en = db.Column(db.String(100))
    category = db.Column(db.String(50))
    
    # 每100克营养数据
    calories = db.Column(db.Float, default=0)  # kcal
    protein = db.Column(db.Float, default=0)  # g
    carbs = db.Column(db.Float, default=0)  # g
    fat = db.Column(db.Float, default=0)  # g
    fiber = db.Column(db.Float, default=0)  # g
    sugar = db.Column(db.Float, default=0)  # g
    sodium = db.Column(db.Float, default=0)  # mg
    
    # 维生素矿物质
    vitamin_c = db.Column(db.Float, default=0)  # mg
    calcium = db.Column(db.Float, default=0)  # mg
    iron = db.Column(db.Float, default=0)  # mg
    potassium = db.Column(db.Float, default=0)  # mg
    
    # 中医食性（五性分类）
    # cold(寒), cool(凉), neutral(平), warm(温), hot(热)
    food_nature = db.Column(db.String(10), default='neutral')
    
    # 配料表分析
    ingredients = db.Column(db.Text)
    additives = db.Column(db.Text)  # JSON格式存储添加剂
    
    # 图片
    image_url = db.Column(db.String(255))
    barcode = db.Column(db.String(50))
    
    is_custom = db.Column(db.Boolean, default=False)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=lambda: now_bj())
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'name_en': self.name_en,
            'category': self.category,
            'calories': self.calories,
            'protein': self.protein,
            'carbs': self.carbs,
            'fat': self.fat,
            'fiber': self.fiber,
            'sugar': self.sugar,
            'sodium': self.sodium,
            'vitamin_c': self.vitamin_c,
            'calcium': self.calcium,
            'iron': self.iron,
            'potassium': self.potassium,
            'food_nature': self.food_nature,
            'image_url': self.image_url,
            'barcode': self.barcode
        }

class FoodRecord(db.Model):
    __tablename__ = 'food_records'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    food_id = db.Column(db.Integer, db.ForeignKey('foods.id'))
    
    # 记录详情
    food_name = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Float, default=100)  # 克数
    meal_type = db.Column(db.String(20))  # breakfast, lunch, dinner, snack
    
    # 实际摄入营养
    calories = db.Column(db.Float, default=0)
    protein = db.Column(db.Float, default=0)
    carbs = db.Column(db.Float, default=0)
    fat = db.Column(db.Float, default=0)
    fiber = db.Column(db.Float, default=0)
    
    # 记录方式
    input_method = db.Column(db.String(20))  # photo, text, voice, barcode
    photo_url = db.Column(db.String(255))
    
    date = db.Column(db.Date, default=date.today)
    time = db.Column(db.Time, default=lambda: now_bj().time())
    created_at = db.Column(db.DateTime, default=lambda: now_bj())
    
    food = db.relationship('Food', backref='records')


# ==================== 新的智能学习系统模型 ====================

class CategoryLibrary(db.Model):
    """类别库 - 存储各类食物的归档信息"""
    __tablename__ = 'category_libraries'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)  # 类别名称：蔬菜、肉类、海鲜等
    name_en = db.Column(db.String(50))
    description = db.Column(db.Text)
    
    # 类别特征统计（自动计算）
    avg_hsv_h = db.Column(db.Float, default=0)  # 平均色相
    avg_hsv_s = db.Column(db.Float, default=0)  # 平均饱和度
    avg_hsv_v = db.Column(db.Float, default=0)  # 平均明度
    
    # 该类别下的食物数量
    food_count = db.Column(db.Integer, default=0)
    
    created_at = db.Column(db.DateTime, default=lambda: now_bj())
    updated_at = db.Column(db.DateTime, default=lambda: now_bj(), onupdate=lambda: now_bj())
    
    # 关系
    foods = db.relationship('LearnedFood', backref='category', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'name_en': self.name_en,
            'description': self.description,
            'food_count': self.food_count,
            'avg_hsv': [self.avg_hsv_h, self.avg_hsv_s, self.avg_hsv_v]
        }


class LearnedFood(db.Model):
    """已学习的食物 - 用户确认后归档的食物"""
    __tablename__ = 'learned_foods'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category_libraries.id'), nullable=False)
    
    food_name = db.Column(db.String(100), nullable=False)
    food_name_normalized = db.Column(db.String(100))  # 标准化名称（去空格、小写）
    
    # 营养信息（可选）
    calories = db.Column(db.Float)
    protein = db.Column(db.Float)
    carbs = db.Column(db.Float)
    fat = db.Column(db.Float)
    
    # 学习统计
    sample_count = db.Column(db.Integer, default=1)  # 学习样本数量
    confirmed_count = db.Column(db.Integer, default=1)  # 确认次数
    
    # 该食物的平均特征（所有样本的平均值）
    avg_hsv_h = db.Column(db.Float, default=0)
    avg_hsv_s = db.Column(db.Float, default=0)
    avg_hsv_v = db.Column(db.Float, default=0)
    avg_brightness = db.Column(db.Float, default=0)
    avg_edge_strength = db.Column(db.Float, default=0)
    avg_color_variance = db.Column(db.Float, default=0)
    
    # 特征范围（用于快速筛选）
    min_hsv_h = db.Column(db.Float, default=0)
    max_hsv_h = db.Column(db.Float, default=360)
    min_brightness = db.Column(db.Float, default=0)
    max_brightness = db.Column(db.Float, default=255)
    
    is_active = db.Column(db.Boolean, default=True)  # 是否激活
    created_at = db.Column(db.DateTime, default=lambda: now_bj())
    updated_at = db.Column(db.DateTime, default=lambda: now_bj(), onupdate=lambda: now_bj())
    
    # 关系
    samples = db.relationship('FoodImageSample', backref='learned_food', lazy=True, cascade='all, delete-orphan')
    user = db.relationship('User', backref='learned_foods')
    
    def to_dict(self):
        return {
            'id': self.id,
            'food_name': self.food_name,
            'category': self.category.name if self.category else None,
            'category_id': self.category_id,
            'sample_count': self.sample_count,
            'confirmed_count': self.confirmed_count,
            'avg_hsv': [self.avg_hsv_h, self.avg_hsv_s, self.avg_hsv_v],
            'avg_brightness': self.avg_brightness,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class FoodImageSample(db.Model):
    """食物图片样本 - 每次学习保存的单个样本"""
    __tablename__ = 'food_image_samples'
    
    id = db.Column(db.Integer, primary_key=True)
    learned_food_id = db.Column(db.Integer, db.ForeignKey('learned_foods.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # 图片特征（详细记录每个样本的特征）
    hsv_h = db.Column(db.Float, nullable=False)  # 色相 0-360
    hsv_s = db.Column(db.Float, nullable=False)  # 饱和度 0-1
    hsv_v = db.Column(db.Float, nullable=False)  # 明度 0-1
    
    brightness = db.Column(db.Float, nullable=False)
    edge_strength = db.Column(db.Float, default=0)
    edge_density = db.Column(db.Float, default=0)
    color_variance = db.Column(db.Float, default=0)
    
    # 区域颜色特征（JSON存储9个区域的颜色）
    region_colors = db.Column(db.Text)  # JSON格式
    
    # 图片哈希（用于去重）
    image_hash = db.Column(db.String(64))
    
    # 元数据
    is_confirmed = db.Column(db.Boolean, default=True)  # 是否已确认
    confidence_at_save = db.Column(db.Float)  # 保存时的置信度
    created_at = db.Column(db.DateTime, default=lambda: now_bj())
    
    def get_region_colors(self):
        """获取区域颜色列表"""
        if self.region_colors:
            return json.loads(self.region_colors)
        return []
    
    def set_region_colors(self, colors):
        """设置区域颜色列表"""
        self.region_colors = json.dumps(colors)


class FoodRecognitionLog(db.Model):
    """识别日志 - 记录每次识别过程，用于分析改进"""
    __tablename__ = 'food_recognition_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # 识别结果
    image_hash = db.Column(db.String(64))
    recognized_foods = db.Column(db.Text)  # JSON格式，存储识别出的食物列表
    
    # 用户反馈
    user_selected_food = db.Column(db.String(100))  # 用户最终选择的食物
    is_correct = db.Column(db.Boolean)  # 识别是否正确
    
    # 图片特征（用于后续分析）
    hsv_h = db.Column(db.Float)
    hsv_s = db.Column(db.Float)
    hsv_v = db.Column(db.Float)
    brightness = db.Column(db.Float)
    
    # 是否已用于学习
    is_learned = db.Column(db.Boolean, default=False)
    learned_food_id = db.Column(db.Integer, db.ForeignKey('learned_foods.id'))
    
    created_at = db.Column(db.DateTime, default=lambda: now_bj())
    
    def get_recognized_foods(self):
        if self.recognized_foods:
            return json.loads(self.recognized_foods)
        return []
    
    def set_recognized_foods(self, foods):
        self.recognized_foods = json.dumps(foods)


# 保留旧表用于兼容，但不再使用
class FoodImageFeature(db.Model):
    """存储用户确认的食物图片特征，用于机器学习（旧版，保留兼容）"""
    __tablename__ = 'food_image_features'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    food_name = db.Column(db.String(100), nullable=False)
    food_category = db.Column(db.String(50))
    
    # 图片特征数据
    avg_color_r = db.Column(db.Float, nullable=False)
    avg_color_g = db.Column(db.Float, nullable=False)
    avg_color_b = db.Column(db.Float, nullable=False)
    dominant_color_r = db.Column(db.Float, nullable=False)
    dominant_color_g = db.Column(db.Float, nullable=False)
    dominant_color_b = db.Column(db.Float, nullable=False)
    brightness = db.Column(db.Float, nullable=False)
    
    # 可选：存储缩略图或图片哈希
    image_hash = db.Column(db.String(64))
    
    # 统计信息
    confirmed_count = db.Column(db.Integer, default=1)  # 被确认次数
    created_at = db.Column(db.DateTime, default=lambda: now_bj())
    last_used = db.Column(db.DateTime, default=lambda: now_bj())
    
    user = db.relationship('User', backref='image_features')
    
    def to_dict(self):
        return {
            'id': self.id,
            'food_name': self.food_name,
            'food_category': self.food_category,
            'avg_color': [self.avg_color_r, self.avg_color_g, self.avg_color_b],
            'dominant_color': [self.dominant_color_r, self.dominant_color_g, self.dominant_color_b],
            'brightness': self.brightness,
            'confirmed_count': self.confirmed_count
        }

class Exercise(db.Model):
    __tablename__ = 'exercises'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50))  # cardio, strength, flexibility, sports
    
    # MET值(代谢当量)
    met_value = db.Column(db.Float, default=3.0)
    
    # 每小时消耗热量(基于70kg体重)
    calories_per_hour = db.Column(db.Float, default=300)
    
    description = db.Column(db.Text)
    icon = db.Column(db.String(50))
    
    def get_calories_burned(self, weight_kg, minutes):
        """根据体重和时长计算消耗热量"""
        # 公式: MET * 体重(kg) * 时间(小时)
        hours = minutes / 60
        return round(self.met_value * weight_kg * hours, 1)

class ExerciseRecord(db.Model):
    __tablename__ = 'exercise_records'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    exercise_id = db.Column(db.Integer, db.ForeignKey('exercises.id'))
    
    exercise_name = db.Column(db.String(100), nullable=False)
    duration = db.Column(db.Integer, default=30)  # 分钟
    calories_burned = db.Column(db.Float, default=0)
    intensity = db.Column(db.String(20), default='moderate')  # low, moderate, high
    
    date = db.Column(db.Date, default=date.today)
    time = db.Column(db.Time, default=lambda: now_bj().time())
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=lambda: now_bj())
    
    exercise = db.relationship('Exercise', backref='records')

class WeightRecord(db.Model):
    __tablename__ = 'weight_records'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    weight = db.Column(db.Float, nullable=False)
    body_fat = db.Column(db.Float)  # 体脂率
    muscle_mass = db.Column(db.Float)  # 肌肉量
    water = db.Column(db.Float)  # 水分率
    date = db.Column(db.Date, default=date.today)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=lambda: now_bj())


class BmiRecord(db.Model):
    """BMI记录模型 - 存储用户的BMI计算历史"""
    __tablename__ = 'bmi_records'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    bmi = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(20))  # 偏瘦、正常、超重、I度肥胖、II度肥胖、III度肥胖
    height = db.Column(db.Float)  # 身高(cm)
    weight = db.Column(db.Float)  # 体重(kg)
    age = db.Column(db.Integer)  # 年龄
    gender = db.Column(db.String(10))  # male, female
    date = db.Column(db.Date, default=date.today)
    created_at = db.Column(db.DateTime, default=lambda: now_bj())
    
    user = db.relationship('User', backref='bmi_records')
    
    def to_dict(self):
        return {
            'id': self.id,
            'bmi': self.bmi,
            'category': self.category,
            'height': self.height,
            'weight': self.weight,
            'age': self.age,
            'gender': self.gender,
            'date': self.date.strftime('%Y-%m-%d') if self.date else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class SleepRecord(db.Model):
    __tablename__ = 'sleep_records'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    bed_time = db.Column(db.DateTime)
    wake_time = db.Column(db.DateTime)
    duration = db.Column(db.Float)  # 总睡眠时长（小时）
    quality = db.Column(db.Integer)  # 1-10评分
    
    # ===== 智能手表扩展字段 =====
    # 睡眠分期时长（分钟）
    deep_sleep = db.Column(db.Float, default=0)      # 深睡时长
    light_sleep = db.Column(db.Float, default=0)     # 浅睡时长
    rem_sleep = db.Column(db.Float, default=0)       # REM/快速眼动时长
    awake_time = db.Column(db.Float, default=0)      # 清醒时长
    
    # 血氧数据
    avg_spo2 = db.Column(db.Float, default=0)        # 平均血氧饱和度
    min_spo2 = db.Column(db.Float, default=0)        # 最低血氧饱和度
    spo2_below_90_minutes = db.Column(db.Float, default=0)  # 低血氧时长(分钟)
    
    # 心率数据
    sleep_hr_avg = db.Column(db.Integer, default=0)  # 睡眠平均心率
    sleep_hr_min = db.Column(db.Integer, default=0)  # 睡眠最低心率
    sleep_hr_max = db.Column(db.Integer, default=0)  # 睡眠最高心率
    
    # 综合评分（来自手表）
    sleep_score = db.Column(db.Integer, default=0)   # 0-100综合睡眠评分
    
    # 数据来源
    data_source = db.Column(db.String(20), default='manual')  # manual/huawei/apple/xiaomi/csv
    source_device = db.Column(db.String(50))         # 设备型号
    
    # 详细睡眠阶段（JSON格式存储时间序列）
    sleep_stages_detail = db.Column(db.Text)         # 详细的睡眠分期时间点
    
    # 睡眠影响因素
    caffeine_before_bed = db.Column(db.Boolean, default=False)
    heavy_meal_before_bed = db.Column(db.Boolean, default=False)
    screen_time = db.Column(db.Boolean, default=False)
    
    date = db.Column(db.Date, default=date.today)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=lambda: now_bj())

class TeaCoffeeLog(db.Model):
    __tablename__ = 'tea_coffee_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    drink_type = db.Column(db.String(50))  # green_tea, black_tea, coffee, oolong, etc.
    amount = db.Column(db.Float, default=250)  # ml
    caffeine_content = db.Column(db.Float, default=0)  # mg
    time = db.Column(db.DateTime, default=lambda: now_bj())
    
    # 效果记录
    alertness = db.Column(db.Integer)  # 1-10提神程度
    sleep_impact = db.Column(db.Integer)  # 1-10对睡眠影响
    
    date = db.Column(db.Date, default=date.today)

class IntermittentFasting(db.Model):
    __tablename__ = 'intermittent_fasting'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    fasting_type = db.Column(db.String(20))  # 16_8, 18_6, 20_4, 5_2
    start_time = db.Column(db.DateTime)
    end_time = db.Column(db.DateTime)
    duration = db.Column(db.Float)  # 实际禁食时长(小时)
    
    status = db.Column(db.String(20), default='active')  # active, completed, broken
    date = db.Column(db.Date, default=date.today)

class HealthNews(db.Model):
    __tablename__ = 'health_news'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    summary = db.Column(db.Text)
    content = db.Column(db.Text)
    source = db.Column(db.String(100))
    source_url = db.Column(db.String(500))
    image_url = db.Column(db.String(500))
    published_at = db.Column(db.DateTime)
    category = db.Column(db.String(50))  # nutrition, exercise, sleep, research
    created_at = db.Column(db.DateTime, default=lambda: now_bj())

class AIAnalysis(db.Model):
    __tablename__ = 'ai_analyses'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    analysis_type = db.Column(db.String(50))  # diet, exercise, sleep, overall
    content = db.Column(db.Text)  # AI分析内容
    recommendations = db.Column(db.Text)  # JSON格式建议
    health_score = db.Column(db.Integer)  # 0-100健康评分
    life_expectancy_bonus = db.Column(db.Float)  # 寿命增加年数
    
    date = db.Column(db.Date, default=date.today)
    created_at = db.Column(db.DateTime, default=lambda: now_bj())


class PageView(db.Model):
    """页面浏览记录"""
    __tablename__ = 'page_views'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # 页面信息
    endpoint = db.Column(db.String(100))  # 路由端点
    page_name = db.Column(db.String(100))  # 页面名称
    page_url = db.Column(db.String(255))  # 完整URL
    referrer = db.Column(db.String(255))  # 来源页面
    
    # 访问设备信息
    user_agent = db.Column(db.String(255))  # 浏览器信息
    
    # 时间
    viewed_at = db.Column(db.DateTime, default=lambda: now_bj())
    
    user = db.relationship('User', backref='page_views')
    
    @staticmethod
    def get_page_stats(user_id=None, days=7):
        """获取页面访问统计"""
        from datetime import timedelta
        start_date = now_bj() - timedelta(days=days)
        
        query = PageView.query.filter(PageView.viewed_at >= start_date)
        if user_id:
            query = query.filter_by(user_id=user_id)
        
        # 按页面分组统计
        stats = db.session.query(
            PageView.page_name,
            PageView.endpoint,
            db.func.count(PageView.id).label('view_count'),
            db.func.max(PageView.viewed_at).label('last_viewed')
        ).filter(
            PageView.viewed_at >= start_date
        )
        
        if user_id:
            stats = stats.filter(PageView.user_id == user_id)
            
        stats = stats.group_by(PageView.page_name, PageView.endpoint).order_by(
            db.func.count(PageView.id).desc()
        ).all()
        
        return stats
