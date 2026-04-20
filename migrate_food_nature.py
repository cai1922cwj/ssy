"""
为食物数据库添加中医食性属性的迁移脚本
五性分类：寒、凉、平、温、热
"""

from app import app, db
from models import Food

# 中医食性分类字典
# 格式：食物名称 -> 食性
FOOD_NATURE_MAP = {
    # ==================== 寒性食物 ====================
    # 蔬菜类
    '苦瓜': 'cold',
    '黄瓜': 'cold',
    '冬瓜': 'cold',
    '西红柿': 'cold',
    '茄子': 'cold',
    '芹菜': 'cold',
    '菠菜': 'cold',
    '茭白': 'cold',
    '莲藕': 'cold',
    '马齿苋': 'cold',
    '蕨菜': 'cold',
    '空心菜': 'cold',
    '苋菜': 'cold',
    '芦荟': 'cold',
    
    # 水果类
    '西瓜': 'cold',
    '梨': 'cold',
    '香蕉': 'cold',
    '柿子': 'cold',
    '奇异果': 'cold',
    '猕猴桃': 'cold',
    '柚子': 'cold',
    '甘蔗': 'cold',
    '橙子': 'cold',
    '荸荠': 'cold',
    '甜瓜': 'cold',
    '火龙果': 'cold',
    
    # 饮品类
    '绿茶': 'cold',
    '菊花茶': 'cold',
    '金银花茶': 'cold',
    '凉茶': 'cold',
    
    # 水产类
    '螃蟹': 'cold',
    '田螺': 'cold',
    '蛤蜊': 'cold',
    '蛏子': 'cold',
    
    # ==================== 凉性食物 ====================
    # 蔬菜类
    '白菜': 'cool',
    '油菜': 'cool',
    '白萝卜': 'cool',
    '豆芽': 'cool',
    '豆腐': 'cool',
    '丝瓜': 'cool',
    '莴笋': 'cool',
    '紫菜': 'cool',
    '海带': 'cool',
    '竹笋': 'cool',
    '芦笋': 'cool',
    '西兰花': 'cool',
    '菜花': 'cool',
    '生菜': 'cool',
    '黄豆': 'cool',
    
    # 水果类
    '苹果': 'cool',
    '草莓': 'cool',
    '葡萄': 'cool',
    '芒果': 'cool',
    '椰子': 'cool',
    '枇杷': 'cool',
    '菠萝': 'cool',
    '柠檬': 'cool',
    '山楂': 'cool',
    '百香果': 'cool',
    
    # 肉类
    '鸭肉': 'cool',
    '兔肉': 'cool',
    '猪肉': 'cool',  # 猪肉性平偏凉
    
    # 谷物类
    '薏米': 'cool',
    '绿豆': 'cool',
    '荞麦': 'cool',
    
    # 饮品类
    '酸奶': 'cool',
    '豆浆': 'cool',
    '蜂蜜': 'cool',
    
    # 蛋奶类
    '牛奶': 'cool',
    '鸡蛋': 'cool',  # 鸡蛋性平偏凉
    
    # ==================== 平性食物 ====================
    # 谷物类
    '大米': 'neutral',
    '小米': 'neutral',
    '小麦': 'neutral',
    '糯米': 'neutral',
    '玉米': 'neutral',
    '燕麦': 'neutral',
    '黑米': 'neutral',
    '红薯': 'neutral',
    '土豆': 'neutral',
    '山药': 'neutral',
    '芋头': 'neutral',
    
    # 蔬菜类
    '南瓜': 'neutral',
    '胡萝卜': 'neutral',
    '香菇': 'neutral',
    '木耳': 'neutral',
    '银耳': 'neutral',
    '四季豆': 'neutral',
    '豌豆': 'neutral',
    '黑豆': 'neutral',
    '红豆': 'neutral',
    
    # 水果类
    '橘子': 'neutral',
    '橙子': 'neutral',
    '桃子': 'neutral',
    '李子': 'neutral',
    '杏子': 'neutral',
    '樱桃': 'neutral',
    '菠萝蜜': 'neutral',
    '无花果': 'neutral',
    '石榴': 'neutral',
    '木瓜': 'neutral',
    '荔枝': 'neutral',
    '桂圆': 'neutral',
    '红枣': 'neutral',
    '枸杞': 'neutral',
    
    # 肉类
    '牛肉': 'neutral',
    '鸡肉': 'neutral',
    '鸡蛋': 'neutral',
    '鹅肉': 'neutral',
    '鸽肉': 'neutral',
    
    # 水产类
    '鱼肉': 'neutral',
    '鲫鱼': 'neutral',
    '鲤鱼': 'neutral',
    '草鱼': 'neutral',
    '鲈鱼': 'neutral',
    '带鱼': 'neutral',
    '黄鱼': 'neutral',
    '虾': 'neutral',
    '海参': 'neutral',
    
    # 坚果类
    '花生': 'neutral',
    '栗子': 'neutral',
    '核桃': 'neutral',
    '莲子': 'neutral',
    '芡实': 'neutral',
    '腰果': 'neutral',
    '杏仁': 'neutral',
    
    # 调料类
    '白糖': 'neutral',
    '红糖': 'neutral',
    '冰糖': 'neutral',
    
    # ==================== 温性食物 ====================
    # 蔬菜类
    '韭菜': 'warm',
    '葱': 'warm',
    '蒜': 'warm',
    '姜': 'warm',
    '香菜': 'warm',
    '洋葱': 'warm',
    '南瓜': 'warm',  # 老南瓜偏温
    '刀豆': 'warm',
    '扁豆': 'warm',
    
    # 水果类
    '荔枝': 'warm',
    '桂圆': 'warm',
    '红枣': 'warm',
    '山楂': 'warm',
    '樱桃': 'warm',
    '石榴': 'warm',
    '桃子': 'warm',
    '杏子': 'warm',
    '榴莲': 'warm',
    '龙眼': 'warm',
    '金桔': 'warm',
    
    # 肉类
    '羊肉': 'warm',
    '狗肉': 'warm',
    '鹿肉': 'warm',
    '鸡肝': 'warm',
    '牛肝': 'warm',
    
    # 谷物类
    '糯米': 'warm',
    '紫米': 'warm',
    '高粱': 'warm',
    
    # 坚果类
    '板栗': 'warm',
    '松子': 'warm',
    '开心果': 'warm',
    '夏威夷果': 'warm',
    
    # 调料类
    '花椒': 'warm',
    '八角': 'warm',
    '桂皮': 'warm',
    '胡椒': 'warm',
    '孜然': 'warm',
    '辣椒': 'warm',  # 辣椒为热性
    '陈皮': 'warm',
    
    # 饮品类
    '红茶': 'warm',
    '普洱熟茶': 'warm',
    '桂花茶': 'warm',
    '玫瑰花茶': 'warm',
    
    # ==================== 热性食物 ====================
    # 调料类
    '辣椒': 'hot',
    '干辣椒': 'hot',
    '花椒': 'hot',
    '胡椒': 'hot',
    '芥末': 'hot',
    '肉桂': 'hot',
    
    # 其他
    '白酒': 'hot',
    '烈酒': 'hot',
    '咖啡': 'hot',
    '榴莲': 'hot',  # 榴莲为热性
}


def migrate():
    """执行迁移"""
    with app.app_context():
        # 检查字段是否存在
        try:
            # 尝试查询所有食物
            foods = Food.query.all()
            print(f"共有 {len(foods)} 种食物")
        except Exception as e:
            print(f"查询失败: {e}")
            return
        
        updated_count = 0
        
        for food in foods:
            food_name = food.name
            
            # 首先尝试精确匹配
            if food_name in FOOD_NATURE_MAP:
                food.food_nature = FOOD_NATURE_MAP[food_name]
                updated_count += 1
                print(f"  更新: {food_name} -> {food.food_nature}")
                continue
            
            # 尝试模糊匹配（包含关系）
            matched = False
            for key, nature in FOOD_NATURE_MAP.items():
                if key in food_name or food_name in key:
                    food.food_nature = nature
                    updated_count += 1
                    print(f"  模糊匹配: {food_name} -> {food.food_nature} (基于: {key})")
                    matched = True
                    break
            
            if not matched:
                # 根据类别设置默认值
                category_nature_map = {
                    'vegetable': 'neutral',
                    'fruit': 'neutral',
                    'meat': 'neutral',
                    'seafood': 'neutral',
                    'grain': 'neutral',
                    'beverage': 'neutral',
                }
                default_nature = category_nature_map.get(food.category, 'neutral')
                if food.food_nature == 'neutral' or food.food_nature is None:
                    food.food_nature = default_nature
                print(f"  默认: {food_name} -> {food.food_nature} (类别: {food.category})")
        
        db.session.commit()
        print(f"\n迁移完成！共更新 {updated_count} 种食物的食性信息")


if __name__ == '__main__':
    migrate()
