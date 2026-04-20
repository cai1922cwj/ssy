"""
Sleep module extension migration script
Add smart watch data support fields to SleepRecord table
"""
import sqlite3
import os

def migrate():
    db_path = os.path.join(os.path.dirname(__file__), 'entropy_food.db')
    
    # Connect to database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get current table structure
    cursor.execute("PRAGMA table_info(sleep_records)")
    columns = [col[1] for col in cursor.fetchall()]
    
    print(f"Current sleep_records columns: {columns}")
    
    # New columns to add
    new_columns = {
        'deep_sleep': 'REAL DEFAULT 0',
        'light_sleep': 'REAL DEFAULT 0',
        'rem_sleep': 'REAL DEFAULT 0',
        'awake_time': 'REAL DEFAULT 0',
        'avg_spo2': 'REAL DEFAULT 0',
        'min_spo2': 'REAL DEFAULT 0',
        'spo2_below_90_minutes': 'REAL DEFAULT 0',
        'sleep_hr_avg': 'INTEGER DEFAULT 0',
        'sleep_hr_min': 'INTEGER DEFAULT 0',
        'sleep_hr_max': 'INTEGER DEFAULT 0',
        'sleep_score': 'INTEGER DEFAULT 0',
        'data_source': 'TEXT DEFAULT "manual"',
        'source_device': 'TEXT',
        'sleep_stages_detail': 'TEXT'
    }
    
    # Add missing columns
    added = []
    for col_name, col_type in new_columns.items():
        if col_name not in columns:
            try:
                cursor.execute(f"ALTER TABLE sleep_records ADD COLUMN {col_name} {col_type}")
                added.append(col_name)
                print(f"[OK] Added column: {col_name}")
            except sqlite3.Error as e:
                print(f"[X] Add column failed {col_name}: {e}")
    
    conn.commit()
    conn.close()
    
    if added:
        print(f"\nSuccess: {len(added)} new columns added: {added}")
    else:
        print("\nAll columns already exist, no migration needed.")
    
    print("\nMigration completed!")

if __name__ == '__main__':
    migrate()
