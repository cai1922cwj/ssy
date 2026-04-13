"""
清理食物数据库并重新同步中文食物数据
"""
import sys
sys.path.append('/home/casa/mysite')

from app import app, db
from models import Food
from baidu_ai import FOOD_NUTRITION_DB

def reset_foods():
    with app.app_context():
        # 1. 删除所有系统食物（is_custom=False）
        print("正在删除所有系统食物数据...")
        deleted = Food.query.filter_by(is_custom=False).delete()
        print(f"已删除 {deleted} 条系统食物记录")
        
        # 2. 从 baidu_ai.py 导入中文食物数据
        print("\n正在导入中文食物数据...")
        count = 0
        for name, nutrition in FOOD_NUTRITION_DB.items():
            # 跳过英文名（包含英文字母的食物名）
            import re
            if re.search(r'[a-zA-Z]', name):
                continue
                
            food = Food(
                name=name,
                calories=nutrition['calories'],
                protein=nutrition['protein'],
                carbs=nutrition['carbs'],
                fat=nutrition['fat'],
                category=nutrition['category'],
                is_custom=False
            )
            db.session.add(food)
            count += 1
            
            if count % 100 == 0:
                print(f"  已导入 {count} 条...")
        
        db.session.commit()
        print(f"\n成功导入 {count} 条中文食物记录")
        
        # 3. 统计各分类数量
        print("\n各分类统计：")
        categories = db.session.query(Food.category, db.func.count(Food.id)).filter_by(is_custom=False).group_by(Food.category).all()
        for cat, num in sorted(categories):
            print(f"  {cat}: {num} 条")

if __name__ == '__main__':
    reset_foods()
