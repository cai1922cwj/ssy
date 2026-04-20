"""修复本地数据库：添加缺失的字段（纯SQL方式）"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'entropy_food.db')

def fix_local_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 检查 foods 表的字段
    cursor.execute("PRAGMA table_info(foods)")
    food_columns = [row[1] for row in cursor.fetchall()]
    print(f"foods 表现有字段: {food_columns}")
    
    if 'food_nature' not in food_columns:
        print("添加 food_nature 字段到 foods 表...")
        cursor.execute("ALTER TABLE foods ADD COLUMN food_nature VARCHAR(10) DEFAULT 'neutral'")
        conn.commit()
        print("food_nature 字段添加成功！")
    else:
        print("food_nature 字段已存在")
    
    # 检查 exercises 表的字段
    cursor.execute("PRAGMA table_info(exercises)")
    exercise_columns = [row[1] for row in cursor.fetchall()]
    print(f"\nexercises 表现有字段: {exercise_columns}")
    
    if 'description' not in exercise_columns:
        print("添加 description 字段到 exercises 表...")
        cursor.execute("ALTER TABLE exercises ADD COLUMN description TEXT DEFAULT ''")
        conn.commit()
        print("description 字段添加成功！")
    else:
        print("description 字段已存在")
    
    # 检查 exercises 表是否有 met_value 字段
    if 'met_value' not in exercise_columns:
        print("添加 met_value 字段到 exercises 表...")
        cursor.execute("ALTER TABLE exercises ADD COLUMN met_value FLOAT DEFAULT 5.0")
        conn.commit()
        print("met_value 字段添加成功！")
    else:
        print("met_value 字段已存在")
    
    conn.close()
    print("\n数据库修复完成！")

if __name__ == "__main__":
    fix_local_db()
