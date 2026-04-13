"""
初始化数据库表结构
"""
import sys
sys.path.append('/home/caisa/ssy')

from app import app, db
from models import *

def init_database():
    with app.app_context():
        print("正在创建数据库表...")
        db.create_all()
        print("数据库表创建完成！")
        
        # 检查表是否创建成功
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        print(f"\n现有表: {tables}")

if __name__ == '__main__':
    init_database()
