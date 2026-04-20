"""修复本地数据库：添加 page_views 表"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'entropy_food.db')

def fix_local_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 检查 page_views 表是否存在
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='page_views'")
    exists = cursor.fetchone()
    
    if not exists:
        print("创建 page_views 表...")
        cursor.execute("""
            CREATE TABLE page_views (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                endpoint VARCHAR(100),
                page_name VARCHAR(100),
                page_url VARCHAR(255),
                referrer VARCHAR(255),
                user_agent VARCHAR(255),
                viewed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)
        conn.commit()
        print("page_views 表创建成功！")
    else:
        print("page_views 表已存在")
    
    conn.close()
    print("数据库修复完成！")

if __name__ == "__main__":
    fix_local_db()
