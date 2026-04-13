# -*- coding: utf-8 -*-
"""
熵食源 - 在线食物营养分析APP
主应用文件
"""
from __future__ import unicode_literals

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
import feedparser

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


@app.route('/api/init-foods')
@login_required
def api_init_foods():
    """手动初始化食物数据库（用于修复数据问题）"""
    try:
        # 清空并重新初始化
        Food.query.delete()
        db.session.commit()
        init_foods()
        return jsonify({'success': True, 'message': f'食物数据库已初始化，共 {Food.query.count()} 种食物'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/refresh-news')
@login_required
def api_refresh_news():
    """手动刷新健康新闻数据"""
    try:
        # 清空并重新初始化
        HealthNews.query.delete()
        db.session.commit()
        init_news()
        return jsonify({'success': True, 'message': f'健康新闻已刷新，共 {HealthNews.query.count()} 条'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


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
    """从 RSS 源实时抓取健康新闻"""
    news_items = []
    news_count = 0
    categories = ['nutrition', 'exercise', 'sleep', 'research']
    
    # 从配置的 RSS 源抓取新闻
    for source_url in app.config.get('NEWS_SOURCES', []):
        try:
            feed = feedparser.parse(source_url)
            if feed.entries:
                for entry in feed.entries[:5]:  # 每个源最多取5条
                    title = entry.get('title', '无标题')
                    summary = entry.get('summary', entry.get('description', '暂无摘要'))
                    # 清理 HTML 标签
                    summary = re.sub(r'<[^>]+>', '', summary)
                    summary = summary[:200] + '...' if len(summary) > 200 else summary
                    
                    # 尝试从标题推断分类
                    title_lower = title.lower()
                    if any(k in title_lower for k in ['营养', '饮食', '食物', '维生素', '蛋白质']):
                        category = 'nutrition'
                    elif any(k in title_lower for k in ['运动', '锻炼', '跑步', '健身', '训练']):
                        category = 'exercise'
                    elif any(k in title_lower for k in ['睡眠', '失眠', '休息']):
                        category = 'sleep'
                    else:
                        category = random.choice(categories)
                    
                    # 解析发布时间
                    published_at = datetime.now()
                    if hasattr(entry, 'published_parsed') and entry.published_parsed:
                        try:
                            from time import mktime
                            published_at = datetime.fromtimestamp(mktime(entry.published_parsed))
                        except:
                            pass
                    
                    news_items.append({
                        'title': title[:100],
                        'summary': summary,
                        'source': feed.feed.get('title', source_url)[:50],
                        'source_url': entry.get('link', ''),
                        'category': category,
                        'published_at': published_at
                    })
                    news_count += 1
        except Exception as e:
            print(f"抓取 RSS 源失败 {source_url}: {e}")
            continue
    
    # 如果没有抓取到新闻，使用备用静态数据
    if not news_items:
        print("RSS 源不可用，使用备用新闻数据")
        fallback_news = app.config.get('FALLBACK_NEWS', [])
        for i, news in enumerate(fallback_news):
            news_items.append({
                'title': news['title'],
                'summary': f"最新健康资讯：{news['title']}。来源：{news['source']}",
                'source': news['source'],
                'source_url': '',
                'category': news['category'],
                'published_at': datetime.now() - timedelta(days=i * 2)
            })
    
    # 写入数据库
    for news in news_items:
        hn = HealthNews(**news)
        db.session.add(hn)
    db.session.commit()
    
    print(f"新闻初始化完成，共抓取 {len(news_items)} 条新闻")


def fetch_latest_news():
    """实时抓取最新新闻（不清理旧数据）"""
    news_items = []
    categories = ['nutrition', 'exercise', 'sleep', 'research']
    
    for source_url in app.config.get('NEWS_SOURCES', []):
        try:
            feed = feedparser.parse(source_url)
            if feed.entries:
                for entry in feed.entries[:10]:
                    title = entry.get('title', '无标题')
                    summary = entry.get('summary', entry.get('description', '暂无摘要'))
                    summary = re.sub(r'<[^>]+>', '', summary)
                    summary = summary[:200] + '...' if len(summary) > 200 else summary
                    
                    title_lower = title.lower()
                    if any(k in title_lower for k in ['营养', '饮食', '食物', '维生素', '蛋白质']):
                        category = 'nutrition'
                    elif any(k in title_lower for k in ['运动', '锻炼', '跑步', '健身', '训练']):
                        category = 'exercise'
                    elif any(k in title_lower for k in ['睡眠', '失眠', '休息']):
                        category = 'sleep'
                    else:
                        category = random.choice(categories)
                    
                    published_at = datetime.now()
                    if hasattr(entry, 'published_parsed') and entry.published_parsed:
                        try:
                            from time import mktime
                            published_at = datetime.fromtimestamp(mktime(entry.published_parsed))
                        except:
                            pass
                    
                    news_items.append({
                        'title': title[:100],
                        'summary': summary,
                        'source': feed.feed.get('title', source_url)[:50],
                        'source_url': entry.get('link', ''),
                        'category': category,
                        'published_at': published_at
                    })
        except Exception as e:
            print(f"抓取失败: {source_url} - {e}")
            continue
    
    return news_items if news_items else None


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
            tips.append('[OK] 您的BMI在健康范围内')
        elif 25 <= bmi <= 29.9:
            bonus_years += 1.0
            tips.append('[!] 适当减重可增加寿命')
        else:
            bonus_years += 0.5
            tips.append('[!] 建议咨询医生制定减重计划')
        
        # 运动习惯
        recent_exercises = ExerciseRecord.query.filter(
            ExerciseRecord.user_id == current_user.id,
            ExerciseRecord.date >= date.today() - timedelta(days=30)
        ).count()
        
        if recent_exercises >= 12:
            bonus_years += 3.0
            tips.append('[OK] 您的运动习惯良好')
        elif recent_exercises >= 4:
            bonus_years += 1.5
            tips.append('[!] 增加运动频率可延年益寿')
        else:
            tips.append('[!] 建议每周至少运动3次')
        
        # 饮食记录
        recent_foods = FoodRecord.query.filter(
            FoodRecord.user_id == current_user.id,
            FoodRecord.date >= date.today() - timedelta(days=30)
        ).count()
        
        if recent_foods >= 60:
            bonus_years += 1.5
            tips.append('[OK] 您的饮食记录习惯很好')
        
        # 睡眠质量
        avg_sleep = db.session.query(db.func.avg(SleepRecord.duration)).filter(
            SleepRecord.user_id == current_user.id,
            SleepRecord.date >= date.today() - timedelta(days=30)
        ).scalar()
        
        if avg_sleep and 7 <= avg_sleep <= 9:
            bonus_years += 2.0
            tips.append('[OK] 您的睡眠时间充足')
        elif avg_sleep and avg_sleep < 7:
            tips.append('[!] 建议保证7-9小时睡眠')
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


@app.route('/api/recognize-food', methods=['POST'])
@login_required
def api_recognize_food():
    """
    食物图像识别API
    优先使用百度AI识别，失败时返回本地数据库匹配结果
    """
    try:
        data = request.get_json()
        image_base64 = data.get('image', '')
        
        app.logger.info(f'收到图片数据，长度: {len(image_base64) if image_base64 else 0}')
        
        if not image_base64:
            return jsonify({'success': False, 'message': '没有图片数据'})
        
        results = []
        
        # 使用本地图片识别（基于颜色特征，支持机器学习）
        app.logger.info('开始使用本地图片识别...')
        try:
            from local_image_recognition import recognize_food_local, extract_image_features
            from baidu_ai import get_food_nutrition
            
            # 先提取特征看看
            features = extract_image_features(image_base64)
            app.logger.info(f'图片特征: {features}')
            
            # 传入用户ID和数据库会话，支持个性化识别
            local_results = recognize_food_local(
                image_base64, 
                top_n=5, 
                user_id=current_user.id if current_user.is_authenticated else None,
                db_session=db.session
            )
            app.logger.info(f'本地识别结果: {local_results}')
            
            if local_results:
                app.logger.info(f'开始处理 {len(local_results)} 个识别结果')
                for item in local_results:
                    try:
                        food_name = item['name']
                        confidence = item['confidence']
                        source = item.get('source', 'builtin')
                        app.logger.info(f'处理食物: {food_name}, 置信度: {confidence}, 来源: {source}')
                        nutrition = get_food_nutrition(food_name)
                        app.logger.info(f'营养数据: {nutrition}')
                        
                        result_item = {
                            'name': food_name,
                            'confidence': confidence,
                            'calories': nutrition.get('calories', 0),
                            'protein': nutrition.get('protein', 0),
                            'carbs': nutrition.get('carbs', 0),
                            'fat': nutrition.get('fat', 0),
                            'category': nutrition.get('category', '其他'),
                            'source': source
                        }
                        
                        # 如果是用户学习的数据，添加标记
                        if source == 'user_learned':
                            result_item['learned'] = True
                            result_item['confirmed_count'] = item.get('confirmed_count', 1)
                        
                        results.append(result_item)
                        app.logger.info(f'已添加 {food_name} 到结果')
                    except Exception as item_error:
                        app.logger.error(f'处理 {item} 时出错: {item_error}')
            else:
                app.logger.warning('本地识别返回空结果')
        except Exception as e:
            app.logger.error(f'本地识别失败: {e}')
            import traceback
            app.logger.error(traceback.format_exc())
        
        # 如果本地识别失败或结果太少，返回备选食物
        if not results:
            from baidu_ai import FOOD_NUTRITION_DB
            # 提供各分类的常见食物，方便用户选择
            fallback_foods = [
                # 主食类
                ('米饭', '主食'), ('面条', '主食'), ('馒头', '主食'), ('面包', '主食'), ('包子', '主食'),
                # 蔬菜类
                ('西红柿', '蔬菜'), ('胡萝卜', '蔬菜'), ('黄瓜', '蔬菜'), ('白菜', '蔬菜'), ('土豆', '蔬菜'),
                # 肉类
                ('猪肉', '肉类'), ('鸡肉', '肉类'), ('牛肉', '肉类'), ('鸡蛋', '蛋类'), ('豆腐', '蔬菜'),
                # 水果
                ('苹果', '水果'), ('香蕉', '水果'), ('橙子', '水果'), ('西瓜', '水果'), ('葡萄', '水果'),
                # 海鲜
                ('虾', '海鲜'), ('鱼', '海鲜'), ('螃蟹', '海鲜'), ('鸡蛋', '蛋类'), ('牛奶', '饮品')
            ]
            for food_name, category in fallback_foods[:8]:
                nutrition = FOOD_NUTRITION_DB.get(food_name, {})
                results.append({
                    'name': food_name,
                    'confidence': 30,
                    'calories': nutrition.get('calories', 100),
                    'protein': nutrition.get('protein', 3),
                    'carbs': nutrition.get('carbs', 15),
                    'fat': nutrition.get('fat', 2),
                    'category': nutrition.get('category', category),
                    'source': 'fallback',
                    'desc': '未能准确识别，请从下方选择或手动搜索'
                })
        
        app.logger.info(f'返回结果数量: {len(results)}, 内容: {results}')
        
        return jsonify({
            'success': True,
            'results': results
        })
        
    except Exception as e:
        import traceback
        app.logger.error(f'食物识别失败: {e}')
        app.logger.error(traceback.format_exc())
        
        # 即使出错也返回备选结果，不让用户看到错误
        try:
            from baidu_ai import FOOD_NUTRITION_DB
            fallback_results = []
            common_vegetables = ['西红柿', '胡萝卜', '黄瓜', '白菜', '土豆', '茄子', '青椒', '洋葱', '西兰花', '菠菜']
            for food_name in common_vegetables[:5]:
                nutrition = FOOD_NUTRITION_DB.get(food_name, {})
                fallback_results.append({
                    'name': food_name,
                    'confidence': 30,
                    'calories': nutrition.get('calories', 100),
                    'protein': nutrition.get('protein', 3),
                    'carbs': nutrition.get('carbs', 15),
                    'fat': nutrition.get('fat', 2),
                    'category': nutrition.get('category', '蔬菜'),
                    'source': 'fallback',
                    'desc': '未能准确识别，请从下方选择或手动搜索'
                })
            return jsonify({
                'success': True,
                'results': fallback_results
            })
        except:
            return jsonify({
                'success': False,
                'message': '识别服务暂时不可用，请手动搜索'
            })


@app.route('/api/foods/<int:food_id>')
@login_required
def api_food_detail(food_id):
    """食物详情API"""
    food = Food.query.get_or_404(food_id)
    return jsonify(food.to_dict())


@app.route('/api/learn-food', methods=['POST'])
@login_required
def api_learn_food():
    """
    学习用户确认的食物图片特征
    用户确认识别结果后，保存图片特征用于下次识别
    """
    try:
        data = request.get_json()
        image_base64 = data.get('image', '')
        food_name = data.get('food_name', '')
        food_category = data.get('food_category', '')
        
        if not image_base64 or not food_name:
            return jsonify({'success': False, 'message': '缺少必要参数'})
        
        # 保存图片特征
        from local_image_recognition import save_food_image_feature
        success = save_food_image_feature(
            image_base64,
            food_name,
            food_category,
            current_user.id,
            db.session
        )
        
        if success:
            return jsonify({
                'success': True,
                'message': f'已学习食物特征: {food_name}'
            })
        else:
            return jsonify({
                'success': False,
                'message': '保存特征失败'
            })
            
    except Exception as e:
        app.logger.error(f'学习食物特征失败: {e}')
        import traceback
        app.logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'message': '服务器错误'
        })


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


@app.route('/admin/sync-foods')
@login_required
def admin_sync_foods():
    """同步食物数据到数据库（临时管理功能）"""
    # 检查是否是管理员（这里简单判断，实际应该使用角色权限）
    if current_user.username != 'admin' and not current_user.is_admin:
        return jsonify({'success': False, 'message': '无权访问'}), 403
    
    try:
        from baidu_ai import FOOD_NUTRITION_DB
        
        # 删除系统预设的食物
        Food.query.filter(Food.is_custom == False).delete()
        db.session.commit()
        
        # 添加新食物
        added_count = 0
        skipped_count = 0
        
        for name, nutrition in FOOD_NUTRITION_DB.items():
            # 检查是否已存在
            existing = Food.query.filter_by(name=name).first()
            if existing:
                skipped_count += 1
                continue
            
            food = Food(
                name=name,
                calories=nutrition.get('calories', 0),
                protein=nutrition.get('protein', 0),
                carbs=nutrition.get('carbs', 0),
                fat=nutrition.get('fat', 0),
                category=nutrition.get('category', '其他'),
                is_custom=False
            )
            db.session.add(food)
            added_count += 1
            
            # 每100条提交一次
            if added_count % 100 == 0:
                db.session.commit()
        
        db.session.commit()
        
        total = Food.query.count()
        return jsonify({
            'success': True,
            'message': f'同步完成！新增 {added_count} 种，跳过 {skipped_count} 种，数据库总计 {total} 种'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'同步失败: {str(e)}'}), 500


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
        # 支持JSON和表单两种格式
        if request.is_json:
            data = request.get_json()
            food_name = data.get('food_name')
            calories = float(data.get('calories', 0))
            protein = float(data.get('protein', 0))
            carbs = float(data.get('carbs', 0))
            fat = float(data.get('fat', 0))
            quantity = float(data.get('serving_size', 100))
            input_method = data.get('input_method', 'text')
            
            # 支持批量添加（语音输入）
            foods = data.get('foods', [])
            if foods:
                for item in foods:
                    record = FoodRecord(
                        user_id=current_user.id,
                        food_name=item.get('name', '未知'),
                        quantity=item.get('quantity', 1),
                        meal_type='snack',
                        calories=float(item.get('calories', 0)),
                        protein=float(item.get('protein', 0)),
                        carbs=float(item.get('carbs', 0)),
                        fat=float(item.get('fat', 0)),
                        input_method=input_method
                    )
                    db.session.add(record)
                db.session.commit()
                return jsonify({'success': True, 'message': '批量添加成功'})
        else:
            food_id = request.form.get('food_id')
            food_name = request.form.get('food_name')
            quantity = float(request.form.get('quantity', 100))
            meal_type = request.form.get('meal_type', 'snack')
            
            food = Food.query.get(food_id) if food_id else None
            
            # 优先使用用户手动输入的营养数据，否则尝试从食物库获取
            user_calories = float(request.form.get('calories', 0) or 0)
            user_protein = float(request.form.get('protein', 0) or 0)
            user_carbs = float(request.form.get('carbs', 0) or 0)
            user_fat = float(request.form.get('fat', 0) or 0)
            
            if user_calories > 0 or user_protein > 0 or user_carbs > 0 or user_fat > 0:
                # 用户手动输入了营养数据
                calories = user_calories
                protein = user_protein
                carbs = user_carbs
                fat = user_fat
            elif food:
                # 从食物库获取营养数据
                calories = food.calories * quantity / 100
                protein = food.protein * quantity / 100
                carbs = food.carbs * quantity / 100
                fat = food.fat * quantity / 100
            else:
                # 尝试模糊匹配食物库
                matched_food = Food.query.filter(Food.name.like(f'%' + food_name + '%')).first()
                if matched_food:
                    calories = matched_food.calories * quantity / 100
                    protein = matched_food.protein * quantity / 100
                    carbs = matched_food.carbs * quantity / 100
                    fat = matched_food.fat * quantity / 100
                else:
                    # 无法获取营养数据，使用0并提示用户
                    flash('请从搜索结果中选择食物，或手动输入营养数据', 'warning')
                    return redirect(url_for('add_diet'))
            
            record = FoodRecord(
                user_id=current_user.id,
                food_id=food_id or (matched_food.id if 'matched_food' in dir() else None),
                food_name=food_name or (food.name if food else '未知食物'),
                quantity=quantity,
                meal_type=meal_type,
                calories=calories,
                protein=protein,
                carbs=carbs,
                fat=fat,
                input_method=request.form.get('input_method', 'text')
            )
            
            db.session.add(record)
            db.session.commit()
            
            flash('饮食记录已添加！', 'success')
            return redirect(url_for('diet'))
        
        # JSON单条记录
        record = FoodRecord(
            user_id=current_user.id,
            food_name=food_name or '未知食物',
            quantity=quantity,
            meal_type='snack',
            calories=calories,
            protein=protein,
            carbs=carbs,
            fat=fat,
            input_method=input_method
        )
        
        db.session.add(record)
        db.session.commit()
        
        return jsonify({'success': True, 'message': '添加成功'})
    
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


# ==================== 拍照识别食物 ====================

@app.route('/food/camera')
@login_required
def food_camera():
    """拍照识别食物页面"""
    return render_template('food_camera.html')


# ==================== 语音输入食物 ====================

@app.route('/food/voice')
@login_required
def food_voice():
    """语音输入食物页面"""
    return render_template('food_voice.html')


# ==================== 文字输入食物 ====================

@app.route('/food/text')
@login_required
def food_text():
    """文字输入食物页面"""
    # 获取食物库
    foods = Food.query.order_by(Food.name).all()
    
    # 获取今日已添加的食物
    today = date.today()
    today_records = FoodRecord.query.filter_by(
        user_id=current_user.id,
        date=today
    ).order_by(FoodRecord.created_at.desc()).all() if hasattr(FoodRecord, 'created_at') else []
    
    today_foods = [{'name': r.food_name, 'portion': r.quantity, 'calories': r.calories} for r in today_records]
    
    # 转换为JSON格式
    foods_json = json.dumps([{
        'id': f.id,
        'name': f.name,
        'name_en': getattr(f, 'name_en', ''),
        'calories': f.calories,
        'protein': f.protein,
        'carbs': f.carbs,
        'fat': f.fat
    } for f in foods], ensure_ascii=False)
    
    return render_template('food_text.html', 
                         foods=foods,
                         foods_json=foods_json,
                         today_foods=today_foods)


# ==================== 条形码扫描 ====================

@app.route('/food/barcode')
@login_required
def food_barcode():
    """条形码扫描页面"""
    # 获取扫描历史
    history = db.session.query(
        FoodRecord.food_name,
        FoodRecord.calories,
        db.func.count(FoodRecord.id).label('count')
    ).filter(
        FoodRecord.user_id == current_user.id,
        FoodRecord.food_name.like('%#%')  # 包含条形码标记
    ).group_by(FoodRecord.food_name, FoodRecord.calories).order_by(
        db.func.count(FoodRecord.id).desc()
    ).limit(10).all()
    
    scan_history = [{'name': h[0].split('#')[0], 'barcode': h[0].split('#')[1] if '#' in h[0] else '', 'calories': h[1]} for h in history]
    
    return render_template('food_barcode.html', history=scan_history)


@app.route('/api/diet/search')
@login_required
def api_diet_search():
    """搜索食物用于饮食记录"""
    query = request.args.get('q', '')
    foods = Food.query.filter(Food.name.contains(query)).limit(10).all()
    return jsonify([f.to_dict() for f in foods])


@app.route('/api/diet/update/<int:record_id>', methods=['POST'])
@login_required
def api_diet_update(record_id):
    """更新饮食记录"""
    record = FoodRecord.query.filter_by(id=record_id, user_id=current_user.id).first()
    if not record:
        return jsonify({'success': False, 'message': '记录不存在'})
    
    data = request.get_json()
    record.food_name = data.get('food_name', record.food_name)
    record.quantity = float(data.get('quantity', record.quantity))
    record.calories = float(data.get('calories', record.calories))
    record.protein = float(data.get('protein', record.protein))
    record.carbs = float(data.get('carbs', record.carbs))
    record.fat = float(data.get('fat', record.fat))
    record.meal_type = data.get('meal_type', record.meal_type)
    
    db.session.commit()
    return jsonify({'success': True, 'message': '修改成功'})


@app.route('/api/diet/delete/<int:record_id>', methods=['POST'])
@login_required
def api_diet_delete(record_id):
    """删除饮食记录"""
    record = FoodRecord.query.filter_by(id=record_id, user_id=current_user.id).first()
    if not record:
        return jsonify({'success': False, 'message': '记录不存在'})
    
    db.session.delete(record)
    db.session.commit()
    return jsonify({'success': True, 'message': '删除成功'})


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


@app.route('/exercise/edit/<int:record_id>', methods=['GET', 'POST'])
@login_required
def edit_exercise(record_id):
    """编辑运动记录"""
    record = ExerciseRecord.query.get_or_404(record_id)

    if record.user_id != current_user.id:
        flash('无权操作', 'error')
        return redirect(url_for('exercise'))

    if request.method == 'POST':
        record.exercise_name = request.form.get('exercise_name')
        record.duration = int(request.form.get('duration', 30))
        record.intensity = request.form.get('intensity', 'moderate')

        # 重新计算热量
        exercise = Exercise.query.get(record.exercise_id) if record.exercise_id else None
        if exercise:
            record.calories_burned = exercise.get_calories_burned(current_user.weight, record.duration)
        else:
            record.calories_burned = record.duration * 5

        db.session.commit()
        flash('运动记录已更新！', 'success')
        return redirect(url_for('exercise'))

    exercises = Exercise.query.order_by(Exercise.name).all()
    return render_template('edit_exercise.html', record=record, exercises=exercises)


@app.route('/exercise/delete/<int:record_id>', methods=['POST'])
@login_required
def delete_exercise(record_id):
    """删除运动记录"""
    record = ExerciseRecord.query.get_or_404(record_id)

    if record.user_id != current_user.id:
        flash('无权操作', 'error')
        return redirect(url_for('exercise'))

    db.session.delete(record)
    db.session.commit()
    flash('运动记录已删除！', 'success')
    return redirect(url_for('exercise'))


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


@app.route('/sleep/edit/<int:record_id>', methods=['GET', 'POST'])
@login_required
def edit_sleep(record_id):
    """编辑睡眠记录"""
    record = SleepRecord.query.get_or_404(record_id)

    if record.user_id != current_user.id:
        flash('无权操作', 'error')
        return redirect(url_for('sleep'))

    if request.method == 'POST':
        try:
            bed_time_str = request.form.get('bed_time')
            wake_time_str = request.form.get('wake_time')

            if bed_time_str and wake_time_str:
                record.bed_time = datetime.strptime(bed_time_str, '%Y-%m-%dT%H:%M')
                record.wake_time = datetime.strptime(wake_time_str, '%Y-%m-%dT%H:%M')
                record.duration = (record.wake_time - record.bed_time).total_seconds() / 3600
            else:
                record.duration = float(request.form.get('duration', 7))

            record.quality = int(request.form.get('quality', 7))
            record.caffeine_before_bed = bool(request.form.get('caffeine'))
            record.heavy_meal_before_bed = bool(request.form.get('heavy_meal'))
            record.notes = request.form.get('notes')

            db.session.commit()
            flash('睡眠记录已更新！', 'success')
        except Exception as e:
            flash(f'更新失败：{str(e)}', 'error')

        return redirect(url_for('sleep'))

    return render_template('sleep_edit.html', record=record)


@app.route('/sleep/delete/<int:record_id>', methods=['POST'])
@login_required
def delete_sleep(record_id):
    """删除睡眠记录"""
    record = SleepRecord.query.get_or_404(record_id)

    if record.user_id != current_user.id:
        flash('无权操作', 'error')
        return redirect(url_for('sleep'))

    db.session.delete(record)
    db.session.commit()
    flash('睡眠记录已删除！', 'success')
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
    
    # 获取健康新闻
    news_items = HealthNews.query.order_by(HealthNews.published_at.desc()).limit(8).all()
    
    return render_template('ai_analysis.html',
                         stats=stats,
                         analysis=analysis,
                         life_bonus=life_bonus,
                         tips=tips,
                         news_items=news_items,
                         current_user=current_user)







@app.route('/export_report')
@login_required
def export_report():
    """导出健康报告为Word文档"""
    # 获取近期数据
    last_30_days = date.today() - timedelta(days=30)
    
    food_records = FoodRecord.query.filter(
        FoodRecord.user_id == current_user.id,
        FoodRecord.date >= last_30_days
    ).all()
    
    exercise_records = ExerciseRecord.query.filter(
        ExerciseRecord.user_id == current_user.id,
        ExerciseRecord.date >= last_30_days
    ).all()
    
    sleep_records = SleepRecord.query.filter(
        SleepRecord.user_id == current_user.id,
        SleepRecord.date >= last_30_days
    ).all()
    
    # 计算统计数据
    total_calories = sum(r.calories for r in food_records) if food_records else 0
    total_protein = sum(r.protein for r in food_records) if food_records else 0
    total_carbs = sum(r.carbs for r in food_records) if food_records else 0
    total_fat = sum(r.fat for r in food_records) if food_records else 0
    total_exercise_minutes = sum(r.duration for r in exercise_records) if exercise_records else 0
    total_calories_burned = sum(r.calories_burned for r in exercise_records) if exercise_records else 0
    avg_sleep = sum(r.duration for r in sleep_records if r.duration) / len(sleep_records) if sleep_records else 0
    
    # 寿命增加计算
    life_bonus, tips = calculate_life_expectancy()
    
    # 生成Word文件
    from docx import Document
    from docx.shared import Pt, RGBColor
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.enum.table import WD_TABLE_ALIGNMENT
    
    # 创建Word文档
    doc = Document()
    
    # 中文内容定义（避免f-string编码问题）
    REPORT_TITLE = '熵食源健康报告'
    SUBTITLE = f'{current_user.username} \u4e2a\u6027\u5316\u5065\u5eb7\u5206\u6790'  # 个性化健康分析
    DATE_LABEL = f'\u62a5\u544a\u751f\u6210\u65e5\u671f\uff1a{date.today().strftime("%Y-%m-%d")}'  # 报告生成日期
    
    # 标题
    title = doc.add_heading(REPORT_TITLE, 0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    # 副标题
    subtitle = doc.add_paragraph()
    subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = subtitle.add_run(SUBTITLE)
    run.font.size = Pt(16)
    
    # 日期
    date_para = doc.add_paragraph()
    date_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = date_para.add_run(DATE_LABEL)
    run.font.size = Pt(10)
    
    doc.add_paragraph()
    
    # 一、寿命预测
    LIFE_HEADING = '\u4e00\u3001\u5bff\u547d\u9884\u6d4b'  # 一、寿命预测
    LIFE_TEXT1 = '\u6839\u636e\u60a8\u7684\u5065\u5eb7\u751f\u6d3b\u65b9\u5f0f\uff0c\u9884\u8ba1\u53ef\u5ef6\u957f\u5bff\u547d'  # 根据您的健康生活方式，预计可延长寿命
    LIFE_TEXT2 = f'+{life_bonus} \u5e74'  # 年
    
    doc.add_heading(LIFE_HEADING, level=1)
    life_para = doc.add_paragraph()
    life_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = life_para.add_run(LIFE_TEXT1)
    run.font.size = Pt(14)
    
    life_num = doc.add_paragraph()
    life_num.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = life_num.add_run(LIFE_TEXT2)
    run.font.size = Pt(48)
    run.font.color.rgb = RGBColor(108, 92, 231)
    
    doc.add_paragraph()
    
    # 二、营养摄入统计
    NUTRITION_HEADING = '\u4e8c\u3001\u8fd130\u5929\u8425\u517b\u6444\u5165\u7edf\u8ba1'  # 二、近30天营养摄入统计
    HEADERS = ['\u9879\u76ee', '\u6570\u503c', '\u8bf4\u660e']  # 项目、数值、说明
    
    doc.add_heading(NUTRITION_HEADING, level=1)
    table1 = doc.add_table(rows=5, cols=3)
    table1.style = 'Table Grid'
    table1.alignment = WD_TABLE_ALIGNMENT.CENTER
    
    for i, header in enumerate(HEADERS):
        cell = table1.rows[0].cells[i]
        cell.text = header
        cell.paragraphs[0].runs[0].font.bold = True
    
    # 使用英文标签避免编码问题
    data1 = [
        ('\u603b\u70ed\u91cf\u6444\u5165', f'{total_calories:.0f} kcal', f'\u65e5\u5747 {total_calories/30:.0f} kcal'),  # 总热量摄入、日均
        ('\u603b\u86cb\u767d\u8d28\u6444\u5165', f'{total_protein:.1f} g', f'\u65e5\u5747 {total_protein/30:.1f} g'),  # 总蛋白质摄入
        ('\u603b\u78b3\u6c34\u6444\u5165', f'{total_carbs:.1f} g', f'\u65e5\u5747 {total_carbs/30:.1f} g'),  # 总碳水摄入
        ('\u603b\u8102\u80aa\u6444\u5165', f'{total_fat:.1f} g', f'\u65e5\u5747 {total_fat/30:.1f} g'),  # 总脂肪摄入
    ]
    for i, row_data in enumerate(data1):
        for j, text in enumerate(row_data):
            table1.rows[i+1].cells[j].text = text
    
    doc.add_paragraph()
    
    # 三、运动统计
    EXERCISE_HEADING = '\u4e09\u3001\u8fd130\u5929\u8fd0\u52a8\u7edf\u8ba1'  # 三、近30天运动统计
    
    doc.add_heading(EXERCISE_HEADING, level=1)
    table2 = doc.add_table(rows=3, cols=3)
    table2.style = 'Table Grid'
    table2.alignment = WD_TABLE_ALIGNMENT.CENTER
    
    for i, header in enumerate(HEADERS):
        cell = table2.rows[0].cells[i]
        cell.text = header
        cell.paragraphs[0].runs[0].font.bold = True
    
    data2 = [
        ('\u603b\u8fd0\u52a8\u65f6\u957f', f'{total_exercise_minutes:.0f} \u5206\u949f', f'\u65e5\u5747 {total_exercise_minutes/30:.1f} \u5206\u949f'),  # 总运动时长、分钟
        ('\u603b\u6d88\u8017\u70ed\u91cf', f'{total_calories_burned:.0f} kcal', f'\u65e5\u5747 {total_calories_burned/30:.0f} kcal'),  # 总消耗热量
    ]
    for i, row_data in enumerate(data2):
        for j, text in enumerate(row_data):
            table2.rows[i+1].cells[j].text = text
    
    doc.add_paragraph()
    
    # 四、睡眠质量
    SLEEP_HEADING = '\u56db\u3001\u7761\u7720\u8d28\u91cf\u5206\u6790'  # 四、睡眠质量分析
    sleep_level = '\u4f18\u79c0' if avg_sleep >= 8 else '\u826f\u597d' if avg_sleep >= 7 else '\u4e00\u822c' if avg_sleep >= 6 else '\u9700\u6539\u5584'  # 优秀、良好、一般、需改善
    
    doc.add_heading(SLEEP_HEADING, level=1)
    doc.add_paragraph(f'\u00b7 \u5e73\u5747\u7761\u7720\u65f6\u957f\uff1a{avg_sleep:.1f} \u5c0f\u65f6/\u5929')  # 平均睡眠时长、小时/天
    doc.add_paragraph(f'\u00b7 \u7761\u7720\u8d28\u91cf\u8bc4\u7ea7\uff1a{sleep_level}')  # 睡眠质量评级
    
    doc.add_paragraph()
    
    # 五、健康建议
    RECOMMEND_HEADING = '\u4e94\u3001\u4e2a\u6027\u5316\u5065\u5eb7\u5efa\u8bae'  # 五、个性化健康建议
    
    doc.add_heading(RECOMMEND_HEADING, level=1)
    doc.add_paragraph('\u300a\u76ee\u6807\u8bbe\u7f6e\u300b')  # 【目标设置】
    doc.add_paragraph(f'\u00b7 \u6bcf\u65e5\u76ee\u6807\u70ed\u91cf\uff1a{current_user.target_calories:.0f} kcal')
    doc.add_paragraph(f'\u00b7 \u6bcf\u65e5\u76ee\u6807\u86cb\u767d\u8d28\uff1a{current_user.target_protein:.0f} g')
    doc.add_paragraph(f'\u00b7 \u5f53\u524d\u4f53\u91cd\uff1a{current_user.weight:.1f} kg')
    
    doc.add_paragraph()
    doc.add_paragraph('\u300a\u5065\u5eb7\u5efa\u8bae\u300b')  # 【健康建议】
    for tip in tips:
        doc.add_paragraph(f'\u00b7 {tip}')
    
    doc.add_paragraph()
    
    # 六、季节饮食建议
    SEASON_HEADING = '\u516d\u3001\u5b63\u8282\u996e\u98df\u5efa\u8bae\uff08\u6625\u5b63\uff09'  # 六、季节饮食建议（春季）
    
    doc.add_heading(SEASON_HEADING, level=1)
    
    table3 = doc.add_table(rows=5, cols=2)
    table3.style = 'Table Grid'
    table3.alignment = WD_TABLE_ALIGNMENT.CENTER
    
    table3.rows[0].cells[0].text = '\u5efa\u8bae\u591a\u5403'  # 建议多吃
    table3.rows[0].cells[1].text = '\u5efa\u8bae\u5c11\u5403'  # 建议少吃
    table3.rows[0].cells[0].paragraphs[0].runs[0].font.bold = True
    table3.rows[0].cells[1].paragraphs[0].runs[0].font.bold = True
    
    more_foods = '\u00b7 \u65b0\u9c9c\u6625\u7b0b\u3001\u9999\u69df\u3001\u8367\u83c9\u7b49\u65f6\u4ee4\u852c\u83dc\n\u00b7 \u8349\u8393\u3001\u6a31\u6843\u3001\u67d0\u67d0\u7b49\u6625\u5b63\u6c34\u679c\n\u00b7 \u6e05\u6de1\u6613\u6d88\u5316\u7684\u98df\u7269\uff0c\u5982\u7ca5\u3001\u6c64\n\u00b7 \u5bcc\u542b\u7ef4\u751f\u7d20C\u7684\u8944\u69d0\u7c7b\u98df\u7269'
    less_foods = '\u00b7 \u6cb9\u80a0\u3001\u8fa3\u6cb9\u523a\u6fc0\u6027\u98df\u7269\n\u00b7 \u751f\u51b7\u51b0\u51c9\u7684\u98df\u7269\u996e\u6599\n\u00b7 \u8fc7\u54b8\u8fc7\u751c\u7684\u91cd\u53e3\u5473\u98df\u54c1\n\u00b7 \u6613\u5f15\u53d1\u8fc7\u654f\u7684\u9c7c\u867e\u6d77\u9c7c'
    
    for i in range(1, 5):
        table3.rows[i].cells[0].text = more_foods.split('\n')[i-1] if i <= len(more_foods.split('\n')) else ''
        table3.rows[i].cells[1].text = less_foods.split('\n')[i-1] if i <= len(less_foods.split('\n')) else ''
    
    doc.add_paragraph()
    doc.add_paragraph()
    
    # 页脚
    FOOTER1 = '熵食源 - 让健康饮食更简单'
    FOOTER2 = '\u672c\u62a5\u544a\u7531AI\u81ea\u52a8\u751f\u6210\uff0c\u6570\u636e\u4ec5\u4f9b\u53c2\u8003\uff0c\u8bf7\u7ed3\u5408\u5b9e\u9645\u60c5\u51b5\u548c\u4e13\u4e1a\u5efa\u8bae\u4f7f\u7528'  # 本报告由AI自动生成，数据仅供参考，请结合实际情况和专业建议使用
    
    footer = doc.add_paragraph()
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = footer.add_run(FOOTER1)
    run.font.size = Pt(10)
    
    footer2 = doc.add_paragraph()
    footer2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = footer2.add_run(FOOTER2)
    run.font.size = Pt(9)
    run.font.color.rgb = RGBColor(128, 128, 128)
    
    # 保存文件
    from flask import make_response
    import urllib.parse
    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    
    response = make_response(buffer.getvalue())
    response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    # 安全处理文件名 - 使用纯ASCII避免编码问题
    safe_username = str(current_user.username).replace('/', '_').replace('\\', '_')
    filename = f'HealthReport_{safe_username}_{date.today().strftime("%Y%m%d")}.docx'
    response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    return response


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
