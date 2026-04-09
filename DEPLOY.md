# 熵食源 - 部署指南

## 本地运行

### 1. 安装依赖

```bash
cd 熵食源
pip install -r requirements.txt
```

### 2. 运行应用

```bash
python app.py
```

### 3. 访问应用

打开浏览器访问: http://localhost:5000

---

## 部署到 PythonAnywhere

### 方法一：从 GitHub 部署（推荐）

#### 步骤 1: 创建 GitHub 仓库

1. 访问 [GitHub](https://github.com) 并登录
2. 点击右上角 "+" -> "New repository"
3. 仓库名称: `entropy-food`
4. 选择 Public 或 Private
5. 点击 "Create repository"

#### 步骤 2: 推送代码到 GitHub

```bash
cd 熵食源
git init
git add .
git commit -m "Initial commit - 熵食源 v1.0"
git branch -M main
git remote add origin https://github.com/yourusername/entropy-food.git
git push -u origin main
```

#### 步骤 3: 注册 PythonAnywhere

1. 访问 [PythonAnywhere](https://www.pythonanywhere.com)
2. 注册免费账号（或登录已有账号）
3. 点击 "Bash" 打开控制台

#### 步骤 4: 从 GitHub 拉取代码

```bash
# 在 PythonAnywhere 控制台执行
cd ~
git clone https://github.com/yourusername/entropy-food.git entropy-food
cd entropy-food
```

#### 步骤 5: 创建虚拟环境并安装依赖

```bash
mkvirtualenv --python=/usr/bin/python3.11 entropy-food
pip install -r requirements.txt
```

#### 步骤 6: 配置 Web 应用

1. 在 PythonAnywhere 仪表盘点击 "Web"
2. 点击 "Add a new web app"
3. 选择 "Manual configuration"
4. 选择 Python 3.11
5. 点击 "Next"

#### 步骤 7: 配置 WSGI 文件

1. 点击 WSGI configuration file 链接
2. 删除原有内容，替换为:

```python
import os
import sys

path = '/home/yourusername/entropy-food'
if path not in sys.path:
    sys.path.insert(0, path)

from wsgi import app as application
```

3. 点击 "Save"

#### 步骤 8: 配置静态文件

1. 在 Web 页面找到 "Static files"
2. 点击 "Enter URL"
3. URL: `/static/`
4. Directory: `/home/yourusername/entropy-food/static`
5. 点击 "Save"

#### 步骤 9: 重启应用

1. 点击 "Reload web app"
2. 访问 `https://yourusername.pythonanywhere.com`

---

### 方法二：手动部署

如果你不想使用 GitHub，可以直接通过上传文件部署：

1. 在 PythonAnywhere 创建文件夹
2. 使用文件管理器上传所有项目文件
3. 按照上面的步骤配置虚拟环境和 Web 应用

---

## 配置自定义域名（可选）

1. 在 PythonAnywhere Web 页面找到 "Custom domains"
2. 添加你的域名
3. 在你的域名 DNS 设置中添加 CNAME 记录指向 `yourusername.pythonanywhere.com`

---

## 故障排除

### 数据库初始化问题

如果遇到数据库错误，执行：

```bash
cd ~/entropy-food
python -c "from app import app, init_database; init_database()"
```

### 依赖安装问题

如果某些依赖安装失败，尝试：

```bash
pip install --upgrade pip
pip install -r requirements.txt --no-cache-dir
```

### 静态文件不显示

检查 WSGI 配置中的路径是否正确，并确保 static 文件夹存在。

---

## 更新代码

### 从 GitHub 更新

```bash
cd ~/entropy-food
git pull origin main
pip install -r requirements.txt
# 重启 Web 应用
```

---

## 安全建议

1. **设置环境变量**：在生产环境中，设置以下环境变量：
   - `SECRET_KEY`: Flask 密钥
   - `DATABASE_URL`: 数据库连接字符串
   - `OPENAI_API_KEY`: 如果使用 AI 功能

2. **HTTPS**：PythonAnywhere 免费版自动提供 HTTPS

3. **定期备份**：定期导出数据库文件

---

## 技术支持

- GitHub Issues: https://github.com/yourusername/entropy-food/issues
- PythonAnywhere Help: https://help.pythonanywhere.com/

---

## License

MIT License - 欢迎贡献代码！
