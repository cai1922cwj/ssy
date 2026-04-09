# 熵食源 - 在线食物营养分析APP

<div align="center">
    <h1>🍎 熵食源</h1>
    <p><strong>智能营养分析，健康生活伴侣</strong></p>
    <p>
        <img src="https://img.shields.io/badge/Python-3.11+-blue.svg" alt="Python">
        <img src="https://img.shields.io/badge/Flask-3.0-green.svg" alt="Flask">
        <img src="https://img.shields.io/badge/License-MIT-orange.svg" alt="License">
    </p>
</div>

---

## 📋 功能概览

### 核心功能

| 功能 | 描述 |
|------|------|
| 🍎 **食物营养信息** | 快速查询食物热量与营养成分，支持自定义食物 |
| 🏃 **运动饮食管理** | 记录运动消耗，追踪食物摄入，计算净热量 |
| 🤖 **AI健康分析** | 智能分析饮食习惯，给出个性化建议 |
| 📰 **权威健康动态** | 自动导入国际权威机构饮食相关研究 |

### 记录方式

- 📷 **拍照识别** - 快速拍照记录食物
- ✏️ **文字输入** - 手动搜索并添加食物
- 🎤 **语音输入** - 语音描述食物（浏览器支持）
- 📊 **条形码扫描** - 扫描商品条形码识别

### 健康管理

- 🍵 **茶与咖啡建议** - 科学的饮品饮用指导
- 😴 **睡眠管理** - 记录睡眠，分析饮食影响
- ⚖️ **体重追踪** - 记录体重变化趋势
- ⏰ **轻断食** - 间歇性禁食方案（16:8, 18:6等）

### 🎉 趣味功能

> **寿命计算器** - 根据健康生活方式，计算可延长的寿命年数！

根据BMI、运动习惯、饮食记录等因素，估算坚持健康生活可额外获得的寿命。

---

## 🚀 快速开始

### 本地运行

```bash
# 1. 克隆项目
git clone https://github.com/yourusername/entropy-food.git
cd entropy-food

# 2. 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. 安装依赖
pip install -r requirements.txt

# 4. 运行应用
python app.py

# 5. 访问应用
# 打开浏览器访问: http://localhost:5000
```

### Docker 运行

```bash
# 使用 Docker Compose
docker-compose up -d
```

---

## 📁 项目结构

```
entropy-food/
├── app.py              # 主应用文件 (Flask路由)
├── models.py           # 数据模型 (SQLAlchemy)
├── config.py           # 配置文件
├── wsgi.py             # WSGI入口 (PythonAnywhere)
├── requirements.txt    # Python依赖
├── README.md           # 项目说明
├── DEPLOY.md           # 部署指南
│
├── templates/           # HTML模板
│   ├── base.html       # 基础模板
│   ├── index.html      # 首页
│   ├── diet.html       # 饮食记录
│   ├── foods.html      # 食物库
│   ├── exercise.html   # 运动记录
│   ├── sleep.html      # 睡眠管理
│   ├── beverages.html  # 茶与咖啡
│   ├── fasting.html    # 轻断食
│   ├── ai_analysis.html # AI分析
│   ├── news.html       # 健康新闻
│   ├── profile.html    # 个人设置
│   ├── login.html      # 登录
│   └── register.html   # 注册
│
└── static/             # 静态资源
    ├── css/
    │   └── style.css   # 自定义样式 (淡蓝色主题)
    └── js/
        └── app.js     # JavaScript功能
```

---

## 🎨 设计特色

### 淡蓝色主题

应用采用清新的淡蓝色作为主色调，给用户带来舒适、健康的视觉体验。

### 卡片式布局

- 圆角卡片设计
- 悬浮动效
- 清晰的视觉层次

### 响应式设计

完美适配桌面端和移动端设备。

---

## 🔧 技术栈

### 后端
- **Python 3.11+**
- **Flask 3.0** - Web框架
- **SQLAlchemy** - ORM
- **Flask-Login** - 用户认证

### 前端
- **HTML5/CSS3**
- **Bootstrap 5.3** - UI框架
- **Bootstrap Icons** - 图标库
- **JavaScript (原生)**

### 数据库
- **SQLite** - 开发环境
- **PostgreSQL** - 生产环境

### 部署
- **PythonAnywhere** - Web托管
- **GitHub** - 代码托管

---

## 📊 数据模型

### 用户 (User)
- 基本信息（年龄、性别、身高、体重）
- 活动水平与目标
- 热量与营养素目标

### 食物 (Food)
- 营养成分数据
- 分类与条形码
- 自定义食物支持

### 记录
- 饮食记录 (FoodRecord)
- 运动记录 (ExerciseRecord)
- 体重记录 (WeightRecord)
- 睡眠记录 (SleepRecord)

---

## 📈 使用示例

### 1. 记录饮食

```
1. 点击"添加记录"按钮
2. 搜索食物或扫描条形码
3. 输入份量（克）
4. 选择餐次（早餐/午餐/晚餐/零食）
5. 确认添加
```

### 2. 记录运动

```
1. 进入运动页面
2. 选择运动项目
3. 设置运动时长
4. 系统自动计算消耗热量
```

### 3. 查看分析

```
1. 进入"AI分析"页面
2. 查看近7天数据统计
3. 获取个性化健康建议
4. 查看寿命延长预期
```

---

## 🌐 部署到 PythonAnywhere

详见 [DEPLOY.md](./DEPLOY.md)

### 简要步骤

1. Fork 本项目到 GitHub
2. 登录 PythonAnywhere
3. 打开 Bash 控制台
4. 克隆仓库: `git clone https://github.com/yourusername/entropy-food.git`
5. 创建虚拟环境
6. 安装依赖
7. 配置 Web 应用
8. 启动！

---

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/amazing`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing`)
5. 创建 Pull Request

---

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

---

## 🙏 致谢

- [Flask](https://flask.palletsprojects.com/) - Web框架
- [Bootstrap](https://getbootstrap.com/) - CSS框架
- [Bootstrap Icons](https://icons.getbootstrap.com/) - 图标库
- [PythonAnywhere](https://www.pythonanywhere.com/) - 托管服务

---

## 📞 联系方式

- **GitHub Issues**: [提交问题](https://github.com/yourusername/entropy-food/issues)
- **邮箱**: your.email@example.com

---

<div align="center">
    <p>Made with ❤️ for a healthier world</p>
    <p>&copy; 2024 熵食源 - 让健康饮食更简单</p>
</div>
