# -*- coding: utf-8 -*-
"""
熵食源 - 在线食物营养分析APP
主应用文件
"""
from __future__ import unicode_literals

from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session, make_response
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime, date, timedelta
from datetime import timezone, tzinfo
import os
import json
import base64
import random
import re
from io import BytesIO
import feedparser
import requests
import wave

from models import db, User, Food, FoodRecord, Exercise, ExerciseRecord, WeightRecord, BmiRecord, SleepRecord, TeaCoffeeLog, IntermittentFasting, HealthNews, AIAnalysis, CategoryLibrary, LearnedFood, FoodImageSample, FoodRecognitionLog, PageView
from functools import wraps

app = Flask(__name__)
app.config.from_object('config.Config')

# 初始化扩展
db.init_app(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = '请先登录'

# 确保上传目录存在
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


# ==================== 数据库初始化 ====================

def init_category_libraries():
    """初始化类别库数据"""
    categories = [
        {'name': '蔬菜', 'description': '各类新鲜蔬菜，富含维生素和膳食纤维', 'keywords': '青菜,白菜,菠菜,芹菜,黄瓜,西红柿,茄子,豆角,青椒,萝卜,土豆,南瓜,冬瓜,丝瓜,苦瓜,生菜,油麦菜,空心菜,苋菜,韭菜,葱,姜,蒜,洋葱,西兰花,花菜,莴笋,竹笋,香菇,蘑菇,木耳'},
        {'name': '肉类', 'description': '猪牛羊鸡等畜禽肉类，主要蛋白质来源', 'keywords': '猪肉,牛肉,羊肉,鸡肉,鸭肉,鹅肉,火腿,培根,香肠,排骨,五花肉,里脊,牛腩,牛排,羊排,鸡腿,鸡翅,鸡胸肉'},
        {'name': '海鲜', 'description': '鱼、虾、蟹、贝类等水产品，富含优质蛋白', 'keywords': '鱼,虾,蟹,贝,鱿鱼,章鱼,海参,鲍鱼,龙虾,对虾,基围虾,带鱼,黄花鱼,鲫鱼,鲤鱼,三文鱼,金枪鱼,鳕鱼,扇贝,蛤蜊,牡蛎,生蚝'},
        {'name': '水果', 'description': '各类新鲜水果，富含维生素和矿物质', 'keywords': '苹果,香蕉,橙子,橘子,柚子,葡萄,西瓜,哈密瓜,草莓,蓝莓,樱桃,桃子,梨子,李子,杏子,柿子,石榴,芒果,菠萝,榴莲,火龙果,猕猴桃,柠檬'},
        {'name': '主食', 'description': '米饭、面条、面包等碳水化合物主食', 'keywords': '米饭,面条,馒头,包子,饺子,馄饨,粥,米粉,河粉,拉面,刀削面,意大利面,面包,吐司,三明治,汉堡,披萨,煎饼,油条,烧饼,玉米,红薯,紫薯,土豆泥'},
        {'name': '蛋类', 'description': '鸡蛋、鸭蛋等各种蛋类食品', 'keywords': '鸡蛋,鸭蛋,鹅蛋,鹌鹑蛋,皮蛋,咸蛋,荷包蛋,煎蛋,炒蛋,蒸蛋,茶叶蛋,卤蛋'},
        {'name': '豆类', 'description': '黄豆、豆腐、豆浆等豆制品', 'keywords': '黄豆,黑豆,红豆,绿豆,豌豆,蚕豆,豆腐,豆腐干,豆腐皮,腐竹,豆浆,豆奶,豆芽,毛豆,四季豆,荷兰豆'},
        {'name': '饮品', 'description': '牛奶、咖啡、茶等各种饮料', 'keywords': '牛奶,酸奶,豆浆,咖啡,茶,绿茶,红茶,乌龙茶,奶茶,果汁,可乐,雪碧,汽水,啤酒,红酒,白酒,蜂蜜水,柠檬水'},
        {'name': '坚果', 'description': '花生、核桃、杏仁等坚果零食', 'keywords': '花生,核桃,杏仁,腰果,开心果,瓜子,松子,榛子,夏威夷果,碧根果,巴旦木,葡萄干,红枣,枸杞,桂圆,莲子'},
        {'name': '其他', 'description': '其他未分类食物', 'keywords': '零食,糖果,巧克力,饼干,蛋糕,面包,薯片,辣条,果冻,布丁,冰淇淋,雪糕,甜点,酱料,调料,油,盐,酱,醋'}
    ]
    
    for cat_data in categories:
        existing = CategoryLibrary.query.filter_by(name=cat_data['name']).first()
        if not existing:
            cat = CategoryLibrary(**cat_data)
            db.session.add(cat)
    
    db.session.commit()


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

# 北京时区 (UTC+8)
BJ_TZ = timezone(timedelta(hours=8))

def now_bj():
    """获取北京时间"""
    return datetime.now(BJ_TZ)

# 页面名称映射
PAGE_NAMES = {
    'index': '首页',
    'diet': '饮食记录',
    'add_diet': '添加饮食',
    'foods': '食物库',
    'exercise': '运动记录',
    'add_exercise': '添加运动',
    'weight': '体重管理',
    'sleep': '睡眠记录',
    'profile': '个人设置',
    'news': '健康新闻',
    'ai_analysis': 'AI分析',
    'fasting': '轻断食',
    'beverages': '饮品记录',
    'food_camera': '拍照识别',
    'food_text': '文本输入',
    'food_voice': '语音输入',
    'food_barcode': '扫码识别',
    'learned_foods': '学习库',
    'learned_food_detail': '学习详情',
}

def track_page_view(f_page_name=None):
    """页面访问记录装饰器"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # 执行原函数
            response = f(*args, **kwargs)
            
            # 仅在用户已登录时记录
            if current_user.is_authenticated:
                try:
                    endpoint = request.endpoint or ''
                    page_name = f_page_name or PAGE_NAMES.get(endpoint, endpoint)
                    
                    # 记录访问
                    view = PageView(
                        user_id=current_user.id,
                        endpoint=endpoint,
                        page_name=page_name,
                        page_url=request.full_path if request.query_string else request.path,
                        referrer=request.referrer or '',
                        user_agent=request.user_agent.string[:255] if request.user_agent else ''
                    )
                    db.session.add(view)
                    db.session.commit()
                except Exception as e:
                    db.session.rollback()
                    print(f"记录页面访问失败: {e}")
            
            return response
        return decorated_function
    return decorator

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
        Exercise(name='快跑', category='cardio', met_value=11.0, calories_per_hour=800, description='冲刺或高强度跑'),
        Exercise(name='游泳', category='cardio', met_value=6.0, calories_per_hour=450, description='自由泳'),
        Exercise(name='游泳(慢)', category='cardio', met_value=4.0, calories_per_hour=300, description='休闲游泳'),
        Exercise(name='骑自行车', category='cardio', met_value=5.8, calories_per_hour=400, description='户外骑行'),
        Exercise(name='动感单车', category='cardio', met_value=7.0, calories_per_hour=500, description='室内动感单车'),
        Exercise(name='跳绳', category='cardio', met_value=11.8, calories_per_hour=850, description='中等强度'),
        Exercise(name='健身操', category='cardio', met_value=6.5, calories_per_hour=480, description='有氧健身操'),
        Exercise(name='有氧舞蹈', category='cardio', met_value=5.5, calories_per_hour=400, description='舞蹈有氧'),
        Exercise(name='爬山', category='cardio', met_value=7.5, calories_per_hour=550, description='户外爬山'),
        Exercise(name='划船机', category='cardio', met_value=7.0, calories_per_hour=500, description='室内划船'),
        Exercise(name='椭圆机', category='cardio', met_value=5.0, calories_per_hour=360, description='椭圆机训练'),
        
        # 力量训练
        Exercise(name='哑铃训练', category='strength', met_value=5.0, calories_per_hour=350, description='上肢力量训练'),
        Exercise(name='杠铃训练', category='strength', met_value=6.0, calories_per_hour=420, description='负重训练'),
        Exercise(name='深蹲', category='strength', met_value=5.0, calories_per_hour=350, description='自重深蹲'),
        Exercise(name='硬拉', category='strength', met_value=6.0, calories_per_hour=420, description='负重硬拉'),
        Exercise(name='俯卧撑', category='strength', met_value=4.0, calories_per_hour=280, description='标准俯卧撑'),
        Exercise(name='平板支撑', category='strength', met_value=4.0, calories_per_hour=280, description='核心训练'),
        Exercise(name='引体向上', category='strength', met_value=5.0, calories_per_hour=350, description='自重或负重'),
        Exercise(name='核心训练', category='strength', met_value=4.5, calories_per_hour=320, description='腹肌训练'),
        
        # 球类运动
        Exercise(name='篮球', category='sports', met_value=8.0, calories_per_hour=580, description='半场或全场'),
        Exercise(name='足球', category='sports', met_value=8.0, calories_per_hour=580, description='比赛或训练'),
        Exercise(name='羽毛球', category='sports', met_value=5.5, calories_per_hour=400, description='单打比赛'),
        Exercise(name='网球', category='sports', met_value=7.3, calories_per_hour=520, description='单打比赛'),
        Exercise(name='乒乓球', category='sports', met_value=4.0, calories_per_hour=280, description='休闲打球'),
        Exercise(name='排球', category='sports', met_value=3.0, calories_per_hour=220, description='室内排球'),
        Exercise(name='高尔夫', category='sports', met_value=3.5, calories_per_hour=250, description='步行下场'),
        Exercise(name='保龄球', category='sports', met_value=3.0, calories_per_hour=220, description='休闲保龄球'),
        
        # 日常活动
        Exercise(name='散步', category='daily', met_value=2.5, calories_per_hour=180, description='轻松步行'),
        Exercise(name='家务劳动', category='daily', met_value=3.5, calories_per_hour=250, description='清洁打扫'),
        Exercise(name='爬楼梯', category='cardio', met_value=8.8, calories_per_hour=650, description='连续爬楼'),
        Exercise(name='遛狗', category='daily', met_value=3.0, calories_per_hour=220, description='遛宠物'),
        Exercise(name='园艺', category='daily', met_value=4.0, calories_per_hour=280, description='种植除草'),
        
        # 休闲运动
        Exercise(name='瑜伽', category='flexibility', met_value=3.0, calories_per_hour=200, description='哈他瑜伽'),
        Exercise(name='普拉提', category='flexibility', met_value=3.8, calories_per_hour=280, description='核心普拉提'),
        Exercise(name='太极', category='flexibility', met_value=3.0, calories_per_hour=200, description='太极拳'),
        Exercise(name='八段锦', category='flexibility', met_value=3.0, calories_per_hour=200, description='传统健身功法'),
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
                    published_at = now_bj()
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
                'published_at': now_bj() - timedelta(days=i * 2)
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
                    
                    published_at = now_bj()
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
@track_page_view('首页')
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
@track_page_view('食物库')
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
                        if source == 'learned_library':
                            result_item['learned'] = True
                            result_item['confirmed_count'] = item.get('confirmed_count', 1)
                            result_item['learned_count'] = item.get('confirmed_count', 1)  # 前端使用learned_count
                            result_item['is_archived'] = item.get('is_archived', False)
                            result_item['sample_count'] = item.get('sample_count', 0)
                        
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
    学习用户确认的食物图片特征（旧版API，保留兼容）
    """
    try:
        data = request.get_json()
        image_base64 = data.get('image', '')
        food_name = data.get('food_name', '')
        food_category = data.get('food_category', '')
        
        if not image_base64 or not food_name:
            return jsonify({'success': False, 'message': '缺少必要参数'})
        
        # 使用新版学习系统
        from local_image_recognition import save_food_sample
        result = save_food_sample(
            image_base64,
            food_name,
            food_category or '其他',
            current_user.id,
            db.session
        )
        
        return jsonify(result)
            
    except Exception as e:
        app.logger.error(f'学习食物特征失败: {e}')
        import traceback
        app.logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'message': '服务器错误'
        })


@app.route('/api/learn-food-v2', methods=['POST'])
@login_required
def api_learn_food_v2():
    """
    新版食物学习API
    用户手动纠正识别结果，AI学习并归档到类别库
    """
    try:
        data = request.get_json()
        image_base64 = data.get('image', '')
        food_name = data.get('food_name', '')
        food_category = data.get('food_category', '')
        
        if not image_base64 or not food_name:
            return jsonify({'success': False, 'message': '缺少必要参数'})
        
        if not food_category:
            return jsonify({'success': False, 'message': '请选择食物类别'})
        
        # 使用新版学习系统保存样本
        from local_image_recognition import save_food_sample
        result = save_food_sample(
            image_base64,
            food_name,
            food_category,
            current_user.id,
            db.session
        )
        
        if result['success']:
            # 获取营养信息
            try:
                from baidu_ai import get_food_nutrition
                nutrition = get_food_nutrition(food_name)
                
                result['calories'] = nutrition.get('calories', 100)
                result['protein'] = nutrition.get('protein', 5)
                result['carbs'] = nutrition.get('carbs', 15)
                result['fat'] = nutrition.get('fat', 3)
            except Exception as nutrition_error:
                # 营养信息获取失败不影响学习结果
                app.logger.warning(f'获取营养信息失败: {nutrition_error}')
                result['calories'] = 100
                result['protein'] = 5
                result['carbs'] = 15
                result['fat'] = 3
        
        return jsonify(result)
            
    except Exception as e:
        app.logger.error(f'学习食物特征失败: {e}')
        import traceback
        app.logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'message': f'服务器错误: {str(e)}'
        })


@app.route('/api/my-learned-foods')
@login_required
def api_my_learned_foods():
    """获取用户已学习的食物列表"""
    try:
        category_id = request.args.get('category_id', type=int)
        
        from local_image_recognition import get_user_learned_foods
        foods = get_user_learned_foods(current_user.id, db.session, category_id)
        
        return jsonify({
            'success': True,
            'foods': foods
        })
    except Exception as e:
        app.logger.error(f'获取学习库失败: {e}')
        return jsonify({
            'success': False,
            'message': str(e)
        })


@app.route('/api/category-libraries')
@login_required
def api_category_libraries():
    """获取所有类别库"""
    try:
        from local_image_recognition import get_category_libraries
        categories = get_category_libraries(db.session)
        
        return jsonify({
            'success': True,
            'categories': categories
        })
    except Exception as e:
        app.logger.error(f'获取类别库失败: {e}')
        return jsonify({
            'success': False,
            'message': str(e)
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


@app.route('/api/add_food', methods=['POST'])
@login_required
def api_add_food():
    """API接口：添加新食物到数据库（用于语音学习功能）"""
    try:
        data = request.get_json()
        name = data.get('name', '').strip()
        # 清理名称末尾的标点符号
        name = name.rstrip('。.。,，、;；:：!！?？')

        category = data.get('category', '其他')
        calories = float(data.get('calories', 0))
        protein = float(data.get('protein', 0))
        carbs = float(data.get('carbs', 0))
        fat = float(data.get('fat', 0))
        serving = data.get('serving', '100g')

        if not name:
            return jsonify({'success': False, 'message': '食物名称不能为空'})

        # 检查是否已存在（忽略大小写）
        existing = Food.query.filter(Food.name.ilike(name)).first()
        if existing:
            return jsonify({'success': False, 'message': f'"{name}" 已存在于数据库中'})

        food = Food(
            name=name,
            category=category,
            calories=calories,
            protein=protein,
            carbs=carbs,
            fat=fat,
            fiber=0,
            is_custom=True,
            created_by=current_user.id
        )
        db.session.add(food)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': f'"{name}" 已添加到食物库！',
            'food': {
                'name': name,
                'category': category,
                'calories': calories,
                'protein': protein,
                'carbs': carbs,
                'fat': fat,
                'serving': serving
            }
        })
    except Exception as e:
        app.logger.error(f'添加食物失败: {e}')
        return jsonify({'success': False, 'message': str(e)})





@app.route('/api/baidu_voice_token')
def api_baidu_voice_token():
    """获取百度语音识别access_token"""
    try:
        api_key = app.config.get('BAIDU_API_KEY')
        secret_key = app.config.get('BAIDU_SECRET_KEY')
        
        if not api_key or not secret_key:
            return jsonify({'success': False, 'message': '未配置百度API密钥'})
        
        url = "https://aip.baidubce.com/oauth/2.0/token"
        params = {
            "grant_type": "client_credentials",
            "client_id": api_key,
            "client_secret": secret_key
        }
        
        response = requests.post(url, params=params, timeout=10)
        result = response.json()
        
        if 'access_token' in result:
            return jsonify({
                'success': True, 
                'access_token': result['access_token'],
                'expires_in': result.get('expires_in', 2592000)
            })
        else:
            return jsonify({'success': False, 'message': result.get('error_description', '获取token失败')})
    except Exception as e:
        app.logger.error(f'获取百度语音token失败: {e}')
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/baidu_asr', methods=['POST'])
def api_baidu_asr():
    """
    百度语音识别API
    接收: audio base64编码的音频数据
    返回: 识别文字
    """
    try:
        api_key = app.config.get('BAIDU_API_KEY')
        secret_key = app.config.get('BAIDU_SECRET_KEY')
        
        if not api_key or not secret_key:
            return jsonify({'success': False, 'message': '未配置百度API密钥'})
        
        # 先获取 token（增加缓存机制）
        token_url = "https://aip.baidubce.com/oauth/2.0/token"
        token_params = {
            "grant_type": "client_credentials",
            "client_id": api_key,
            "client_secret": secret_key
        }
        
        token_response = requests.post(token_url, params=token_params, timeout=30)
        token_result = token_response.json()
        
        if 'access_token' not in token_result:
            return jsonify({'success': False, 'message': '获取access_token失败'})
        
        access_token = token_result['access_token']
        
        # 获取音频数据
        audio_data = request.files.get('audio')
        audio_bytes = None
        
        if audio_data:
            audio_bytes = audio_data.read()
        else:
            # 从base64获取
            data = request.get_json(silent=True) or {}
            audio_base64 = data.get('audio', '')
            if audio_base64:
                app.logger.info(f'收到base64音频数据，长度: {len(audio_base64)}')
                try:
                    audio_bytes = base64.b64decode(audio_base64)
                    app.logger.info(f'解码后音频数据长度: {len(audio_bytes)}')
                except Exception as e:
                    app.logger.error(f'音频解码失败: {e}')
                    return jsonify({'success': False, 'message': '音频解码失败'})
        
        if not audio_bytes:
            app.logger.error('没有收到音频数据')
            return jsonify({'success': False, 'message': '没有音频数据'})
        
        # 调用百度短语音识别API（新版，支持更多格式）
        asr_url = f"https://vop.baidu.com/pro_api"
        
        # 百度语音识别参数
        params = {
            'dev_pid': 1537,  # 中文普通话识别
            'format': 'wav',  # 使用wav格式
            'rate': 16000,
            'token': access_token,
            'cuid': 'entropy_food_app',
            'len': len(audio_bytes),
            'channel': 1
        }
        
        headers = {
            'Content-Type': 'audio/wav; rate=16000'
        }
        
        app.logger.info(f'发送百度ASR请求, 音频长度: {len(audio_bytes)}, URL: {asr_url}')
        
        # 增加超时时间到60秒
        asr_response = requests.post(
            asr_url,
            params=params,
            headers=headers,
            data=audio_bytes,
            timeout=60
        )
        
        result = asr_response.json()
        app.logger.info(f'百度ASR响应: {result}')
        
        if result.get('err_no') == 0 and result.get('result'):
            text = result['result'][0]
            # 去掉末尾标点
            text = re.sub(r'[。！？，、；：""''【】（）\s]+$', '', text.strip())
            return jsonify({'success': True, 'text': text})
        else:
            err_msg = result.get('err_msg', '识别失败')
            err_no = result.get('err_no', 0)
            app.logger.error(f'百度语音识别失败: err_no={err_no}, err_msg={err_msg}')
            return jsonify({'success': False, 'message': err_msg})
            
    except requests.exceptions.Timeout:
        app.logger.error('百度语音识别超时')
        return jsonify({'success': False, 'message': '识别超时，请重试或缩短语音'})
    except Exception as e:
        app.logger.error(f'百度语音识别异常: {e}')
        import traceback
        app.logger.error(traceback.format_exc())
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/all_foods')
def api_get_foods():
    """API接口：获取所有食物列表"""
    try:
        foods = Food.query.all()
        food_list = []
        for f in foods:
            food_list.append({
                'name': f.name,
                'category': f.category,
                'calories': f.calories,
                'protein': f.protein,
                'carbs': f.carbs,
                'fat': f.fat,
                'serving': '100g'
            })
        return jsonify({'success': True, 'foods': food_list})
    except Exception as e:
        app.logger.error(f'获取食物列表失败: {e}')
        return jsonify({'success': False, 'message': str(e), 'foods': []})


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
@track_page_view('饮食记录')
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
            
            # 支持批量添加（多食物批量输入）
            foods = data.get('foods', [])
            meal_type = data.get('meal_type')  # 不再默认零食
            
            # 获取记录日期
            record_date_str = data.get('record_date')
            if record_date_str:
                try:
                    record_date = datetime.strptime(record_date_str, '%Y-%m-%d').date()
                except:
                    record_date = date.today()
            else:
                record_date = date.today()
            
            # 根据时间智能判断餐次
            if not meal_type or meal_type == 'snack':
                current_hour = now_bj().hour
                if current_hour >= 5 and current_hour < 10:
                    meal_type = 'breakfast'
                elif current_hour >= 10 and current_hour < 14:
                    meal_type = 'lunch'
                elif current_hour >= 14 and current_hour < 17:
                    meal_type = 'snack'
                elif current_hour >= 17 and current_hour < 21:
                    meal_type = 'dinner'
                else:
                    meal_type = 'snack'  # 深夜默认为零食
            
            if foods:
                for item in foods:
                    quantity = float(item.get('quantity', 100))
                    # 如果传入的是每100g数据，需要根据实际份量换算
                    cal_per_100 = float(item.get('calories_per_100g', 0))
                    if cal_per_100 > 0:
                        calories = cal_per_100 * quantity / 100
                        protein = float(item.get('protein_per_100g', 0)) * quantity / 100
                        carbs = float(item.get('carbs_per_100g', 0)) * quantity / 100
                        fat = float(item.get('fat_per_100g', 0)) * quantity / 100
                    else:
                        calories = float(item.get('calories', 0))
                        protein = float(item.get('protein', 0))
                        carbs = float(item.get('carbs', 0))
                        fat = float(item.get('fat', 0))
                    
                    # 兼容 JavaScript 发送的 name 和 food_name 字段
                    food_name = item.get('food_name') or item.get('name') or '未知食物'
                    
                    record = FoodRecord(
                        user_id=current_user.id,
                        food_id=item.get('food_id'),
                        food_name=food_name,
                        quantity=quantity,
                        meal_type=meal_type,
                        calories=calories,
                        protein=protein,
                        carbs=carbs,
                        fat=fat,
                        input_method=input_method,
                        date=record_date,
                        time=now_bj().time()  # 使用当前时间
                    )
                    db.session.add(record)
                db.session.commit()
                return jsonify({'success': True, 'message': f'批量添加{len(foods)}条记录成功'})
        else:
            food_id = request.form.get('food_id')
            food_name = request.form.get('food_name')
            quantity = float(request.form.get('quantity', 100))
            meal_type = request.form.get('meal_type', 'snack')
            
            # 获取记录日期
            record_date_str = request.form.get('record_date')
            if record_date_str:
                try:
                    record_date = datetime.strptime(record_date_str, '%Y-%m-%d').date()
                except:
                    record_date = date.today()
            else:
                record_date = date.today()
            
            food = Food.query.get(food_id) if food_id else None
            
            # 优先使用用户手动输入的营养数据，否则尝试从食物库获取
            user_calories = float(request.form.get('calories', 0) or 0)
            user_protein = float(request.form.get('protein', 0) or 0)
            user_carbs = float(request.form.get('carbs', 0) or 0)
            user_fat = float(request.form.get('fat', 0) or 0)
            
            matched_food = None
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
                food_id=food_id or (matched_food.id if matched_food else None),
                food_name=food_name or (food.name if food else '未知食物'),
                quantity=quantity,
                meal_type=meal_type,
                calories=calories,
                protein=protein,
                carbs=carbs,
                fat=fat,
                input_method=request.form.get('input_method', 'text'),
                date=record_date,
                time=now_bj().time()
            )
            
            db.session.add(record)
            db.session.commit()
            
            flash('饮食记录已添加！', 'success')
            return redirect(url_for('diet', date=record_date.isoformat()))
        
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
    
    return render_template('add_diet.html', recent_foods=recent_foods, today=date.today().isoformat())


# ==================== 拍照识别食物 ====================

@app.route('/food/camera')
@login_required
def food_camera():
    """拍照识别食物页面"""
    return render_template('food_camera.html')


@app.route('/my-learned-foods')
@login_required
def learned_foods():
    """我的学习库页面"""
    category_id = request.args.get('category_id', type=int)
    
    # 获取所有类别
    categories = CategoryLibrary.query.all()
    
    # 获取用户学习的食物
    query = LearnedFood.query.filter_by(user_id=current_user.id, is_active=True)
    if category_id:
        query = query.filter_by(category_id=category_id)
    foods = query.order_by(LearnedFood.updated_at.desc()).all()
    
    # 统计
    total_foods = LearnedFood.query.filter_by(user_id=current_user.id, is_active=True).count()
    total_samples = db.session.query(db.func.sum(LearnedFood.sample_count)).filter_by(
        user_id=current_user.id
    ).scalar() or 0
    archived_foods = LearnedFood.query.filter(
        LearnedFood.user_id == current_user.id,
        LearnedFood.is_active == True,
        LearnedFood.sample_count >= 2
    ).count()
    
    return render_template('learned_foods.html',
                         categories=categories,
                         foods=foods,
                         current_category=category_id,
                         total_foods=total_foods,
                         total_samples=total_samples,
                         archived_foods=archived_foods)


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
@track_page_view('运动记录')
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
        # 检查是否为JSON请求
        if request.is_json:
            data = request.get_json()
            exercise_name = data.get('exercise_name')
            duration = int(data.get('duration', 30))
            calories_burned = int(data.get('calories_burned', 0))
            intensity = data.get('intensity', 'moderate')

            if not exercise_name:
                return jsonify({'success': False, 'message': '运动名称不能为空'})

            record = ExerciseRecord(
                user_id=current_user.id,
                exercise_name=exercise_name,
                duration=duration,
                calories_burned=calories_burned,
                intensity=intensity
            )
            db.session.add(record)
            db.session.commit()

            return jsonify({'success': True, 'message': '运动记录已保存'})

        # 表单请求处理
        exercise_ids = request.form.getlist('exercise_ids')
        exercise_name = request.form.get('exercise_name')
        duration = int(request.form.get('duration', 30))
        intensity = request.form.get('intensity', 'moderate')

        # 获取自定义运动的卡路里
        custom_calories = request.form.get('custom_calories')
        custom_name = request.form.get('exercise_name')

        # 处理选择的运动
        added_count = 0
        total_calories = 0

        if exercise_ids:
            for ex_id in exercise_ids:
                try:
                    exercise = Exercise.query.get(int(ex_id))
                    if exercise:
                        calories = exercise.get_calories_burned(current_user.weight, duration)
                        record = ExerciseRecord(
                            user_id=current_user.id,
                            exercise_id=exercise.id,
                            exercise_name=exercise.name,
                            duration=duration,
                            calories_burned=calories,
                            intensity=intensity
                        )
                        db.session.add(record)
                        total_calories += calories
                        added_count += 1
                except (ValueError, TypeError):
                    continue

        # 处理自定义运动
        if custom_name and custom_calories:
            cal_per_hour = int(custom_calories)
            # 根据强度调整
            intensity_factor = {'low': 0.7, 'moderate': 1.0, 'high': 1.3}.get(intensity, 1.0)
            calories = int(cal_per_hour * intensity_factor * duration / 60)
            record = ExerciseRecord(
                user_id=current_user.id,
                exercise_name=custom_name,
                duration=duration,
                calories_burned=calories,
                intensity=intensity
            )
            db.session.add(record)
            total_calories += calories
            added_count += 1

        if added_count > 0:
            db.session.commit()
            flash(f'已添加 {added_count} 项运动记录！共燃烧 {total_calories} kcal', 'success')
        else:
            flash('请至少选择一项运动', 'warning')

        return redirect(url_for('exercise'))

    exercises = Exercise.query.order_by(Exercise.category, Exercise.name).all()
    # 常用运动：选择热量消耗较高的8种
    common_exercises = Exercise.query.filter(
        Exercise.name.in_(['跑步', '游泳', '骑自行车', '跳绳', '篮球', '羽毛球', '快走', '瑜伽'])
    ).all()
    return render_template('add_exercise.html', exercises=exercises, common_exercises=common_exercises)


@app.route('/api/add_exercise', methods=['POST'])
@login_required
def api_add_exercise():
    """API接口：添加新运动到数据库"""
    try:
        data = request.get_json()
        name = data.get('name', '').strip()
        # 清理名称末尾的标点符号
        import re
        name = re.sub(r'[。.，、;：!？]+$', '', name)

        if not name:
            return jsonify({'success': False, 'message': '运动名称不能为空'})

        # 检查是否已存在
        existing = Exercise.query.filter(Exercise.name.ilike(name)).first()
        if existing:
            return jsonify({'success': False, 'message': f'"{name}" 已存在于运动库中'})

        category = data.get('category', '其他')
        met_value = float(data.get('met_value', 5.0))
        calories_per_hour = int(data.get('calories_per_hour', 300))
        intensity = data.get('intensity', 'moderate')

        exercise = Exercise(
            name=name,
            category=category,
            met_value=met_value,
            calories_per_hour=calories_per_hour,
            description=f'用户学习添加: {name}'
        )
        db.session.add(exercise)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': f'"{name}" 已添加到运动库！',
            'exercise': {
                'name': name,
                'category': category,
                'met_value': met_value,
                'calories_per_hour': calories_per_hour,
                'intensity': intensity
            }
        })
    except Exception as e:
        app.logger.error(f'添加运动失败: {e}')
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/all_exercises')
def api_all_exercises():
    """API接口：获取所有运动列表"""
    try:
        exercises = Exercise.query.all()
        exercise_list = []
        for ex in exercises:
            exercise_list.append({
                'name': ex.name,
                'category': ex.category,
                'met_value': ex.met_value,
                'calories_per_hour': ex.calories_per_hour
            })
        return jsonify({'success': True, 'exercises': exercise_list})
    except Exception as e:
        app.logger.error(f'获取运动列表失败: {e}')
        return jsonify({'success': False, 'message': str(e), 'exercises': []})


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
@track_page_view('体重管理')
def weight():
    """体重记录页面"""
    records = WeightRecord.query.filter_by(user_id=current_user.id).order_by(WeightRecord.date.desc()).limit(30).all()
    
    current_weight = records[0].weight if records else (current_user.weight or 65.0)
    weight_change = 0
    if len(records) >= 2:
        weight_change = records[0].weight - records[1].weight
    
    return render_template('weight.html',
                         records=records,
                         current_weight=current_weight,
                         weight_change=round(weight_change, 1),
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


@app.route('/api/bmi/save', methods=['POST'])
@login_required
def save_bmi_record():
    """保存BMI记录"""
    try:
        data = request.get_json()
        
        bmi_record = BmiRecord(
            user_id=current_user.id,
            bmi=data.get('bmi'),
            category=data.get('category'),
            height=data.get('height'),
            weight=data.get('weight'),
            age=data.get('age', current_user.age),
            gender=data.get('gender', current_user.gender)
        )
        
        db.session.add(bmi_record)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'BMI记录已保存',
            'record': bmi_record.to_dict()
        })
    except Exception as e:
        app.logger.error(f'保存BMI记录失败: {e}')
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@app.route('/api/bmi/history')
@login_required
def get_bmi_history():
    """获取BMI历史记录"""
    try:
        records = BmiRecord.query.filter_by(
            user_id=current_user.id
        ).order_by(BmiRecord.date.desc(), BmiRecord.created_at.desc()).limit(30).all()
        
        return jsonify({
            'success': True,
            'records': [r.to_dict() for r in records]
        })
    except Exception as e:
        app.logger.error(f'获取BMI历史失败: {e}')
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@app.route('/api/bmi/calculate', methods=['POST'])
@login_required
def calculate_bmi():
    """BMI计算API"""
    try:
        data = request.get_json()
        
        height_cm = float(data.get('height'))
        weight_kg = float(data.get('weight'))
        
        # 计算BMI
        height_m = height_cm / 100
        bmi = weight_kg / (height_m * height_m)
        
        # 确定分类
        if bmi < 18.5:
            category = '偏瘦'
        elif bmi < 24.9:
            category = '正常'
        elif bmi < 29.9:
            category = '超重'
        elif bmi < 34.9:
            category = 'I度肥胖'
        elif bmi < 39.9:
            category = 'II度肥胖'
        else:
            category = 'III度肥胖'
        
        # 计算理想体重范围
        min_weight = 18.5 * height_m * height_m
        max_weight = 24.9 * height_m * height_m
        ideal_weight = 22 * height_m * height_m
        
        return jsonify({
            'success': True,
            'bmi': round(bmi, 1),
            'category': category,
            'ideal_weight_range': {
                'min': round(min_weight, 1),
                'max': round(max_weight, 1),
                'ideal': round(ideal_weight, 1)
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


# ==================== 睡眠管理 ====================

@app.route('/sleep')
@login_required
@track_page_view('睡眠记录')
def sleep():
    """睡眠记录页面"""
    records = SleepRecord.query.filter_by(user_id=current_user.id).order_by(SleepRecord.date.desc()).limit(14).all()
    
    # 计算统计数据
    avg_duration = 0
    avg_quality = 0
    avg_score = 0
    avg_deep = 0
    avg_rem = 0
    today = date.today()
    
    if records:
        valid_records = [r for r in records if r.duration]
        if valid_records:
            avg_duration = sum(r.duration for r in valid_records) / len(valid_records)
        
        quality_records = [r for r in records if r.quality]
        if quality_records:
            avg_quality = sum(r.quality for r in quality_records) / len(quality_records)
        
        score_records = [r for r in records if r.sleep_score and r.sleep_score > 0]
        if score_records:
            avg_score = sum(r.sleep_score for r in score_records) / len(score_records)
        
        deep_records = [r for r in records if r.deep_sleep]
        if deep_records:
            avg_deep = sum(r.deep_sleep for r in deep_records) / len(deep_records)
        
        rem_records = [r for r in records if r.rem_sleep]
        if rem_records:
            avg_rem = sum(r.rem_sleep for r in rem_records) / len(rem_records)
    
    return render_template('sleep.html',
                         records=records,
                         today=today,
                         avg_duration=round(avg_duration, 1),
                         avg_quality=round(avg_quality, 1),
                         avg_score=round(avg_score, 0) if avg_score > 0 else round(avg_quality * 10, 0),
                         avg_deep=round(avg_deep, 0),
                         avg_rem=round(avg_rem, 0))


@app.route('/sleep/add', methods=['POST'])
@login_required
def add_sleep():
    """添加睡眠记录"""
    bed_time_str = request.form.get('bed_time')
    wake_time_str = request.form.get('wake_time')
    duration_str = request.form.get('duration')
    
    bed_time = None
    wake_time = None
    duration = None
    
    # 尝试解析时间
    try:
        if bed_time_str:
            bed_time = datetime.strptime(bed_time_str, '%Y-%m-%dT%H:%M')
        if wake_time_str:
            wake_time = datetime.strptime(wake_time_str, '%Y-%m-%dT%H:%M')
    except:
        pass
    
    # 计算时长
    if bed_time and wake_time:
        diff = (wake_time - bed_time).total_seconds() / 3600
        # 处理跨天情况
        if diff < 0:
            diff += 24
        duration = round(diff, 1)
    elif duration_str:
        try:
            duration = float(duration_str)
        except:
            duration = 7.0
    
    # 确保有默认值
    if not duration:
        duration = 7.0
    
    # 获取睡眠分期数据（分钟）
    deep_sleep = request.form.get('deep_sleep')
    light_sleep = request.form.get('light_sleep')
    rem_sleep = request.form.get('rem_sleep')
    awake_time = request.form.get('awake_time')
    
    # 检查是否有分期数据
    has_stages = any([deep_sleep, light_sleep, rem_sleep, awake_time])
    
    record = SleepRecord(
        user_id=current_user.id,
        bed_time=bed_time,
        wake_time=wake_time,
        duration=duration,
        quality=int(request.form.get('quality', 8)),
        caffeine_before_bed=bool(request.form.get('caffeine')),
        heavy_meal_before_bed=bool(request.form.get('heavy_meal')),
        screen_time=bool(request.form.get('screen_time')),
        notes=request.form.get('notes'),
        data_source='manual',
        # 睡眠分期数据
        deep_sleep=float(deep_sleep) if deep_sleep and deep_sleep.strip() else 0,
        light_sleep=float(light_sleep) if light_sleep and light_sleep.strip() else 0,
        rem_sleep=float(rem_sleep) if rem_sleep and rem_sleep.strip() else 0,
        awake_time=float(awake_time) if awake_time and awake_time.strip() else 0
    )
    
    db.session.add(record)
    db.session.commit()
    
    # 根据是否有分期数据显示不同提示
    if has_stages:
        flash(f'睡眠记录已添加！时长 {duration:.1f} 小时，深睡 {deep_sleep or 0} 分钟，REM {rem_sleep or 0} 分钟', 'success')
    else:
        flash(f'睡眠记录已添加！时长 {duration:.1f} 小时', 'success')
    
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
                diff = (record.wake_time - record.bed_time).total_seconds() / 3600
                if diff < 0:
                    diff += 24
                record.duration = round(diff, 1)
            else:
                record.duration = float(request.form.get('duration', 7))

            record.quality = int(request.form.get('quality', 8))
            record.caffeine_before_bed = bool(request.form.get('caffeine'))
            record.heavy_meal_before_bed = bool(request.form.get('heavy_meal'))
            record.notes = request.form.get('notes')
            
            # 睡眠分期数据
            record.deep_sleep = float(request.form.get('deep_sleep') or 0)
            record.light_sleep = float(request.form.get('light_sleep') or 0)
            record.rem_sleep = float(request.form.get('rem_sleep') or 0)
            record.awake_time = float(request.form.get('awake_time') or 0)

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


@app.route('/sleep/import', methods=['GET', 'POST'])
@login_required
def sleep_import():
    """从智能手表导入睡眠数据（CSV格式）"""
    if request.method == 'POST':
        if 'csv_file' not in request.files:
            flash('请选择CSV文件', 'error')
            return redirect(url_for('sleep_import'))
        
        file = request.files['csv_file']
        device_type = request.form.get('device_type', 'generic')  # huawei/apple/xiaomi/generic
        
        if file.filename == '':
            flash('请选择CSV文件', 'error')
            return redirect(url_for('sleep_import'))
        
        try:
            import csv
            import io
            
            # 读取CSV内容
            stream = io.StringIO(file.stream.read().decode('utf-8-sig'))
            reader = csv.DictReader(stream)
            
            imported_count = 0
            updated_count = 0
            errors = []
            
            for row_num, row in enumerate(reader, 2):
                try:
                    # 解析日期
                    date_str = row.get('date') or row.get('日期') or row.get('sleep_date') or row.get('记录日期')
                    if not date_str:
                        continue
                    
                    # 尝试多种日期格式
                    for fmt in ['%Y-%m-%d', '%Y/%m/%d', '%d/%m/%Y', '%m/%d/%Y']:
                        try:
                            record_date = datetime.strptime(date_str, fmt).date()
                            break
                        except:
                            continue
                    else:
                        errors.append(f'行{row_num}: 日期格式错误')
                        continue
                    
                    # 检查是否已存在该日期的记录
                    existing = SleepRecord.query.filter_by(
                        user_id=current_user.id,
                        date=record_date
                    ).first()
                    
                    # 解析睡眠时长（分钟或小时）
                    duration_str = row.get('duration') or row.get('睡眠时长') or row.get('总睡眠时长') or row.get('sleep_duration')
                    duration = parse_duration(duration_str) if duration_str else None
                    
                    # 解析睡眠分期（分钟）
                    deep_sleep = parse_duration(row.get('deep_sleep') or row.get('深睡') or row.get('深睡眠时长') or '0')
                    light_sleep = parse_duration(row.get('light_sleep') or row.get('浅睡') or row.get('浅睡眠时长') or '0')
                    rem_sleep = parse_duration(row.get('rem_sleep') or row.get('REM') or row.get('快速眼动') or '0')
                    awake_time = parse_duration(row.get('awake') or row.get('清醒') or row.get('清醒时长') or '0')
                    
                    # 解析时间
                    bed_time = parse_datetime(row.get('bed_time') or row.get('入睡时间') or row.get('bedtime'))
                    wake_time = parse_datetime(row.get('wake_time') or row.get('醒来时间') or row.get('waketime'))
                    
                    # 解析其他数据
                    quality = int(float(row.get('quality') or row.get('质量') or row.get('sleep_quality') or 0))
                    sleep_score = int(float(row.get('sleep_score') or row.get('睡眠评分') or row.get('score') or 0))
                    avg_spo2 = float(row.get('avg_spo2') or row.get('平均血氧') or row.get('spo2_avg') or 0)
                    min_spo2 = float(row.get('min_spo2') or row.get('最低血氧') or row.get('spo2_min') or 0)
                    sleep_hr_avg = int(float(row.get('hr_avg') or row.get('平均心率') or row.get('sleep_hr_avg') or 0))
                    
                    if existing:
                        # 更新现有记录
                        existing.duration = duration
                        existing.deep_sleep = deep_sleep
                        existing.light_sleep = light_sleep
                        existing.rem_sleep = rem_sleep
                        existing.awake_time = awake_time
                        existing.bed_time = bed_time or existing.bed_time
                        existing.wake_time = wake_time or existing.wake_time
                        existing.quality = quality or existing.quality
                        existing.sleep_score = sleep_score
                        existing.avg_spo2 = avg_spo2
                        existing.min_spo2 = min_spo2
                        existing.sleep_hr_avg = sleep_hr_avg
                        existing.data_source = device_type
                        updated_count += 1
                    else:
                        # 创建新记录
                        record = SleepRecord(
                            user_id=current_user.id,
                            date=record_date,
                            duration=duration,
                            deep_sleep=deep_sleep,
                            light_sleep=light_sleep,
                            rem_sleep=rem_sleep,
                            awake_time=awake_time,
                            bed_time=bed_time,
                            wake_time=wake_time,
                            quality=quality,
                            sleep_score=sleep_score,
                            avg_spo2=avg_spo2,
                            min_spo2=min_spo2,
                            sleep_hr_avg=sleep_hr_avg,
                            data_source=device_type,
                            source_device=row.get('device') or row.get('设备') or ''
                        )
                        db.session.add(record)
                        imported_count += 1
                        
                except Exception as e:
                    errors.append(f'行{row_num}: {str(e)}')
            
            db.session.commit()
            
            if imported_count > 0 or updated_count > 0:
                msg = f'导入成功！新增 {imported_count} 条，更新 {updated_count} 条'
                if errors:
                    msg += f'，{len(errors)} 条出错'
                flash(msg, 'success')
            elif errors:
                flash(f'导入完成但有问题: {errors[0]}', 'warning')
            else:
                flash('没有找到有效数据', 'warning')
                
        except Exception as e:
            flash(f'导入失败: {str(e)}', 'error')
        
        return redirect(url_for('sleep'))
    
    # 显示导入页面
    return render_template('sleep_import.html')


@app.route('/sleep/add-online', methods=['POST'])
@login_required
def sleep_add_online():
    """在线表单添加睡眠数据"""
    try:
        date_str = request.form.get('date')
        duration = float(request.form.get('duration', 0))
        
        if not date_str or not duration:
            return jsonify({'success': False, 'error': '请填写日期和睡眠时长'}), 400
        
        record_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        
        # 检查是否已存在该日期的记录
        existing = SleepRecord.query.filter_by(
            user_id=current_user.id,
            date=record_date
        ).first()
        
        if existing:
            # 更新现有记录
            existing.duration = duration
            existing.deep_sleep = float(request.form.get('deep_sleep') or 0)
            existing.light_sleep = float(request.form.get('light_sleep') or 0)
            existing.rem_sleep = float(request.form.get('rem_sleep') or 0)
            existing.awake_time = float(request.form.get('awake') or 0)
            existing.sleep_score = int(request.form.get('sleep_score') or 0)
            existing.avg_spo2 = float(request.form.get('avg_spo2') or 0)
            existing.min_spo2 = float(request.form.get('min_spo2') or 0)
            existing.sleep_hr_avg = int(request.form.get('hr_avg') or 0)
            existing.notes = request.form.get('notes')
            existing.data_source = request.form.get('device_type', 'manual')
            
            if request.form.get('bed_time'):
                existing.bed_time = parse_datetime(record_date.strftime('%Y-%m-%d') + ' ' + request.form.get('bed_time'))
            if request.form.get('wake_time'):
                existing.wake_time = parse_datetime(record_date.strftime('%Y-%m-%d') + ' ' + request.form.get('wake_time'))
        else:
            # 创建新记录
            record = SleepRecord(
                user_id=current_user.id,
                date=record_date,
                duration=duration,
                deep_sleep=float(request.form.get('deep_sleep') or 0),
                light_sleep=float(request.form.get('light_sleep') or 0),
                rem_sleep=float(request.form.get('rem_sleep') or 0),
                awake_time=float(request.form.get('awake') or 0),
                sleep_score=int(request.form.get('sleep_score') or 0),
                avg_spo2=float(request.form.get('avg_spo2') or 0),
                min_spo2=float(request.form.get('min_spo2') or 0),
                sleep_hr_avg=int(request.form.get('hr_avg') or 0),
                notes=request.form.get('notes'),
                data_source=request.form.get('device_type', 'manual')
            )
            
            if request.form.get('bed_time'):
                record.bed_time = parse_datetime(record_date.strftime('%Y-%m-%d') + ' ' + request.form.get('bed_time'))
            if request.form.get('wake_time'):
                record.wake_time = parse_datetime(record_date.strftime('%Y-%m-%d') + ' ' + request.form.get('wake_time'))
            
            db.session.add(record)
        
        db.session.commit()
        return jsonify({'success': True, 'message': '导入成功'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/sleep/analyze/<int:record_id>')
@login_required
def sleep_analyze(record_id):
    """获取单条睡眠记录的详细分析"""
    record = SleepRecord.query.get_or_404(record_id)
    
    if record.user_id != current_user.id:
        return jsonify({'error': '无权访问'}), 403
    
    # 生成分析和建议
    analysis = analyze_sleep_record(record)
    
    return jsonify(analysis)


def parse_duration(value):
    """解析时长字符串（支持分钟和小时格式）"""
    if not value:
        return 0
    value = str(value).strip()
    
    # 如果包含冒号（HH:MM格式）
    if ':' in value:
        parts = value.split(':')
        if len(parts) == 2:
            return float(parts[0]) + float(parts[1]) / 60
        elif len(parts) == 3:
            return float(parts[0]) + float(parts[1]) / 60 + float(parts[2]) / 3600
    
    # 如果包含"小时"或"h"
    if '小时' in value or 'h' in value.lower():
        try:
            return float(value.replace('小时', '').replace('h', '').replace('H', '').strip())
        except:
            return 0
    
    # 如果包含"分钟"或"min"
    if '分钟' in value or 'min' in value.lower():
        try:
            return float(value.replace('分钟', '').replace('min', '').replace('Min', '').strip()) / 60
        except:
            return 0
    
    # 纯数字，假设是小时
    try:
        return float(value)
    except:
        return 0


def parse_datetime(value):
    """解析日期时间字符串"""
    if not value:
        return None
    value = str(value).strip()
    
    formats = [
        '%Y-%m-%d %H:%M:%S',
        '%Y-%m-%d %H:%M',
        '%Y/%m/%d %H:%M:%S',
        '%Y/%m/%d %H:%M',
        '%Y-%m-%dT%H:%M:%S',
        '%Y-%m-%dT%H:%M',
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(value, fmt)
        except:
            continue
    return None


def analyze_sleep_record(record):
    """分析单条睡眠记录，生成解读和建议"""
    analysis = {
        'summary': '',
        'score': 0,
        'interpretation': [],
        'suggestions': []
    }
    
    if not record.duration:
        return analysis
    
    # 计算睡眠结构评分
    score = 0
    issues = []
    suggestions = []
    
    # 检查是否有智能手表详细数据
    has_watch_data = any([
        record.deep_sleep and record.deep_sleep > 0,
        record.rem_sleep and record.rem_sleep > 0,
        record.awake_time and record.awake_time > 0,
        record.avg_spo2 and record.avg_spo2 > 0,
        record.sleep_hr_avg and record.sleep_hr_avg > 0
    ])
    
    # 1. 时长评估 (40分)
    if record.duration < 6:
        score += max(0, int(record.duration * 5))  # 每小时5分
        issues.append('睡眠时长不足')
        suggestions.append('建议保证7-9小时睡眠，成年人每晚需要充足睡眠才能维持健康')
    elif record.duration > 9:
        if record.duration > 11:
            score += 20
            issues.append('睡眠时间过长')
            suggestions.append('过长的睡眠可能反映疲劳或健康问题，建议保持7-9小时的规律睡眠')
        else:
            score += 30
            analysis['interpretation'].append(f'睡眠时长 {record.duration:.1f}小时，略长但可接受')
    elif record.duration >= 7 and record.duration <= 9:
        score += 40
        analysis['interpretation'].append(f'✓ 睡眠时长理想 ({record.duration:.1f}小时)')
    else:  # 6-7小时
        score += 25
        analysis['interpretation'].append(f'睡眠时长 {record.duration:.1f}小时，接近推荐值')
    
    # 2. 深睡眠评估（应占20-25%）- 15分
    if record.duration and record.deep_sleep and record.deep_sleep > 0:
        deep_ratio = record.deep_sleep / (record.duration * 60) * 100
        if deep_ratio < 15:
            issues.append('深睡眠不足')
            suggestions.append('深睡眠不足会影响身体修复，建议睡前避免剧烈运动和摄入咖啡因')
        elif deep_ratio > 30:
            score += 15
            analysis['interpretation'].append(f'✓ 深睡眠充足 ({deep_ratio:.0f}%)')
        else:
            score += 10
            analysis['interpretation'].append(f'深睡眠占比 {deep_ratio:.0f}%，基本正常')
    
    # 3. REM睡眠评估（应占20-25%）- 15分
    if record.duration and record.rem_sleep and record.rem_sleep > 0:
        rem_ratio = record.rem_sleep / (record.duration * 60) * 100
        if rem_ratio < 15:
            issues.append('REM睡眠不足')
            suggestions.append('REM睡眠与记忆整合相关，建议规律作息以改善REM睡眠质量')
        else:
            score += 15
            analysis['interpretation'].append(f'✓ REM睡眠正常 ({rem_ratio:.0f}%)')
    
    # 4. 清醒次数评估 - 10分
    if record.awake_time and record.awake_time > 0:
        if record.awake_time > 60:
            issues.append('夜间清醒时间较长')
            suggestions.append('夜间频繁醒来可能与呼吸暂停或睡眠环境有关，建议检查卧室环境')
        elif record.awake_time > 30:
            score += 5
            analysis['interpretation'].append(f'清醒时间 {record.awake_time:.0f} 分钟')
        else:
            score += 10
            analysis['interpretation'].append(f'✓ 夜间清醒次数少 ({record.awake_time:.0f}分钟)')
    
    # 5. 血氧评估 - 10分
    if record.min_spo2 and record.min_spo2 > 0:
        if record.min_spo2 < 90:
            issues.append('夜间血氧偏低')
            suggestions.append('血氧低于90%可能提示睡眠呼吸暂停，建议咨询医生')
        elif record.avg_spo2 and record.avg_spo2 > 0:
            score += 10
            analysis['interpretation'].append(f'✓ 血氧正常 (平均{record.avg_spo2:.0f}%)')
    
    # 6. 心率评估 - 10分
    if record.sleep_hr_avg and record.sleep_hr_avg > 0:
        if record.sleep_hr_avg > 70:
            issues.append('睡眠心率偏高')
            suggestions.append('睡眠心率偏高可能与压力、运动不足或咖啡因摄入有关')
        elif record.sleep_hr_avg < 45:
            issues.append('睡眠心率偏低')
            suggestions.append('如果您不是运动员，这可能需要咨询医生')
        else:
            score += 10
            analysis['interpretation'].append(f'✓ 睡眠心率正常 ({record.sleep_hr_avg}次/分)')
    
    # 7. 如果没有智能手表数据，使用质量评分
    if not has_watch_data and record.quality:
        # 质量分数占剩余权重
        quality_score = record.quality * 6  # 质量10分 -> 60分
        analysis['interpretation'].append(f'基于您的睡眠质量自评 ({record.quality}/10)')
    
    # 限制分数在100以内
    score = min(score, 100)
    
    # 如果分数太低但有时长数据，使用时长估算
    if score < 30 and record.duration:
        # 根据时长重新估算
        if record.duration >= 7 and record.duration <= 9:
            score = 60 + (record.quality or 5) * 3 if record.quality else 70
        elif record.duration >= 6:
            score = 40 + (record.quality or 5) * 4 if record.quality else 50
    
    # 生成综合评语
    if score >= 85:
        summary = '优秀'
    elif score >= 70:
        summary = '良好'
    elif score >= 50:
        summary = '一般'
    else:
        summary = '需改善'
    
    analysis['score'] = max(1, score)  # 至少1分
    analysis['summary'] = f'本次睡眠{summary} (评分: {analysis["score"]}/100)'
    
    if issues:
        analysis['issues'] = issues
    analysis['suggestions'] = suggestions[:3]  # 最多返回3条建议
    
    return analysis


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
        start_time=now_bj(),
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
    
    record.end_time = now_bj()
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
@track_page_view('健康新闻')
def news():
    """健康新闻页面"""
    category = request.args.get('category')
    
    query = HealthNews.query
    if category:
        query = query.filter_by(category=category)
    
    news_items = query.order_by(HealthNews.published_at.desc()).limit(20).all()
    
    return render_template('news.html', news_items=news_items, current_category=category)


# ==================== 页面访问统计 ====================

@app.route('/page-stats')
@login_required
def page_stats():
    """页面访问统计"""
    days = request.args.get('days', 7, type=int)
    
    # 获取页面访问统计
    stats = PageView.get_page_stats(user_id=current_user.id, days=days)
    
    # 计算总计
    total_views = sum(s.view_count for s in stats)
    
    # 获取每日趋势
    start_date = now_bj() - timedelta(days=days)
    
    # 直接用 Python 处理，避免数据库函数兼容性问题
    all_views = PageView.query.filter(
        PageView.user_id == current_user.id,
        PageView.viewed_at >= start_date
    ).all()
    
    # 按日期分组
    daily_data = {}
    for v in all_views:
        day = v.viewed_at.strftime('%Y-%m-%d')
        daily_data[day] = daily_data.get(day, 0) + 1
    
    daily_views = sorted(daily_data.items())
    
    # 获取最近访问记录
    recent_views = PageView.query.filter_by(user_id=current_user.id).order_by(
        PageView.viewed_at.desc()
    ).limit(20).all()
    
    return render_template('page_stats.html', 
                         stats=stats,
                         total_views=total_views,
                         daily_views=daily_views,
                         recent_views=recent_views,
                         days=days)


@app.route('/api/page-stats')
@login_required
def api_page_stats():
    """页面统计API"""
    days = request.args.get('days', 7, type=int)
    stats = PageView.get_page_stats(user_id=current_user.id, days=days)
    
    return jsonify({
        'stats': [
            {
                'page_name': s.page_name,
                'endpoint': s.endpoint,
                'view_count': s.view_count,
                'last_viewed': s.last_viewed.strftime('%Y-%m-%d %H:%M') if s.last_viewed else None
            } for s in stats
        ]
    })


# ==================== 个人设置 ====================

@app.route('/profile', methods=['GET', 'POST'])
@login_required
@track_page_view('个人设置')
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
else:
    # PythonAnywhere WSGI 模式
    with app.app_context():
        init_database()
