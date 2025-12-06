# Render快速部署指南（5分钟）

## 快速步骤

### 1️⃣ 推送到GitHub

```bash
cd pythonProject/wjx_survey
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/你的用户名/wjx_survey.git
git branch -M main
git push -u origin main
```

### 2️⃣ 访问Render

1. 打开 https://render.com
2. 用GitHub账户登录
3. 授权Render

### 3️⃣ 创建Web Service

1. 点击 "New +" → "Web Service"
2. 选择 `wjx_survey` 仓库
3. 填写：
   - Name: `wjx-survey`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn app:app`
   - Plan: **Free**
4. 点击 "Create Web Service"

### 4️⃣ 添加环境变量

在"Environment"标签中添加：

```
FLASK_ENV=production
FLASK_SECRET_KEY=your-secret-key-12345
```

### 5️⃣ 创建数据库

1. 点击 "New +" → "PostgreSQL"
2. Name: `wjx-survey-db`
3. Plan: **Free**
4. 创建后，复制连接信息

### 6️⃣ 更新Web Service环境变量

添加数据库信息：

```
DB_HOST=your-db-host.render.com
DB_PORT=5432
DB_USER=your-db-user
DB_PASSWORD=your-db-password
DB_NAME=wjx_survey
```

### 7️⃣ 等待部署

- 部署通常需要2-5分钟
- 在Logs标签中查看进度
- 完成后会显示绿色的"Live"

### 8️⃣ 访问应用

```
https://wjx-survey.onrender.com
```

## 常见错误及解决

| 错误 | 解决方案 |
|------|--------|
| Build failed | 检查requirements.txt是否存在 |
| Application failed to start | 检查环境变量是否正确 |
| Database connection error | 检查数据库信息是否正确 |
| Port already in use | 重启应用 |

## 下一步

1. ✅ 初始化数据库
2. ✅ 测试登录功能
3. ✅ 测试问卷填写
4. ✅ 配置自定义域名（可选）

## 有用的链接

- 📚 完整部署指南: `RENDER_DEPLOYMENT.md`
- 🔧 Render文档: https://render.com/docs
- 💬 社区支持: https://render.com/community

## 成本

✅ 完全免费！

- Web Service: $0
- PostgreSQL: $0
- 总计: $0/月

## 需要帮助？

1. 查看Render的Logs标签
2. 阅读完整部署指南
3. 访问Render社区论坛
