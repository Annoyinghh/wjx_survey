# Render部署指南

## 前置条件

1. GitHub账户
2. Render账户（https://render.com）
3. 项目已上传到GitHub

## 部署步骤

### 步骤1：准备GitHub仓库

```bash
# 在项目根目录初始化git
cd pythonProject/wjx_survey
git init

# 添加所有文件
git add .

# 提交
git commit -m "Initial commit"

# 添加远程仓库（替换为你的GitHub仓库地址）
git remote add origin https://github.com/你的用户名/wjx_survey.git

# 推送到GitHub
git branch -M main
git push -u origin main
```

### 步骤2：在Render上创建账户

1. 访问 https://render.com
2. 使用GitHub账户登录
3. 授权Render访问你的GitHub仓库

### 步骤3：创建Web Service

1. 点击 "New +" → "Web Service"
2. 选择你的GitHub仓库 `wjx_survey`
3. 填写配置：
   - **Name**: wjx-survey
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
   - **Plan**: Free

### 步骤4：添加环境变量

在Web Service的"Environment"标签中添加：

```
FLASK_ENV=production
FLASK_SECRET_KEY=your-secret-key-here
DB_HOST=your-database-host
DB_PORT=3306
DB_USER=your-db-user
DB_PASSWORD=your-db-password
DB_NAME=wjx_survey
```

### 步骤5：创建PostgreSQL数据库

1. 点击 "New +" → "PostgreSQL"
2. 填写配置：
   - **Name**: wjx-survey-db
   - **Plan**: Free
3. 创建后，复制连接信息到环境变量

**注意**：Render免费版只支持PostgreSQL，不支持MySQL。需要修改代码使用PostgreSQL。

### 步骤6：修改数据库配置（使用PostgreSQL）

如果使用PostgreSQL，需要修改user.py：

```python
import psycopg2
from psycopg2 import pool

# 创建连接池
connection_pool = psycopg2.pool.SimpleConnectionPool(
    1, 20,
    host=os.getenv('DB_HOST'),
    port=int(os.getenv('DB_PORT', 5432)),
    user=os.getenv('DB_USER'),
    password=os.getenv('DB_PASSWORD'),
    database=os.getenv('DB_NAME')
)
```

### 步骤7：部署

1. 点击 "Deploy"
2. 等待部署完成（通常需要2-5分钟）
3. 部署完成后，你会获得一个公网URL

## 部署后的配置

### 初始化数据库

部署完成后，需要初始化数据库：

```bash
# 通过Render的Shell运行初始化脚本
python setup_database.py
```

或者在Render的Shell中执行SQL脚本：

```bash
psql -U your-db-user -h your-db-host -d wjx_survey < init_database.sql
```

### 访问应用

部署完成后，你可以通过以下URL访问应用：

```
https://your-app-name.onrender.com
```

## 常见问题

### Q: 部署失败，显示"Build failed"

A: 检查以下几点：
1. `requirements.txt` 是否存在且格式正确
2. `Procfile` 是否存在且内容正确
3. 所有依赖是否都在 `requirements.txt` 中

### Q: 应用启动后立即崩溃

A: 检查以下几点：
1. 环境变量是否正确设置
2. 数据库连接是否正常
3. 查看Render的日志了解具体错误

### Q: 数据库连接失败

A: 检查以下几点：
1. 数据库是否已创建
2. 环境变量中的数据库信息是否正确
3. 数据库是否允许远程连接

### Q: 免费版有什么限制

A: Render免费版的限制：
- 每月15GB带宽
- 0.5GB内存
- 共享CPU
- 30天无活动后自动休眠
- 数据库只支持PostgreSQL

### Q: 如何防止应用休眠

A: 
1. 升级到付费版
2. 或者使用外部服务定期访问应用（如UptimeRobot）

## 更新应用

每次更新代码后：

```bash
git add .
git commit -m "Update message"
git push origin main
```

Render会自动检测到更新并重新部署。

## 监控和日志

1. 在Render Dashboard中查看应用状态
2. 点击应用名称查看详细日志
3. 使用"Logs"标签查看实时日志

## 性能优化

1. 使用CDN加速静态文件
2. 启用缓存
3. 优化数据库查询
4. 使用连接池

## 安全建议

1. 不要在代码中硬编码敏感信息
2. 使用环境变量存储密钥
3. 定期更新依赖
4. 启用HTTPS（Render自动提供）
5. 设置强密码

## 成本估算

Render免费版：
- Web Service: 免费
- PostgreSQL: 免费（有限制）
- 总成本: $0/月

付费版（如需更多资源）：
- Web Service: $7+/月
- PostgreSQL: $15+/月
- 总成本: $22+/月

## 支持

- Render文档: https://render.com/docs
- 社区论坛: https://render.com/community
- 邮件支持: support@render.com
