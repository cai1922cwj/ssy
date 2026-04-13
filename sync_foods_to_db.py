"""
将 baidu_ai.py 中的食物数据同步到数据库
"""
import sys
from app import app, db
from models import Food
from baidu_ai import FOOD_NUTRITION_DB

def sync_foods():
    """同步食物数据到数据库"""
    with app.app_context():
        print(f"开始同步食物数据...")
        print(f"食物库中共有 {len(FOOD_NUTRITION_DB)} 种食物")
        
        # 统计各分类数量
        categories = {}
        for nutrition in FOOD_NUTRITION_DB.values():
            cat = nutrition.get('category', '其他')
            categories[cat] = categories.get(cat, 0) + 1
        
        print("\n各分类数量:")
        for cat, count in sorted(categories.items(), key=lambda x: -x[1]):
            print(f"  {cat}: {count} 种")
        
        # 清空现有食物数据（可选，如果需要保留用户自定义食物，可以注释掉）
        existing_count = Food.query.count()
        print(f"\n数据库中现有 {existing_count} 种食物")
        
        # 删除系统预设的食物（保留用户自定义的）
        Food.query.filter(Food.is_custom == False).delete()
        db.session.commit()
        print("已清空系统预设食物数据")
        
        # 添加新食物
        added_count = 0
        skipped_count = 0
        
        for name, nutrition in FOOD_NUTRITION_DB.items():
            # 检查是否已存在（用户可能已添加）
            existing = Food.query.filter_by(name=name).first()
            if existing:
                skipped_count += 1
                continue
            
            food = Food(
                name=name,
                calories=nutrition.get('calories', 0),
                protein=nutrition.get('protein', 0),
                carbs=nutrition.get('carbs', 0),
                fat=nutrition.get('fat', 0),
                category=nutrition.get('category', '其他'),
                is_custom=False  # 标记为系统预设
            )
            db.session.add(food)
            added_count += 1
            
            # 每100条提交一次
            if added_count % 100 == 0:
                db.session.commit()
                print(f"已添加 {added_count} 种食物...")
        
        db.session.commit()
        
        print(f"\n同步完成!")
        print(f"  - 新增: {added_count} 种")
        print(f"  - 跳过（已存在）: {skipped_count} 种")
        print(f"  - 数据库总计: {Food.query.count()} 种")

if __name__ == '__main__':
    sync_foods()
