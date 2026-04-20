"""
Weight module fix script for PythonAnywhere
Ensure all required columns exist in weight_records and bmi_records tables
"""
import sqlite3
import os

def fix_weight_db():
    db_path = os.path.expanduser('~/entropy-food/entropy_food.db')
    
    if not os.path.exists(db_path):
        db_path = 'entropy_food.db'
        if not os.path.exists(db_path):
            print("Database not found!")
            return False
    
    print(f"Using database: {db_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check weight_records table
    cursor.execute("PRAGMA table_info(weight_records)")
    weight_cols = {col[1]: col for col in cursor.fetchall()}
    print(f"\nweight_records columns: {list(weight_cols.keys())}")
    
    # Required columns for weight_records
    weight_required = {
        'id': 'INTEGER PRIMARY KEY',
        'user_id': 'INTEGER NOT NULL',
        'weight': 'REAL NOT NULL',
        'body_fat': 'REAL',
        'muscle_mass': 'REAL',
        'water': 'REAL',
        'date': 'TEXT',
        'notes': 'TEXT',
        'created_at': 'TEXT'
    }
    
    # Add missing columns to weight_records
    for col_name, col_def in weight_required.items():
        if col_name not in weight_cols:
            try:
                cursor.execute(f"ALTER TABLE weight_records ADD COLUMN {col_name} {col_def}")
                print(f"  [+] Added: {col_name}")
            except sqlite3.Error as e:
                print(f"  [!] Failed: {col_name} - {e}")
    
    # Check bmi_records table
    cursor.execute("PRAGMA table_info(bmi_records)")
    bmi_cols = {col[1]: col for col in cursor.fetchall()}
    print(f"\nbmi_records columns: {list(bmi_cols.keys())}")
    
    # Required columns for bmi_records
    bmi_required = {
        'id': 'INTEGER PRIMARY KEY',
        'user_id': 'INTEGER NOT NULL',
        'bmi': 'REAL NOT NULL',
        'category': 'TEXT',
        'height': 'REAL',
        'weight': 'REAL',
        'age': 'INTEGER',
        'gender': 'TEXT',
        'date': 'TEXT',
        'created_at': 'TEXT'
    }
    
    # Add missing columns to bmi_records
    for col_name, col_def in bmi_required.items():
        if col_name not in bmi_cols:
            try:
                cursor.execute(f"ALTER TABLE bmi_records ADD COLUMN {col_name} {col_def}")
                print(f"  [+] Added: {col_name}")
            except sqlite3.Error as e:
                print(f"  [!] Failed: {col_name} - {e}")
    
    # Check users table for weight column
    cursor.execute("PRAGMA table_info(users)")
    user_cols = {col[1]: col for col in cursor.fetchall()}
    print(f"\nusers columns: {list(user_cols.keys())}")
    
    if 'weight' not in user_cols:
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN weight REAL DEFAULT 65.0")
            print("  [+] Added: weight column to users")
        except sqlite3.Error as e:
            print(f"  [!] Failed: weight - {e}")
    
    conn.commit()
    conn.close()
    
    print("\n[OK] Database check completed!")
    return True

if __name__ == '__main__':
    print("=" * 50)
    print("Weight Module Database Fix")
    print("=" * 50)
    fix_weight_db()
