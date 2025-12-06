# Render 云端部署最终设置

## 当前状态

✅ 代码已推送到 GitHub
✅ PostgreSQL 数据库已创建
✅ 应用已部署到 Render

## 需要完成的步骤

### 第1步：在 Render 中设置 DATABASE_URL 环境变量

1. 访问 Render Dashboard
2. 选择 Web Service `wjx-survey`
3. 点击 "Environment" 标签
4. 添加新的环境变量：

| Key | Value |
|-----|-------|
| `DATABASE_URL` | `postgresql://wjx_survey_db_ld9r_user:awy3dVvk7u77Y0WG25rbbc5cqD9NeYyS@dpg-d4pv20e3jp1c73985c6g-a.singapore-postgres.render.com:5432/wjx_survey_db_ld9r` |
| `FLASK_ENV` | `production` |
| `SECRET_KEY` | `your-random-secret-key-here` |

5. 点击 "Save" 保存

### 第2步：等待自动重新部署

Render 会自动检测到环境变量变化，自动重新部署应用。

### 第3步：初始化数据库

部署完成后，在 Render Web Service 的 Shell 中运行：

```bash
python setup_cloud.py
```

这会创建所有必要的表和默认管理员账号。

### 第4步：测试应用

访问 https://wjx-survey.onrender.com

用默认账号登录：
- 用户名: Bear
- 密码: xzx123456

## 本地开发

本地开发时，确保有 MySQL 或 PostgreSQL 运行：

### 使用 MySQL（推荐本地开发）

1. 创建 `.env` 文件：
```env
DB_TYPE=mysql
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=123456
DB_NAME=wjx_survey
FLASK_ENV=development
```

2. 运行应用：
```bash
python app.py
```

### 使用 PostgreSQL（本地开发）

1. 创建 `.env` 文件：
```env
DB_TYPE=postgresql
PG_HOST=localhost
PG_PORT=5432
PG_USER=postgres
PG_PASSWORD=postgres
PG_NAME=wjx_survey
FLASK_ENV=development
```

2. 运行应用：
```bash
python app.py
```

## 故障排查

### 应用显示 500 错误

1. 检查 Render 的 Logs
2. 确保 `DATABASE_URL` 环境变量已设置
3. 确保数据库表已初始化（运行 `python setup_cloud.py`）

### 无法连接数据库

1. 检查 `DATABASE_URL` 是否正确
2. 检查数据库是否在线
3. 检查网络连接

### 忘记管理员密码

在 Render Shell 中运行：
```bash
python setup_cloud.py
```

这会重新创建默认管理员账号。

## 完成！

应用现在应该可以正常使用了。

访问：https://wjx-survey.onrender.com
