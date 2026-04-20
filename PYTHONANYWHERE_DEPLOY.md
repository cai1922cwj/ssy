# 熵食源 - PythonAnywhere 部署指南

## 一、准备工作

### 1.1 登录 PythonAnywhere
- 访问 https://www.pythonanywhere.com
- 登录您的账号

### 1.2 本地需要上传的文件清单

```
核心文件：
├── app.py
├── models.py
├── config.py
├── wsgi.py
├── requirements.txt

模板文件：
└── templates/
    ├── base.html
    ├── index.html
    ├── diet.html
    ├── add_diet.html      ← 本次新增
    ├── sleep.html         ← 本次更新
    ├── exercise.html
    └── ... (其他25个html文件)

静态文件：
└── static/
    └── ... (CSS、JS文件)

数据库：
└── instance/
    └── entropy_food.db
```

---

## 二、开始部署

### 2.1 创建目录结构

在 PythonAnywhere Files 页面，依次创建以下目录：

```
/home/你的用户名/mysite/
├── templates/
├── static/
└── instance/
```

### 2.2 上传核心文件

在 **Files** 页面，上传以下文件到 `/home/你的用户名/mysite/`：

1. `app.py`
2. `models.py`
3. `config.py`
4. `wsgi.py`
5. `requirements.txt`

### 2.3 上传模板文件

1. 进入 `mysite/templates/` 目录
2. 上传所有 `.html` 文件（共25个）

### 2.4 上传静态文件

1. 进入 `mysite/static/` 目录
2. 上传所有 CSS 和 JS 文件

### 2.5 上传数据库

1. 进入 `mysite/instance/` 目录
2. 上传 `entropy_food.db`

---

## 三、配置 Web App

### 3.1 打开 Web 标签

点击顶部 **Web** 标签，进入 Web 应用配置页面。

### 3.2 配置 WSGI 文件

点击 **WSGI configuration file** 链接，编辑文件：

```python
import sys
import os

# 添加项目路径
path = '/home/你的用户名/mysite'
if path not in sys.path:
    sys.path.insert(0, path)

from wsgi import app as application
```

### 3.3 配置 Static Files

在 Static Files 部分添加：

| URL | Directory |
|-----|-----------|
| `/static/` | `/home/你的用户名/mysite/static` |

---

## 四、安装依赖

### 4.1 打开 Bash

点击 **Consoles** → **Bash**

### 4.2 安装依赖

```bash
cd ~/mysite
pip install -r requirements.txt
```

等待安装完成...

---

## 五、重启 Web App

### 5.1 重新加载

回到 **Web** 页面，点击 **Reload** 按钮刷新应用。

### 5.2 测试访问

在浏览器访问：`https://你的用户名.pythonanywhere.com`

---

## 六、本次更新内容

### 需要覆盖上传的文件（本次修改）

| 文件 | 说明 |
|------|------|
| `app.py` | 修复批量添加饮食记录功能 |
| `templates/add_diet.html` | 新增多食物批量添加界面 |
| `models.py` | SleepRecord 新增智能手表字段 |
| `templates/sleep.html` | 睡眠页面UI优化 |
| `entropy_food.db` | 更新数据库结构 |

### 更新后操作

1. 上传上述文件覆盖旧文件
2. 在 Bash 中运行数据库迁移（如需要）：
   ```bash
   cd ~/mysite
   flask db upgrade
   ```
3. 回到 Web 页面点击 **Reload**

---

## 七、常见问题

### Q1: Import Error
如果遇到导入错误，检查：
- 所有 .py 文件是否都上传了
- `__init__.py` 是否存在

### Q2: 数据库错误
如果数据库报错，尝试：
1. 删除 `instance/entropy_food.db`
2. 在 Bash 中重新初始化：
   ```bash
   python init_db.py
   ```
   ⚠️ 注意：这会清空所有数据！

### Q3: 静态文件不显示
确保 Static Files 配置正确，URL 必须以 `/static/` 开头。

---

## 八、部署完成检查清单

- [ ] 所有核心文件已上传
- [ ] 所有模板文件已上传
- [ ] 静态文件已上传
- [ ] 数据库已上传
- [ ] 依赖已安装
- [ ] WSGI 文件已配置
- [ ] Static Files 已配置
- [ ] Web App 已 Reload
- [ ] 网站可正常访问
