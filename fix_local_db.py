"""修复本地数据库：添加 food_nature 字段"""
from app import app, db
from models import Food
from sqlalchemy import text

def fix_local_db():
    with app.app_context():
        # 检查字段是否存在
        result = db.session.execute(text("PRAGMA table_info(foods)"))
        columns = [row[1] for row in result]
        
        if 'food_nature' not in columns:
            print("添加 food_nature 字段...")
            db.session.execute(text("ALTER TABLE foods ADD COLUMN food_nature VARCHAR(10) DEFAULT 'neutral'"))
            db.session.commit()
            print("food_nature 字段添加成功！")
        else:
            print("food_nature 字段已存在")
        
        # 检查 exercises 表是否有 description 字段
        result = db.session.execute(text("PRAGMA table_info(exercises)"))
        columns = [row[1] for row in result]
        
        if 'description' not in columns:
            print("添加 description 字段...")
            db.session.execute(text("ALTER TABLE exercises ADD COLUMN description TEXT DEFAULT ''"))
            db.session.commit()
            print("description 字段添加成功！")
        else:
            print("description 字段已存在")
        
        print("数据库修复完成！")

if __name__ == "__main__":
    fix_local_db()
