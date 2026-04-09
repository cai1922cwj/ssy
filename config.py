import os
from datetime import timedelta

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'entropy-food-source-secret-key-2024'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///entropy_food.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    PERMANENT_SESSION_LIFETIME = timedelta(days=30)
    
    # OpenAI API配置
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY') or ''
    
    # 上传文件配置
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    
    # 新闻RSS源
    NEWS_SOURCES = [
        'https://www.who.int/rss-feeds/news-english.xml',
        'https://www.nih.gov/news-events/news-releases/rss.xml',
        'https://www.hsph.harvard.edu/news/feed/',
        'https://www.nutrition.org/rss-feeds/',
    ]
    
    # 食物数据库API
    USDA_API_KEY = os.environ.get('USDA_API_KEY') or ''
    
    # 应用配置
    APP_NAME = '熵食源'
    APP_VERSION = '1.0.0'
