import os
from datetime import timedelta

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'entropy-food-source-secret-key-2024'
    # 使用绝对路径确保数据库位置一致
    BASE_DIR = os.path.abspath(os.path.dirname(os.path.abspath(__file__)))
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or f'sqlite:///{os.path.join(BASE_DIR, "entropy_food.db")}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    PERMANENT_SESSION_LIFETIME = timedelta(days=30)
    
    # OpenAI API配置
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY') or ''
    
    # 上传文件配置
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    
    # 新闻RSS源 - 中文健康新闻
    NEWS_SOURCES = [
        'http://www.chinahealth.org.cn/rss/',
        'https://www.cn-healthcare.com/rss/news.xml',
        'http://www.jiankang.cn/rss.xml',
    ]
    
    # 备用的中文健康新闻源（如RSS不可用时的静态数据）
    FALLBACK_NEWS = [
        {'title': '《中国居民膳食指南》最新发布，指导健康饮食', 'source': '中国营养学会', 'category': 'nutrition'},
        {'title': '研究发现：每天走7000步可显著降低心血管疾病风险', 'source': '中华医学会', 'category': 'exercise'},
        {'title': '专家提示：保证7-8小时睡眠有助于增强免疫力', 'source': '中国睡眠研究会', 'category': 'sleep'},
        {'title': '最新研究：适量饮茶可延缓大脑衰老', 'source': '中国农业大学', 'category': 'nutrition'},
        {'title': '运动医学指南：老年人适合的四种运动方式', 'source': '中国运动医学杂志', 'category': 'exercise'},
        {'title': '睡眠专家建议：睡前避免使用电子设备', 'source': '北京睡眠研究中心', 'category': 'sleep'},
        {'title': '营养学新发现：膳食纤维对肠道健康的重要性', 'source': '中国营养学会', 'category': 'nutrition'},
        {'title': '研究表明：冥想可有效减轻压力和焦虑', 'source': '中华心理学会', 'category': 'research'},
        {'title': '健康体重管理：BMI指数的新标准解读', 'source': '中国疾控中心', 'category': 'research'},
        {'title': '运动与长寿：规律运动可将寿命延长3-5年', 'source': '北京大学公共卫生学院', 'category': 'exercise'},
        {'title': '睡眠质量评估：如何判断自己的睡眠是否健康', 'source': '中国睡眠研究会', 'category': 'sleep'},
        {'title': '营养专家推荐：每周摄入25种以上食物更健康', 'source': '中国营养学会', 'category': 'nutrition'},
    ]
    
    # 食物数据库API
    USDA_API_KEY = os.environ.get('USDA_API_KEY') or ''
    
    # 百度AI配置（用于图像识别）
    # 需要在百度智能云创建应用获取: https://ai.baidu.com/
    BAIDU_API_KEY = 'f94AtRCSUm5ndsdLObTIi2r6'
    BAIDU_SECRET_KEY = 'lWCx48CJ1X3ut2ULtMn30vfIqAEIZd82'
    
    # 应用配置
    APP_NAME = '熵食源'
    APP_VERSION = '1.0.0'
