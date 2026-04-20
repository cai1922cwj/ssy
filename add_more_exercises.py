"""添加更多运动项目到数据库"""

from app import app, db
from models import Exercise

# 更多运动项目数据（MET值参考：Compendium of Physical Activities）
MORE_EXERCISES = [
    # ===== 有氧运动 (Cardio) =====
    {"name": "慢跑 (6 km/h)", "category": "cardio", "met_value": 6.0, "description": "轻松慢跑"},
    {"name": "慢跑 (8 km/h)", "category": "cardio", "met_value": 9.8, "description": "中等速度跑"},
    {"name": "快跑 (10 km/h)", "category": "cardio", "met_value": 11.5, "description": "快速跑"},
    {"name": "冲刺跑", "category": "cardio", "met_value": 14.5, "description": "全力冲刺"},
    {"name": "快走 (5 km/h)", "category": "cardio", "met_value": 3.5, "description": "快速步行"},
    {"name": "爬山", "category": "cardio", "met_value": 7.8, "description": "负重爬山"},
    {"name": "爬楼梯", "category": "cardio", "met_value": 8.8, "description": "爬楼梯运动"},
    {"name": "跳绳 (慢)", "category": "cardio", "met_value": 8.8, "description": "慢速跳绳"},
    {"name": "跳绳 (快)", "category": "cardio", "met_value": 12.3, "description": "快速跳绳"},
    {"name": "骑自行车 (休闲)", "category": "cardio", "met_value": 4.0, "description": "休闲骑行"},
    {"name": "骑自行车 (15km/h)", "category": "cardio", "met_value": 7.5, "description": "中等速度骑行"},
    {"name": "骑自行车 (20km/h)", "category": "cardio", "met_value": 11.0, "description": "快速骑行"},
    {"name": "游泳 (慢)", "category": "cardio", "met_value": 5.8, "description": "休闲游泳"},
    {"name": "游泳 (自由泳)", "category": "cardio", "met_value": 8.0, "description": "自由泳"},
    {"name": "游泳 (蛙泳)", "category": "cardio", "met_value": 10.0, "description": "蛙泳"},
    {"name": "游泳 (仰泳)", "category": "cardio", "met_value": 7.0, "description": "仰泳"},
    {"name": "游泳 (蝶泳)", "category": "cardio", "met_value": 11.0, "description": "蝶泳"},
    {"name": "打篮球", "category": "cardio", "met_value": 8.0, "description": "篮球比赛"},
    {"name": "篮球 (投篮)", "category": "cardio", "met_value": 4.5, "description": "投篮练习"},
    {"name": "踢足球", "category": "cardio", "met_value": 10.0, "description": "足球比赛"},
    {"name": "踢足球 (守门)", "category": "cardio", "met_value": 6.0, "description": "守门"},
    {"name": "打网球", "category": "cardio", "met_value": 8.0, "description": "网球单打"},
    {"name": "打网球 (双打)", "category": "cardio", "met_value": 6.0, "description": "网球双打"},
    {"name": "打羽毛球", "category": "cardio", "met_value": 5.5, "description": "羽毛球休闲"},
    {"name": "羽毛球 (比赛)", "category": "cardio", "met_value": 7.0, "description": "羽毛球比赛"},
    {"name": "打乒乓球", "category": "cardio", "met_value": 4.0, "description": "乒乓球"},
    {"name": "打排球", "category": "cardio", "met_value": 3.0, "description": "排球休闲"},
    {"name": "打排球 (比赛)", "category": "cardio", "met_value": 6.0, "description": "排球比赛"},
    {"name": "打台球/斯诺克", "category": "cardio", "met_value": 2.5, "description": "台球"},
    {"name": "高尔夫", "category": "cardio", "met_value": 4.3, "description": "高尔夫步行"},
    {"name": "保龄球", "category": "cardio", "met_value": 3.0, "description": "保龄球"},
    {"name": "跳舞 (慢)", "category": "cardio", "met_value": 4.5, "description": "慢节奏舞蹈"},
    {"name": "跳舞 (快)", "category": "cardio", "met_value": 7.8, "description": "快节奏舞蹈"},
    {"name": "广场舞", "category": "cardio", "met_value": 4.0, "description": "广场舞"},
    {"name": "跳广场舞 (快)", "category": "cardio", "met_value": 5.5, "description": "快速广场舞"},
    {"name": "健身操", "category": "cardio", "met_value": 6.0, "description": "有氧健身操"},
    {"name": "搏击操", "category": "cardio", "met_value": 9.8, "description": "搏击操/Kickboxing"},
    {"name": "踏板操", "category": "cardio", "met_value": 7.5, "description": "踏板有氧"},
    {"name": "划船机", "category": "cardio", "met_value": 7.0, "description": "划船机训练"},
    {"name": "椭圆机", "category": "cardio", "met_value": 5.0, "description": "椭圆机"},
    {"name": "动感单车", "category": "cardio", "met_value": 8.0, "description": "动感单车"},
    {"name": "跑步机 (走路)", "category": "cardio", "met_value": 3.5, "description": "跑步机步行"},
    {"name": "跑步机 (跑步)", "category": "cardio", "met_value": 9.8, "description": "跑步机跑步"},
    {"name": "滑雪", "category": "cardio", "met_value": 7.0, "description": "越野滑雪"},
    {"name": "单板滑雪", "category": "cardio", "met_value": 6.0, "description": "单板滑雪"},
    {"name": "滑冰", "category": "cardio", "met_value": 7.0, "description": "滑冰"},
    {"name": "轮滑", "category": "cardio", "met_value": 7.0, "description": "轮滑"},
    {"name": "滑板", "category": "cardio", "met_value": 5.0, "description": "滑板运动"},
    {"name": "冲浪", "category": "cardio", "met_value": 3.0, "description": "冲浪"},
    {"name": "划独木舟", "category": "cardio", "met_value": 4.0, "description": "划独木舟"},
    {"name": "皮划艇", "category": "cardio", "met_value": 5.0, "description": "皮划艇"},
    {"name": "帆船", "category": "cardio", "met_value": 3.0, "description": "帆船"},
    {"name": "登山", "category": "cardio", "met_value": 6.0, "description": "徒步登山"},
    {"name": "远足", "category": "cardio", "met_value": 5.3, "description": "野外远足"},
    {"name": "太极", "category": "cardio", "met_value": 3.0, "description": "太极拳"},
    {"name": "八段锦", "category": "cardio", "met_value": 3.5, "description": "八段锦"},
    {"name": "五禽戏", "category": "cardio", "met_value": 3.5, "description": "五禽戏"},
    {"name": "气功", "category": "cardio", "met_value": 2.5, "description": "气功"},
    {"name": "抖空竹", "category": "cardio", "met_value": 4.0, "description": "抖空竹"},
    {"name": "踢毽子", "category": "cardio", "met_value": 4.0, "description": "踢毽子"},
    {"name": "放风筝", "category": "cardio", "met_value": 2.5, "description": "放风筝"},
    {"name": "飞盘", "category": "cardio", "met_value": 3.0, "description": "飞盘运动"},
    
    # ===== 力量训练 (Strength) =====
    {"name": "举哑铃", "category": "strength", "met_value": 3.5, "description": "哑铃训练"},
    {"name": "卧推", "category": "strength", "met_value": 4.0, "description": "杠铃卧推"},
    {"name": "深蹲", "category": "strength", "met_value": 5.0, "description": "深蹲训练"},
    {"name": "硬拉", "category": "strength", "met_value": 6.0, "description": "硬拉训练"},
    {"name": "引体向上", "category": "strength", "met_value": 5.0, "description": "引体向上"},
    {"name": "俯卧撑", "category": "strength", "met_value": 4.0, "description": "俯卧撑"},
    {"name": "仰卧起坐", "category": "strength", "met_value": 3.0, "description": "仰卧起坐"},
    {"name": "平板支撑", "category": "strength", "met_value": 4.0, "description": "平板支撑"},
    {"name": "卷腹", "category": "strength", "met_value": 3.0, "description": "卷腹"},
    {"name": "臀桥", "category": "strength", "met_value": 3.0, "description": "臀桥训练"},
    {"name": "箭步蹲", "category": "strength", "met_value": 4.5, "description": "箭步蹲"},
    {"name": "腿部推举", "category": "strength", "met_value": 4.0, "description": "腿部推举"},
    {"name": "肩部推举", "category": "strength", "met_value": 3.5, "description": "肩部推举"},
    {"name": "划船训练", "category": "strength", "met_value": 4.0, "description": "坐姿划船"},
    {"name": "二头肌弯举", "category": "strength", "met_value": 3.0, "description": "二头肌弯举"},
    {"name": "三头肌训练", "category": "strength", "met_value": 3.0, "description": "三头肌训练"},
    {"name": "腹肌轮", "category": "strength", "met_value": 5.0, "description": "腹肌轮训练"},
    {"name": "壶铃训练", "category": "strength", "met_value": 6.0, "description": "壶铃训练"},
    {"name": "TRX训练", "category": "strength", "met_value": 5.0, "description": "TRX悬吊训练"},
    {"name": "自重训练", "category": "strength", "met_value": 3.5, "description": "徒手自重训练"},
    {"name": "CrossFit", "category": "strength", "met_value": 12.0, "description": "CrossFit高强度训练"},
    {"name": "功能训练", "category": "strength", "met_value": 5.0, "description": "功能性训练"},
    {"name": "核心训练", "category": "strength", "met_value": 4.0, "description": "核心力量训练"},
    {"name": "阻力带训练", "category": "strength", "met_value": 3.5, "description": "阻力带训练"},
    {"name": "沙袋训练", "category": "strength", "met_value": 5.0, "description": "沙袋训练"},
    
    # ===== 柔韧性/拉伸 (Flexibility) =====
    {"name": "拉伸运动", "category": "flexibility", "met_value": 2.0, "description": "全身拉伸"},
    {"name": "瑜伽", "category": "flexibility", "met_value": 2.5, "description": "哈他瑜伽"},
    {"name": "瑜伽 (力量)", "category": "flexibility", "met_value": 4.0, "description": "力量瑜伽"},
    {"name": "普拉提", "category": "flexibility", "met_value": 3.5, "description": "普拉提"},
    {"name": "拉伸训练", "category": "flexibility", "met_value": 2.0, "description": "柔韧性训练"},
    {"name": "舞蹈拉伸", "category": "flexibility", "met_value": 2.5, "description": "舞蹈拉伸"},
    
    # ===== 休闲活动 (Leisure) =====
    {"name": "散步", "category": "leisure", "met_value": 2.5, "description": "悠闲散步"},
    {"name": "遛狗", "category": "leisure", "met_value": 3.0, "description": "遛狗"},
    {"name": "园艺", "category": "leisure", "met_value": 3.8, "description": "园艺活动"},
    {"name": "钓鱼", "category": "leisure", "met_value": 2.5, "description": "钓鱼"},
    {"name": "木工", "category": "leisure", "met_value": 3.0, "description": "木工活动"},
    {"name": "搬家/搬重物", "category": "leisure", "met_value": 6.5, "description": "搬运重物"},
    {"name": "擦地板", "category": "leisure", "met_value": 3.5, "description": "擦地板"},
    {"name": "吸尘", "category": "leisure", "met_value": 3.3, "description": "吸尘打扫"},
    {"name": "整理房间", "category": "leisure", "met_value": 2.5, "description": "整理房间"},
    {"name": "洗碗", "category": "leisure", "met_value": 2.3, "description": "洗碗"},
    {"name": "做饭", "category": "leisure", "met_value": 2.5, "description": "做饭"},
    {"name": "购物", "category": "leisure", "met_value": 2.3, "description": "逛街购物"},
    {"name": "抱孩子", "category": "leisure", "met_value": 2.0, "description": "抱小孩"},
    {"name": "陪孩子玩", "category": "leisure", "met_value": 3.5, "description": "与孩子玩耍"},
    {"name": "打麻将", "category": "leisure", "met_value": 1.5, "description": "打麻将"},
    {"name": "唱KTV", "category": "leisure", "met_value": 2.0, "description": "KTV唱歌"},
    {"name": "乐器演奏", "category": "leisure", "met_value": 2.0, "description": "演奏乐器"},
    {"name": "书法", "category": "leisure", "met_value": 1.5, "description": "书法练习"},
    {"name": "绘画", "category": "leisure", "met_value": 2.0, "description": "绘画"},
    {"name": "棋类游戏", "category": "leisure", "met_value": 1.5, "description": "下棋"},
    
    # ===== 冬季运动 (Winter Sports) =====
    {"name": "滑雪 (高山)", "category": "winter", "met_value": 6.0, "description": "高山滑雪"},
    {"name": "滑冰 (速滑)", "category": "winter", "met_value": 9.0, "description": "速度滑冰"},
    {"name": "冰球", "category": "winter", "met_value": 8.0, "description": "冰球运动"},
    {"name": "雪地行走", "category": "winter", "met_value": 5.0, "description": "雪地行走"},
    {"name": "雪橇", "category": "winter", "met_value": 4.0, "description": "雪橇运动"},
    
    # ===== 水上运动 (Water Sports) =====
    {"name": "潜水", "category": "water", "met_value": 7.0, "description": "休闲潜水"},
    {"name": "浮潜", "category": "water", "met_value": 3.0, "description": "浮潜"},
    {"name": "水球", "category": "water", "met_value": 10.0, "description": "水球运动"},
    {"name": "水中有氧", "category": "water", "met_value": 5.0, "description": "水中健身"},
    {"name": "水疗/桑拿", "category": "water", "met_value": 1.0, "description": "水疗放松"},
    
    # ===== 搏击运动 (Martial Arts) =====
    {"name": "拳击", "category": "martial", "met_value": 12.8, "description": "拳击训练"},
    {"name": "散打", "category": "martial", "met_value": 10.0, "description": "散打训练"},
    {"name": "跆拳道", "category": "martial", "met_value": 9.0, "description": "跆拳道"},
    {"name": "柔道", "category": "martial", "met_value": 8.0, "description": "柔道训练"},
    {"name": "摔跤", "category": "martial", "met_value": 8.0, "description": "摔跤训练"},
    {"name": "柔术", "category": "martial", "met_value": 6.0, "description": "巴西柔术"},
    {"name": "咏春拳", "category": "martial", "met_value": 5.0, "description": "咏春拳"},
    {"name": "形意拳", "category": "martial", "met_value": 4.5, "description": "形意拳"},
    {"name": "八卦掌", "category": "martial", "met_value": 4.5, "description": "八卦掌"},
    {"name": "剑道", "category": "martial", "met_value": 6.0, "description": "剑道训练"},
    {"name": "射箭", "category": "martial", "met_value": 3.5, "description": "射箭"},
    {"name": "射击", "category": "martial", "met_value": 2.5, "description": "射击运动"},
    {"name": "马术", "category": "martial", "met_value": 5.5, "description": "骑马"},
    {"name": "武术套路", "category": "martial", "met_value": 4.0, "description": "武术套路"},
]

def add_exercises():
    """添加更多运动项目"""
    with app.app_context():
        added_count = 0
        existing_names = {e.name for e in Exercise.query.all()}
        
        for exercise_data in MORE_EXERCISES:
            if exercise_data["name"] not in existing_names:
                exercise = Exercise(
                    name=exercise_data["name"],
                    category=exercise_data["category"],
                    met_value=exercise_data["met_value"],
                    description=exercise_data.get("description", "")
                )
                db.session.add(exercise)
                added_count += 1
            else:
                print(f"已存在: {exercise_data['name']}")
        
        db.session.commit()
        print(f"\n成功添加 {added_count} 个运动项目！")
        print(f"当前共有 {Exercise.query.count()} 个运动项目")

if __name__ == "__main__":
    add_exercises()
