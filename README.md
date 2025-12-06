# 问卷星自动填写系统

一个基于 Flask 的问卷自动填写平台，支持 AI 智能填写和权重配置。

## 功能特性

- 🔐 用户注册/登录系统
- 📝 问卷自动填写
- 🤖 AI 智能填写支持
- ⚙️ 权重配置
- 💰 积分系统
- 👨‍💼 管理员后台
- 📊 填写记录追踪

## 快速部署到网络（5分钟）

### 前置条件
- GitHub 账号（免费）
- Render 账号（免费）

### 第1步：推送代码到 GitHub

```bash
cd pythonProject/wjx_survey
git init
git add .
git commit -m "wjx_survey deployment"
git remote add origin https://github.com/Annoyinghh/wjx_survey.git
git branch -M main
git push -u origin main
```

### 第2步：在 Render 创建数据库

1. 访问 https://render.com
2. 点击 "New +" → " "
3. 填写：
   - Name: `wjx-survey-db`
   - Database: `wjx_survey`
   - Region: 选择离你最近的
4. 创建后复制 **Internal Database URL**

### 第3步：在 Render 创建 Web Service

1. 点击 "New +" → "Web Service"
2. 连接 GitHub 仓库 `wjx_survey`
3. 配置：
   - Name: `wjx-survey`
   - Root Directory: `pythonProject/wjx_survey`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn app:app`
4. 点击 "Create Web Service"

### 第4步：配置环境变量

在 Web Service 的 "Environment" 中添加：

```
DATABASE_URL=postgresql://user:password@host:port/database
FLASK_ENV=production
SECRET_KEY=your-random-secret-key
```

### 第5步：初始化数据库

部署完成后，在 Web Service 页面点击 "Shell"，运行以下命令之一：

**方式A（推荐）：**
```bash
python init_db.py
```

**方式B：**
```bash
python -c "from user import init_db; init_db()"
```

看到 "✓ 数据库初始化成功！" 即可。

### 第6步：访问应用

Render 会分配 URL，格式如：`https://wjx-survey.onrender.com`

## 本地开发

### 1. 克隆项目
```bash
git clone https://github.com/your-username/wjx_survey.git
cd wjx_survey
```

### 2. 创建虚拟环境
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

### 3. 安装依赖
```bash
pip install -r requirements.txt
```

### 4. 配置环境变量
```bash
cp .env.example .env
# 编辑 .env 文件，配置数据库连接
```

### 5. 初始化数据库
```bash
python init_db.py
```

### 6. 运行应用
```bash
python app.py
```

访问 http://localhost:5000

## 默认账号

初始化后的默认管理员账号：
- **用户名**: Bear
- **密码**: xzx123456

⚠️ **请立即修改密码！**

## 项目结构

```
wjx_survey/
├── app.py                 # Flask 主应用
├── user.py               # 用户认证模块
├── config.py             # 配置管理
├── survey_parser.py      # 问卷解析
├── survey_filler.py      # 问卷填写
├── requirements.txt      # 依赖列表
├── Procfile             # Render 部署配置
├── runtime.txt          # Python 版本
├── .env.example         # 环境变量示例
├── init_db.py           # 数据库初始化脚本
└── templates/           # HTML 模板
    ├── login.html
    ├── register.html
    ├── index.html
    └── admin.html
```

## 数据库

使用 PostgreSQL（云端部署）或 MySQL（本地开发）

### 主要表结构

| 表名 | 说明 |
|------|------|
| users | 用户账号 |
| admins | 管理员账号 |
| survey_records | 问卷填写记录 |
| points_log | 积分变化日志 |

## API 端点

### 认证
- `POST /user/register` - 用户注册
- `POST /user/login` - 用户登录
- `POST /user/logout` - 登出
- `GET /user/profile` - 获取用户信息

### 问卷
- `POST /parse` - 解析问卷
- `POST /submit` - 提交填写任务
- `GET /progress` - 获取进度
- `POST /stop` - 停止任务

### 记录
- `GET /survey-records` - 获取填写记录
- `GET /points-log` - 获取积分日志

### 管理员
- `GET /admin/users` - 获取用户列表
- `POST /admin/user/<id>/points` - 修改积分
- `POST /admin/add-user` - 添加用户
- `DELETE /admin/user/<id>` - 删除用户

## 环境变量

```env
# Render 自动提供
DATABASE_URL=postgresql://user:password@host:port/database

# 或手动配置
DB_TYPE=postgresql
PG_HOST=localhost
PG_PORT=5432
PG_USER=postgres
PG_PASSWORD=postgres
PG_NAME=wjx_survey

# Flask 配置
FLASK_ENV=production
SECRET_KEY=your-secret-key
```

## 常见问题

### Q: 部署失败怎么办？
A: 查看 Render Web Service 的 "Logs" 标签找到错误信息。

### Q: 如何更新代码？
A: 修改代码后 push 到 GitHub，Render 会自动重新部署。

### Q: 数据会丢失吗？
A: 不会，PostgreSQL 数据库会持久化保存。

### Q: 免费吗？
A: 完全免费！Render 提供免费的 Web Service 和 PostgreSQL。

### Q: 如何修改管理员密码？
A: 登录管理员账号后在个人资料页面修改。

### Q: 为什么问卷星上没有显示答卷？
A: 当前使用 HTTP 请求方式提交，问卷星可能需要 JavaScript 处理。建议改用 Selenium 来模拟真实浏览器行为。

### Q: 如何改进提交成功率？
A: 
1. 使用 Selenium 替代 HTTP 请求
2. 添加更多的请求头和参数
3. 实现重试机制
4. 添加验证码识别功能

## 许可证

MIT License

## 更新日志

### v1.0.0 (2025-12-06)
- 初始版本发布
- PostgreSQL 数据库支持
- 完整的用户认证系统
- 问卷自动填写功能
- 管理员后台
