# -*- coding: utf-8 -*-
"""
强制重新加载数据库 - 删除并重新创建
"""
import os
import sys

# 获取项目路径
project_path = '/home/caisa/ssy'
db_path = os.path.join(project_path, 'entropy_food.db')

print(f"项目路径: {project_path}")
print(f"数据库路径: {db_path}")

# 删除旧的数据库文件
if os.path.exists(db_path):
    try:
        os.remove(db_path)
        print(f"[OK] 已删除旧数据库: {db_path}")
    except Exception as e:
        print(f"[ERROR] 删除数据库失败: {e}")
        sys.exit(1)
else:
    print("[INFO] 数据库文件不存在，将创建新数据库")

# 切换到项目目录
os.chdir(project_path)
sys.path.insert(0, project_path)

# 重新创建所有表
try:
    from app import app
    from models import db
    
    with app.app_context():
        db.create_all()
        print("[OK] 数据库表已重新创建")
        
        # 验证表结构
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        print(f"\n现有表: {tables}")
        
        # 检查 users 表的列
        if 'users' in tables:
            columns = inspector.get_columns('users')
            column_names = [col['name'] for col in columns]
            print(f"\nusers 表列: {column_names}")
            
            if 'is_admin' in column_names:
                print("[OK] is_admin 列已存在")
            else:
                print("[ERROR] is_admin 列不存在")
                sys.exit(1)
        
        # 同步食物数据
        print("\n正在同步食物数据...")
        from baidu_ai import FOOD_NUTRITION_DB
        from models import Food
        
        count = 0
        for food_name, nutrition in FOOD_NUTRITION_DB.items():
            existing = Food.query.filter_by(name=food_name, is_custom=False).first()
            if not existing:
                food = Food(
                    name=food_name,
                    calories=nutrition.get('calories', 0),
                    protein=nutrition.get('protein', 0),
                    carbs=nutrition.get('carbs', 0),
                    fat=nutrition.get('fat', 0),
                    category=nutrition.get('category', '其他'),
                    is_custom=False
                )
                db.session.add(food)
                count += 1
                if count % 100 == 0:
                    db.session.commit()
                    print(f"  已导入 {count} 条...")
        
        db.session.commit()
        print(f"\n[OK] 成功导入 {count} 条食物记录")
        
except Exception as e:
    print(f"[ERROR] 数据库创建失败: {e}")
    import traceback
    print(traceback.format_exc())
    sys.exit(1)

print("\n[OK] 数据库修复完成！请刷新网页测试。")
