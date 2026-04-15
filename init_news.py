#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
初始化健康新闻数据
"""
import sys
sys.path.insert(0, '/home/caisa/ssy')

from app import app, init_news
from models import db, HealthNews

print("=" * 50)
print("初始化健康新闻")
print("=" * 50)

with app.app_context():
    # 检查现有新闻
    existing = HealthNews.query.count()
    print(f"\n现有新闻: {existing} 条")
    
    if existing == 0:
        print("\n开始初始化新闻...")
        init_news()
        
        # 验证
        news = HealthNews.query.all()
        print(f"\n[OK] 共初始化 {len(news)} 条新闻")
        for n in news[:5]:
            print(f"  - {n.title[:40]}...")
    else:
        print("\n新闻数据已存在，跳过初始化")
        print("\n当前新闻列表:")
        for n in HealthNews.query.limit(5).all():
            print(f"  - {n.title[:40]}...")

print("\n" + "=" * 50)
print("完成!")
print("=" * 50)
