from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime, date
from werkzeug.security import generate_password_hash, check_password_hash
import json

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
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
    
    # 配料表分析
    ingredients = db.Column(db.Text)
    additives = db.Column(db.Text)  # JSON格式存储添加剂
    
    # 图片
    image_url = db.Column(db.String(255))
    barcode = db.Column(db.String(50))
    
    is_custom = db.Column(db.Boolean, default=False)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
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
    time = db.Column(db.Time, default=datetime.now().time)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    food = db.relationship('Food', backref='records')

class FoodImageFeature(db.Model):
    """存储用户确认的食物图片特征，用于机器学习"""
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
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_used = db.Column(db.DateTime, default=datetime.utcnow)
    
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
    time = db.Column(db.Time, default=datetime.now().time)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
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
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class SleepRecord(db.Model):
    __tablename__ = 'sleep_records'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    bed_time = db.Column(db.DateTime)
    wake_time = db.Column(db.DateTime)
    duration = db.Column(db.Float)  # 小时
    quality = db.Column(db.Integer)  # 1-10评分
    
    # 睡眠影响因素
    caffeine_before_bed = db.Column(db.Boolean, default=False)
    heavy_meal_before_bed = db.Column(db.Boolean, default=False)
    screen_time = db.Column(db.Boolean, default=False)
    
    date = db.Column(db.Date, default=date.today)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class TeaCoffeeLog(db.Model):
    __tablename__ = 'tea_coffee_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    drink_type = db.Column(db.String(50))  # green_tea, black_tea, coffee, oolong, etc.
    amount = db.Column(db.Float, default=250)  # ml
    caffeine_content = db.Column(db.Float, default=0)  # mg
    time = db.Column(db.DateTime, default=datetime.utcnow)
    
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
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

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
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
