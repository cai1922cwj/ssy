"""
熵食源 - 在线食物营养分析APP
主应用文件
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime, date, timedelta
import os
import json
import base64
import random
import re
from io import BytesIO

from models import db, User, Food, FoodRecord, Exercise, ExerciseRecord, WeightRecord, SleepRecord, TeaCoffeeLog, IntermittentFasting, HealthNews, AIAnalysis

app = Flask(__name__)
app.config.from_object('config.Config')

# 初始化扩展
db.init_app(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = '请先登录'

# 确保上传目录存在
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ==================== 模板上下文处理器 ====================

@app.context_processor
def inject_variables():
    """向所有模板注入通用变量"""
    life_expectancy_bonus = 0
    return dict(
        life_expectancy_bonus=life_expectancy_bonus,
        timedelta=timedelta
    )


# ==================== 辅助函数 ====================

def init_database():
    """初始化数据库和示例数据"""
    with app.app_context():
        db.create_all()
        
        # 检查是否已有数据
        if Food.query.count() == 0:
            init_foods()
        if Exercise.query.count() == 0:
            init_exercises()
        if HealthNews.query.count() == 0:
            init_news()


def init_foods():
    """初始化食物数据库"""
    foods = [
        # 主食类
        Food(name='白米饭', calories=116, protein=2.6, carbs=25.9, fat=0.3, fiber=0.3, category='主食'),
        Food(name='全麦面包', calories=247, protein=13, carbs=41, fat=3.4, fiber=7, category='主食'),
        Food(name='面条', calories=284, protein=8, carbs=59, fat=1.2, fiber=2.4, category='主食'),
        Food(name='燕麦片', calories=389, protein=17, carbs=66, fat=7, fiber=11, category='主食'),
        Food(name='糙米饭', calories=111, protein=2.5, carbs=23, fat=0.9, fiber=1.8, category='主食'),
        
        # 肉类
        Food(name='鸡胸肉', calories=133, protein=31, carbs=0, fat=1.2, fiber=0, category='肉类'),
        Food(name='牛肉', calories=250, protein=26, carbs=0, fat=15, fiber=0, category='肉类'),
        Food(name='猪肉', calories=272, protein=27, carbs=0, fat=18, fiber=0, category='肉类'),
        Food(name='鱼肉', calories=90, protein=20, carbs=0, fat=1, fiber=0, category='肉类'),
        Food(name='虾仁', calories=99, protein=24, carbs=0, fat=0.3, fiber=0, category='肉类'),
        
        # 蔬菜类
        Food(name='西兰花', calories=34, protein=3, carbs=6, fat=0.4, fiber=2.6, category='蔬菜'),
        Food(name='菠菜', calories=23, protein=3, carbs=4, fat=0.3, fiber=2.2, category='蔬菜'),
        Food(name='胡萝卜', calories=41, protein=1, carbs=10, fat=0.2, fiber=2.8, category='蔬菜'),
        Food(name='番茄', calories=18, protein=0.9, carbs=4, fat=0.2, fiber=1.2, category='蔬菜'),
        Food(name='黄瓜', calories=15, protein=0.7, carbs=4, fat=0.1, fiber=0.5, category='蔬菜'),
        
        # 水果类
        Food(name='苹果', calories=52, protein=0.3, carbs=14, fat=0.2, fiber=2.4, category='水果'),
        Food(name='香蕉', calories=89, protein=1.1, carbs=23, fat=0.3, fiber=2.6, category='水果'),
        Food(name='橙子', calories=47, protein=0.9, carbs=12, fat=0.1, fiber=2.4, category='水果'),
        Food(name='葡萄', calories=67, protein=0.6, carbs=17, fat=0.4, fiber=0.9, category='水果'),
        Food(name='蓝莓', calories=57, protein=0.7, carbs=14, fat=0.3, fiber=2.4, category='水果'),
        
        # 饮品类
        Food(name='牛奶', calories=42, protein=3.4, carbs=5, fat=1, fiber=0, category='饮品'),
        Food(name='酸奶', calories=59, protein=3.2, carbs=7, fat=1.7, fiber=0, category='饮品'),
        Food(name='绿茶', calories=1, protein=0, carbs=0, fat=0, fiber=0, category='饮品'),
        Food(name='咖啡', calories=2, protein=0.3, carbs=0, fat=0, fiber=0, category='饮品'),
        Food(name='橙汁', calories=45, protein=0.7, carbs=10, fat=0.2, fiber=0.2, category='饮品'),
        
        # 蛋类
        Food(name='鸡蛋', calories=155, protein=13, carbs=1.1, fat=11, fiber=0, category='蛋类'),
        Food(name='蛋白', calories=52, protein=11, carbs=0.7, fat=0.2, fiber=0, category='蛋类'),
        Food(name='蛋黄', calories=322, protein=16, carbs=3.6, fat=27, fiber=0, category='蛋类'),
        
        # 坚果类
        Food(name='杏仁', calories=579, protein=21, carbs=22, fat=50, fiber=12, category='坚果'),
        Food(name='核桃', calories=654, protein=15, carbs=14, fat=65, fiber=7, category='坚果'),
        Food(name='花生', calories=567, protein=26, carbs=16, fat=49, fiber=8, category='坚果'),
        
        # 常见快餐
        Food(name='汉堡', calories=295, protein=15, carbs=24, fat=14, fiber=1.5, category='快餐'),
        Food(name='披萨', calories=266, protein=11, carbs=33, fat=10, fiber=2.3, category='快餐'),
        Food(name='炸薯条', calories=312, protein=3, carbs=41, fat=15, fiber=3.8, category='快餐'),
        Food(name='炸鸡', calories=298, protein=24, carbs=10, fat=17, fiber=0.5, category='快餐'),
        
        # 中国传统食物
        Food(name='饺子', calories=242, protein=12, carbs=28, fat=10, fiber=1.2, category='中式主食'),
        Food(name='包子', calories=227, protein=9, carbs=35, fat=6, fiber=1.4, category='中式主食'),
        Food(name='馒头', calories=223, protein=7, carbs=47, fat=1.1, fiber=1.3, category='中式主食'),
        Food(name='豆腐', calories=81, protein=8, carbs=2, fat=4.8, fiber=0.4, category='豆制品'),
        Food(name='豆浆', calories=33, protein=3, carbs=2, fat=1.6, fiber=0.3, category='豆制品'),
    ]
    
    for food in foods:
        db.session.add(food)
    db.session.commit()


def init_exercises():
    """初始化运动数据库"""
    exercises = [
        # 有氧运动
        Exercise(name='快走', category='cardio', met_value=3.8, calories_per_hour=280, description='户外或跑步机快走'),
        Exercise(name='慢跑', category='cardio', met_value=7.0, calories_per_hour=500, description='每小时7-8公里'),
        Exercise(name='跑步', category='cardio', met_value=9.8, calories_per_hour=700, description='每小时10-12公里'),
        Exercise(name='游泳', category='cardio', met_value=6.0, calories_per_hour=450, description='自由泳'),
        Exercise(name='骑自行车', category='cardio', met_value=5.8, calories_per_hour=400, description='户外骑行'),
        Exercise(name='跳绳', category='cardio', met_value=11.8, calories_per_hour=850, description='中等强度'),
        Exercise(name='瑜伽', category='flexibility', met_value=3.0, calories_per_hour=200, description='哈他瑜伽'),
        Exercise(name='健身操', category='cardio', met_value=6.5, calories_per_hour=480, description='有氧健身操'),
        
        # 力量训练
        Exercise(name='哑铃训练', category='strength', met_value=5.0, calories_per_hour=350, description='上肢力量训练'),
        Exercise(name='深蹲', category='strength', met_value=5.0, calories_per_hour=350, description='自重深蹲'),
        Exercise(name='硬拉', category='strength', met_value=6.0, calories_per_hour=420, description='负重硬拉'),
        Exercise(name='俯卧撑', category='strength', met_value=4.0, calories_per_hour=280, description='标准俯卧撑'),
        Exercise(name='平板支撑', category='strength', met_value=4.0, calories_per_hour=280, description='核心训练'),
        
        # 球类运动
        Exercise(name='篮球', category='sports', met_value=8.0, calories_per_hour=580, description='半场或全场'),
        Exercise(name='足球', category='sports', met_value=8.0, calories_per_hour=580, description='比赛或训练'),
        Exercise(name='网球', category='sports', met_value=7.3, calories_per_hour=520, description='单打比赛'),
        Exercise(name='乒乓球', category='sports', met_value=4.0, calories_per_hour=280, description='休闲打球'),
        
        # 日常活动
        Exercise(name='家务劳动', category='daily', met_value=3.5, calories_per_hour=250, description='清洁打扫'),
        Exercise(name='爬楼梯', category='cardio', met_value=8.8, calories_per_hour=650, description='连续爬楼'),
        Exercise(name='散步', category='cardio', met_value=2.5, calories_per_hour=180, description='轻松步行'),
    ]
    
    for ex in exercises:
        db.session.add(ex)
    db.session.commit()


def init_news():
    """初始化健康新闻"""
    news_items = [
        {
            'title': '研究表明：地中海饮食可降低心血管疾病风险',
            'summary': '最新研究显示，坚持地中海饮食模式可显著降低心血管疾病发生率。',
            'source': '哈佛公共卫生学院',
            'category': 'nutrition',
            'published_at': datetime.now() - timedelta(days=2)
        },
        {
            'title': '适度运动如何改善睡眠质量',
            'summary': '研究发现，每天进行30分钟中等强度运动可显著改善睡眠质量。',
            'source': 'NIH国立睡眠研究所',
            'category': 'exercise',
            'published_at': datetime.now() - timedelta(days=5)
        },
        {
            'title': '蛋白质摄入时机对肌肉合成的影响',
            'summary': '运动前后蛋白质摄入的最佳时机和数量对肌肉增长至关重要。',
            'source': '国际运动营养学会',
            'category': 'nutrition',
            'published_at': datetime.now() - timedelta(days=7)
        },
        {
            'title': '间歇性禁食的健康益处研究进展',
            'summary': '多项研究表明，间歇性禁食可能改善代谢健康和延长寿命。',
            'source': '《新英格兰医学杂志》',
            'category': 'research',
            'published_at': datetime.now() - timedelta(days=10)
        },
        {
            'title': '睡眠不足与肥胖的关联机制',
            'summary': '研究表明睡眠不足会影响荷尔蒙平衡，导致食欲增加和代谢减慢。',
            'source': '斯坦福大学睡眠研究中心',
            'category': 'sleep',
            'published_at': datetime.now() - timedelta(days=12)
        },
    ]
    
    for news in news_items:
        hn = HealthNews(**news)
        db.session.add(hn)
    db.session.commit()


def calculate_life_expectancy():
    """计算健康生活方式可延长的寿命"""
    bonus_years = 0
    tips = []
    
    # 检查用户是否登录
    if not current_user.is_authenticated:
        return bonus_years, tips
    
    # BMI评估
    try:
        bmi = current_user.get_bmi()
        if 18.5 <= bmi <= 24.9:
            bonus_years += 2.5
            tips.append('✅ 您的BMI在健康范围内')
        elif 25 <= bmi <= 29.9:
            bonus_years += 1.0
            tips.append('⚠️ 适当减重可增加寿命')
        else:
            bonus_years += 0.5
            tips.append('⚠️ 建议咨询医生制定减重计划')
        
        # 运动习惯
        recent_exercises = ExerciseRecord.query.filter(
            ExerciseRecord.user_id == current_user.id,
            ExerciseRecord.date >= date.today() - timedelta(days=30)
        ).count()
        
        if recent_exercises >= 12:
            bonus_years += 3.0
            tips.append('✅ 您的运动习惯良好')
        elif recent_exercises >= 4:
            bonus_years += 1.5
            tips.append('⚠️ 增加运动频率可延年益寿')
        else:
            tips.append('⚠️ 建议每周至少运动3次')
        
        # 饮食记录
        recent_foods = FoodRecord.query.filter(
            FoodRecord.user_id == current_user.id,
            FoodRecord.date >= date.today() - timedelta(days=30)
        ).count()
        
        if recent_foods >= 60:
            bonus_years += 1.5
            tips.append('✅ 您的饮食记录习惯很好')
        
        # 睡眠质量
        avg_sleep = db.session.query(db.func.avg(SleepRecord.duration)).filter(
            SleepRecord.user_id == current_user.id,
            SleepRecord.date >= date.today() - timedelta(days=30)
        ).scalar()
        
        if avg_sleep and 7 <= avg_sleep <= 9:
            bonus_years += 2.0
            tips.append('✅ 您的睡眠时间充足')
        elif avg_sleep and avg_sleep < 7:
            tips.append('⚠️ 建议保证7-9小时睡眠')
    except Exception as e:
        pass  # 忽略计算错误
    
    return round(bonus_years, 1), tips


# ==================== 路由 ====================

@app.route('/')
def index():
    """首页"""
    life_expectancy_bonus, tips = calculate_life_expectancy() if current_user.is_authenticated else (0, [])
    
    news = HealthNews.query.order_by(HealthNews.published_at.desc()).limit(5).all()
    today_stats = get_today_stats() if current_user.is_authenticated else None
    
    return render_template('index.html', 
                         news=news, 
                         life_expectancy_bonus=life_expectancy_bonus,
                         tips=tips,
                         today_stats=today_stats)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        if User.query.filter_by(email=email).first():
            flash('该邮箱已被注册', 'error')
            return redirect(url_for('register'))
        
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        flash('注册成功！请登录', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            login_user(user)
            flash('登录成功！', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))
        
        flash('邮箱或密码错误', 'error')
    
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('已退出登录', 'info')
    return redirect(url_for('index'))


# ==================== 食物管理 ====================

@app.route('/foods')
@login_required
def foods():
    """食物库页面"""
    category = request.args.get('category')
    search = request.args.get('search')
    
    query = Food.query
    if category:
        query = query.filter_by(category=category)
    if search:
        query = query.filter(Food.name.contains(search))
    
    foods = query.order_by(Food.name).all()
    categories = db.session.query(Food.category).distinct().all()
    categories = [c[0] for c in categories if c[0]]
    
    return render_template('foods.html', foods=foods, categories=categories, current_category=category)


@app.route('/api/foods')
@login_required
def api_foods():
    """食物搜索API"""
    query = request.args.get('q', '')
    foods = Food.query.filter(Food.name.contains(query)).limit(10).all()
    return jsonify([f.to_dict() for f in foods])


@app.route('/api/foods/<int:food_id>')
@login_required
def api_food_detail(food_id):
    """食物详情API"""
    food = Food.query.get_or_404(food_id)
    return jsonify(food.to_dict())


@app.route('/foods/add', methods=['GET', 'POST'])
@login_required
def add_food():
    """添加自定义食物"""
    if request.method == 'POST':
        food = Food(
            name=request.form.get('name'),
            category=request.form.get('category'),
            calories=float(request.form.get('calories', 0)),
            protein=float(request.form.get('protein', 0)),
            carbs=float(request.form.get('carbs', 0)),
            fat=float(request.form.get('fat', 0)),
            fiber=float(request.form.get('fiber', 0)),
            is_custom=True,
            created_by=current_user.id
        )
        db.session.add(food)
        db.session.commit()
        flash('食物添加成功！', 'success')
        return redirect(url_for('foods'))
    
    return render_template('add_food.html')


# ==================== 饮食记录 ====================

@app.route('/diet')
@login_required
def diet():
    """饮食记录页面"""
    record_date = request.args.get('date', date.today().isoformat())
    try:
        target_date = datetime.strptime(record_date, '%Y-%m-%d').date()
    except:
        target_date = date.today()
    
    records = FoodRecord.query.filter_by(user_id=current_user.id, date=target_date).order_by(FoodRecord.time).all()
    
    # 统计
    total_calories = sum(r.calories for r in records)
    total_protein = sum(r.protein for r in records)
    total_carbs = sum(r.carbs for r in records)
    total_fat = sum(r.fat for r in records)
    
    return render_template('diet.html',
                         records=records,
                         target_date=target_date,
                         total_calories=total_calories,
                         total_protein=total_protein,
                         total_carbs=total_carbs,
                         total_fat=total_fat,
                         target_calories=current_user.target_calories)


@app.route('/diet/add', methods=['GET', 'POST'])
@login_required
def add_diet_record():
    """添加饮食记录"""
    if request.method == 'POST':
        food_id = request.form.get('food_id')
        food_name = request.form.get('food_name')
        quantity = float(request.form.get('quantity', 100))
        meal_type = request.form.get('meal_type', 'snack')
        
        food = Food.query.get(food_id) if food_id else None
        
        record = FoodRecord(
            user_id=current_user.id,
            food_id=food_id,
            food_name=food_name or (food.name if food else '未知食物'),
            quantity=quantity,
            meal_type=meal_type,
            calories=(food.calories * quantity / 100) if food else 0,
            protein=(food.protein * quantity / 100) if food else 0,
            carbs=(food.carbs * quantity / 100) if food else 0,
            fat=(food.fat * quantity / 100) if food else 0,
            input_method=request.form.get('input_method', 'text')
        )
        
        db.session.add(record)
        db.session.commit()
        
        flash('饮食记录已添加！', 'success')
        return redirect(url_for('diet'))
    
    # 获取常用食物
    recent_foods = db.session.query(
        FoodRecord.food_name,
        db.func.count(FoodRecord.id).label('count')
    ).filter(
        FoodRecord.user_id == current_user.id
    ).group_by(FoodRecord.food_name).order_by(
        db.func.count(FoodRecord.id).desc()
    ).limit(10).all()
    
    return render_template('add_diet.html', recent_foods=recent_foods)


@app.route('/api/diet/search')
@login_required
def api_diet_search():
    """搜索食物用于饮食记录"""
    query = request.args.get('q', '')
    foods = Food.query.filter(Food.name.contains(query)).limit(10).all()
    return jsonify([f.to_dict() for f in foods])


# ==================== 运动管理 ====================

@app.route('/exercise')
@login_required
def exercise():
    """运动记录页面"""
    record_date = request.args.get('date', date.today().isoformat())
    try:
        target_date = datetime.strptime(record_date, '%Y-%m-%d').date()
    except:
        target_date = date.today()
    
    records = ExerciseRecord.query.filter_by(user_id=current_user.id, date=target_date).all()
    total_burned = sum(r.calories_burned for r in records)
    
    return render_template('exercise.html',
                         records=records,
                         target_date=target_date,
                         total_burned=total_burned)


@app.route('/exercise/add', methods=['GET', 'POST'])
@login_required
def add_exercise():
    """添加运动记录"""
    if request.method == 'POST':
        exercise_id = request.form.get('exercise_id')
        exercise_name = request.form.get('exercise_name')
        duration = int(request.form.get('duration', 30))
        intensity = request.form.get('intensity', 'moderate')
        
        exercise = Exercise.query.get(exercise_id) if exercise_id else None
        
        calories = 0
        if exercise:
            calories = exercise.get_calories_burned(current_user.weight, duration)
        else:
            # 默认估算
            calories = duration * 5  # 约5kcal/分钟
        
        record = ExerciseRecord(
            user_id=current_user.id,
            exercise_id=exercise_id,
            exercise_name=exercise_name or (exercise.name if exercise else '未知运动'),
            duration=duration,
            calories_burned=calories,
            intensity=intensity
        )
        
        db.session.add(record)
        db.session.commit()
        
        flash(f'运动记录已添加！燃烧了 {calories} kcal', 'success')
        return redirect(url_for('exercise'))
    
    exercises = Exercise.query.order_by(Exercise.name).all()
    return render_template('add_exercise.html', exercises=exercises)


@app.route('/api/exercises')
@login_required
def api_exercises():
    """运动列表API"""
    exercises = Exercise.query.order_by(Exercise.name).all()
    return jsonify([{
        'id': e.id,
        'name': e.name,
        'category': e.category,
        'calories_per_hour': e.calories_per_hour,
        'met_value': e.met_value
    } for e in exercises])


# ==================== 体重管理 ====================

@app.route('/weight')
@login_required
def weight():
    """体重记录页面"""
    records = WeightRecord.query.filter_by(user_id=current_user.id).order_by(WeightRecord.date.desc()).limit(30).all()
    
    current_weight = records[0].weight if records else current_user.weight
    weight_change = 0
    if len(records) >= 2:
        weight_change = records[0].weight - records[1].weight
    
    return render_template('weight.html',
                         records=records,
                         current_weight=current_weight,
                         weight_change=weight_change,
                         target_weight=request.args.get('target', 65))


@app.route('/weight/add', methods=['POST'])
@login_required
def add_weight():
    """添加体重记录"""
    weight = float(request.form.get('weight'))
    
    record = WeightRecord(
        user_id=current_user.id,
        weight=weight,
        body_fat=request.form.get('body_fat'),
        notes=request.form.get('notes')
    )
    
    # 更新用户当前体重
    current_user.weight = weight
    
    db.session.add(record)
    db.session.commit()
    
    flash('体重记录已添加！', 'success')
    return redirect(url_for('weight'))


# ==================== 睡眠管理 ====================

@app.route('/sleep')
@login_required
def sleep():
    """睡眠记录页面"""
    records = SleepRecord.query.filter_by(user_id=current_user.id).order_by(SleepRecord.date.desc()).limit(14).all()
    
    avg_duration = 0
    avg_quality = 0
    if records:
        avg_duration = sum(r.duration for r in records if r.duration) / len(records)
        avg_quality = sum(r.quality for r in records if r.quality) / len(records)
    
    return render_template('sleep.html',
                         records=records,
                         avg_duration=round(avg_duration, 1),
                         avg_quality=round(avg_quality, 1))


@app.route('/sleep/add', methods=['POST'])
@login_required
def add_sleep():
    """添加睡眠记录"""
    bed_time_str = request.form.get('bed_time')
    wake_time_str = request.form.get('wake_time')
    
    try:
        bed_time = datetime.strptime(bed_time_str, '%Y-%m-%dT%H:%M') if bed_time_str else None
        wake_time = datetime.strptime(wake_time_str, '%Y-%m-%dT%H:%M') if wake_time_str else None
        
        duration = None
        if bed_time and wake_time:
            duration = (wake_time - bed_time).total_seconds() / 3600
    except:
        duration = float(request.form.get('duration', 7))
    
    record = SleepRecord(
        user_id=current_user.id,
        bed_time=bed_time,
        wake_time=wake_time,
        duration=duration,
        quality=int(request.form.get('quality', 7)),
        caffeine_before_bed=bool(request.form.get('caffeine')),
        heavy_meal_before_bed=bool(request.form.get('heavy_meal')),
        screen_time=bool(request.form.get('screen_time')),
        notes=request.form.get('notes')
    )
    
    db.session.add(record)
    db.session.commit()
    
    flash('睡眠记录已添加！', 'success')
    return redirect(url_for('sleep'))


# ==================== 茶与咖啡 ====================

@app.route('/beverages')
@login_required
def beverages():
    """茶与咖啡建议页面"""
    logs = TeaCoffeeLog.query.filter_by(user_id=current_user.id).order_by(TeaCoffeeLog.date.desc()).limit(14).all()
    
    # 建议
    suggestions = {
        'green_tea': '绿茶富含抗氧化物质，建议上午饮用以获得最佳效果。每日2-3杯为宜。',
        'black_tea': '红茶适合配合餐食饮用，可帮助消化。避免睡前2小时饮用。',
        'coffee': '咖啡建议在上午9-11点饮用，此时皮质醇水平下降。每日不超过400mg咖啡因。',
        'oolong': '乌龙茶适合午后饮用，帮助消化脂肪。半发酵茶，介于绿茶和红茶之间。'
    }
    
    return render_template('beverages.html', logs=logs, suggestions=suggestions)


@app.route('/beverages/add', methods=['POST'])
@login_required
def add_beverage():
    """添加茶/咖啡记录"""
    drink_type = request.form.get('drink_type')
    
    caffeine_content = {
        'green_tea': 30,
        'black_tea': 45,
        'coffee': 95,
        'oolong': 37
    }.get(drink_type, 50)
    
    log = TeaCoffeeLog(
        user_id=current_user.id,
        drink_type=drink_type,
        amount=float(request.form.get('amount', 250)),
        caffeine_content=caffeine_content,
        alertness=int(request.form.get('alertness', 5)),
        sleep_impact=int(request.form.get('sleep_impact', 3))
    )
    
    db.session.add(log)
    db.session.commit()
    
    flash('记录已添加！', 'success')
    return redirect(url_for('beverages'))


# ==================== 轻断食 ====================

@app.route('/fasting')
@login_required
def fasting():
    """轻断食页面"""
    records = IntermittentFasting.query.filter_by(user_id=current_user.id).order_by(IntermittentFasting.date.desc()).limit(30).all()
    
    suggestions = {
        '16_8': '16:8方案 - 每天禁食16小时，在8小时内进食。推荐早晨9点到下午5点进食。',
        '18_6': '18:6方案 - 每天禁食18小时，在6小时内进食。更加激进，适合有经验者。',
        '20_4': '20:4方案 - 每天禁食20小时，在4小时内进食。又称"战士饮食"，适合短期执行。',
        '5_2': '5:2方案 - 每周5天正常饮食，2天限制热量摄入（女性500kcal，男性600kcal）。'
    }
    
    return render_template('fasting.html', records=records, suggestions=suggestions)


@app.route('/fasting/start', methods=['POST'])
@login_required
def start_fasting():
    """开始轻断食"""
    fasting_type = request.form.get('fasting_type')
    
    record = IntermittentFasting(
        user_id=current_user.id,
        fasting_type=fasting_type,
        start_time=datetime.now(),
        status='active'
    )
    
    db.session.add(record)
    db.session.commit()
    
    flash('轻断食已开始！', 'success')
    return redirect(url_for('fasting'))


@app.route('/fasting/end/<int:record_id>', methods=['POST'])
@login_required
def end_fasting(record_id):
    """结束轻断食"""
    record = IntermittentFasting.query.get_or_404(record_id)
    
    if record.user_id != current_user.id:
        flash('无权操作', 'error')
        return redirect(url_for('fasting'))
    
    record.end_time = datetime.now()
    record.status = 'completed'
    if record.start_time:
        record.duration = (record.end_time - record.start_time).total_seconds() / 3600
    
    db.session.commit()
    
    flash(f'轻断食完成！持续了 {round(record.duration, 1)} 小时', 'success')
    return redirect(url_for('fasting'))


# ==================== AI分析 ====================

@app.route('/ai-analysis')
@login_required
def ai_analysis():
    """AI健康分析页面"""
    # 获取近期数据
    last_7_days = date.today() - timedelta(days=7)
    
    food_records = FoodRecord.query.filter(
        FoodRecord.user_id == current_user.id,
        FoodRecord.date >= last_7_days
    ).all()
    
    exercise_records = ExerciseRecord.query.filter(
        ExerciseRecord.user_id == current_user.id,
        ExerciseRecord.date >= last_7_days
    ).all()
    
    sleep_records = SleepRecord.query.filter(
        SleepRecord.user_id == current_user.id,
        SleepRecord.date >= last_7_days
    ).all()
    
    # 计算统计数据
    stats = {
        'avg_calories': 0,
        'avg_protein': 0,
        'avg_carbs': 0,
        'avg_fat': 0,
        'total_exercise_minutes': 0,
        'total_calories_burned': 0,
        'avg_sleep_duration': 0,
        'avg_sleep_quality': 0
    }
    
    if food_records:
        stats['avg_calories'] = sum(r.calories for r in food_records) / len(food_records)
        stats['avg_protein'] = sum(r.protein for r in food_records) / len(food_records)
        stats['avg_carbs'] = sum(r.carbs for r in food_records) / len(food_records)
        stats['avg_fat'] = sum(r.fat for r in food_records) / len(food_records)
    
    if exercise_records:
        stats['total_exercise_minutes'] = sum(r.duration for r in exercise_records)
        stats['total_calories_burned'] = sum(r.calories_burned for r in exercise_records)
    
    if sleep_records:
        stats['avg_sleep_duration'] = sum(r.duration for r in sleep_records if r.duration) / len(sleep_records)
        stats['avg_sleep_quality'] = sum(r.quality for r in sleep_records if r.quality) / len(sleep_records)
    
    # 生成AI分析
    analysis = generate_ai_analysis(stats)
    
    # 寿命增加
    life_bonus, tips = calculate_life_expectancy()
    
    return render_template('ai_analysis.html',
                         stats=stats,
                         analysis=analysis,
                         life_bonus=life_bonus,
                         tips=tips,
                         current_user=current_user)


def generate_ai_analysis(stats):
    """生成AI健康分析"""
    analysis = []
    
    # 热量分析
    if stats['avg_calories'] > 0:
        if stats['avg_calories'] > current_user.target_calories * 1.2:
            analysis.append({
                'type': 'warning',
                'title': '热量摄入偏高',
                'content': f'您近期平均每日摄入 {stats["avg_calories"]:.0f} kcal，超过目标 {current_user.target_calories:.0f} kcal。建议减少高热量食物，增加蔬菜水果比例。'
            })
        elif stats['avg_calories'] < current_user.target_calories * 0.8:
            analysis.append({
                'type': 'info',
                'title': '热量摄入偏低',
                'content': f'您近期平均每日摄入 {stats["avg_calories"]:.0f} kcal，略低于目标。建议适当增加优质蛋白和健康脂肪的摄入。'
            })
        else:
            analysis.append({
                'type': 'success',
                'title': '热量摄入良好',
                'content': f'您近期平均每日摄入 {stats["avg_calories"]:.0f} kcal，接近目标 {current_user.target_calories:.0f} kcal。继续保持！'
            })
    
    # 蛋白质分析
    if stats['avg_protein'] > 0:
        protein_ideal = current_user.weight * 1.2  # 每公斤体重1.2g蛋白质
        if stats['avg_protein'] < protein_ideal * 0.8:
            analysis.append({
                'type': 'info',
                'title': '蛋白质摄入不足',
                'content': f'建议增加蛋白质摄入，当前约 {stats["avg_protein"]:.0f}g，建议至少 {protein_ideal:.0f}g。可多吃鸡胸肉、鱼虾、蛋奶和豆制品。'
            })
    
    # 运动分析
    if stats['total_exercise_minutes'] > 0:
        weekly_mins = stats['total_exercise_minutes']
        if weekly_mins >= 150:
            analysis.append({
                'type': 'success',
                'title': '运动量充足',
                'content': f'本周已运动 {weekly_mins:.0f} 分钟，达到WHO推荐的每周150分钟标准。继续加油！'
            })
        else:
            analysis.append({
                'type': 'info',
                'title': '建议增加运动',
                'content': f'本周已运动 {weekly_mins:.0f} 分钟，建议再增加 {150 - weekly_mins:.0f} 分钟达到标准。'
            })
    else:
        analysis.append({
            'type': 'warning',
            'title': '运动记录缺失',
            'content': '本周暂无运动记录。开始记录您的运动吧，哪怕每天散步30分钟也对健康大有裨益！'
        })
    
    # 睡眠分析
    if stats['avg_sleep_duration'] > 0:
        if stats['avg_sleep_duration'] < 6:
            analysis.append({
                'type': 'warning',
                'title': '睡眠不足',
                'content': f'您的平均睡眠时间为 {stats["avg_sleep_duration"]:.1f} 小时，低于推荐的7-9小时。睡眠不足会影响代谢和免疫力。'
            })
        elif stats['avg_sleep_duration'] > 9:
            analysis.append({
                'type': 'info',
                'title': '睡眠时间偏多',
                'content': f'您的平均睡眠时间为 {stats["avg_sleep_duration"]:.1f} 小时，过多睡眠可能反而影响健康。'
            })
        else:
            analysis.append({
                'type': 'success',
                'title': '睡眠质量良好',
                'content': f'您的平均睡眠时间为 {stats["avg_sleep_duration"]:.1f} 小时，符合推荐标准。'
            })
    
    return analysis


# ==================== 健康新闻 ====================

@app.route('/news')
def news():
    """健康新闻页面"""
    category = request.args.get('category')
    
    query = HealthNews.query
    if category:
        query = query.filter_by(category=category)
    
    news_items = query.order_by(HealthNews.published_at.desc()).limit(20).all()
    
    return render_template('news.html', news_items=news_items, current_category=category)


# ==================== 个人设置 ====================

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """个人资料设置"""
    if request.method == 'POST':
        current_user.age = int(request.form.get('age', 25))
        current_user.gender = request.form.get('gender', 'male')
        current_user.height = float(request.form.get('height', 170))
        current_user.weight = float(request.form.get('weight', 65))
        current_user.activity_level = request.form.get('activity_level', 'moderate')
        current_user.goal = request.form.get('goal', 'maintain')
        
        # 计算新的目标热量
        bmr = current_user.get_bmr()
        tdee = current_user.get_tdee()
        
        if current_user.goal == 'lose':
            current_user.target_calories = tdee - 500
        elif current_user.goal == 'gain':
            current_user.target_calories = tdee + 300
        else:
            current_user.target_calories = tdee
        
        # 营养素目标
        current_user.target_protein = current_user.weight * 1.5  # 每公斤1.5g蛋白质
        current_user.target_carbs = current_user.target_calories * 0.5 / 4  # 50%碳水
        current_user.target_fat = current_user.target_calories * 0.25 / 9  # 25%脂肪
        
        db.session.commit()
        flash('个人资料已更新！', 'success')
        return redirect(url_for('profile'))
    
    return render_template('profile.html')


# ==================== API接口 ====================

@app.route('/api/stats/daily')
@login_required
def api_daily_stats():
    """每日统计数据API"""
    target_date = request.args.get('date', date.today().isoformat())
    try:
        target = datetime.strptime(target_date, '%Y-%m-%d').date()
    except:
        target = date.today()
    
    food_records = FoodRecord.query.filter_by(user_id=current_user.id, date=target).all()
    exercise_records = ExerciseRecord.query.filter_by(user_id=current_user.id, date=target).all()
    
    calories_consumed = sum(r.calories for r in food_records)
    calories_burned = sum(r.calories_burned for r in exercise_records)
    net_calories = calories_consumed - calories_burned
    
    return jsonify({
        'date': target.isoformat(),
        'calories_consumed': round(calories_consumed, 1),
        'calories_burned': round(calories_burned, 1),
        'net_calories': round(net_calories, 1),
        'target_calories': current_user.target_calories,
        'protein': round(sum(r.protein for r in food_records), 1),
        'carbs': round(sum(r.carbs for r in food_records), 1),
        'fat': round(sum(r.fat for r in food_records), 1)
    })


def get_today_stats():
    """获取今日统计"""
    food_records = FoodRecord.query.filter_by(user_id=current_user.id, date=date.today()).all()
    exercise_records = ExerciseRecord.query.filter_by(user_id=current_user.id, date=date.today()).all()
    
    return {
        'calories_consumed': sum(r.calories for r in food_records),
        'calories_burned': sum(r.calories_burned for r in exercise_records),
        'protein': sum(r.protein for r in food_records),
        'carbs': sum(r.carbs for r in food_records),
        'fat': sum(r.fat for r in food_records)
    }


# ==================== 启动应用 ====================

if __name__ == '__main__':
    with app.app_context():
        init_database()
    app.run(debug=True, host='0.0.0.0', port=5000)
