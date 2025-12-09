import os
from dotenv import load_dotenv

# 优先加载本地 .env 文件（本地开发）
if os.path.exists('.env'):
    load_dotenv('.env')
elif os.path.exists('.env.local'):
    load_dotenv('.env.local')

# 获取运行环境
ENV = os.getenv('FLASK_ENV', 'local')

# 总是定义MySQL配置（本地开发用）
MYSQL_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', 3306)),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', '123456'),
    'database': os.getenv('DB_NAME', 'wjx_survey'),
    'charset': 'utf8mb4',
    'autocommit': True
}

# 检查是否有DATABASE_URL（云端PostgreSQL）
DATABASE_URL = os.getenv('DATABASE_URL')

if DATABASE_URL:
    # 云端模式：使用PostgreSQL
    DB_TYPE = 'postgresql'
    print(f"[CONFIG] 使用 PostgreSQL (云端模式)")
    
    # PostgreSQL配置
    POSTGRESQL_CONFIG = {
        'database_url': DATABASE_URL
    }
    DB_CONFIG = POSTGRESQL_CONFIG
else:
    # 本地模式：使用MySQL
    DB_TYPE = 'mysql'
    print(f"[CONFIG] 使用 MySQL (本地开发)")
    DB_CONFIG = MYSQL_CONFIG

# Flask 配置
SECRET_KEY = os.getenv('SECRET_KEY', 'wjx_survey_secret_key')
DEBUG = os.getenv('DEBUG', 'True').lower() == 'true' if ENV == 'local' else False

# 问卷填写器使用 selenium  模式（云端兼容）
print(f"[CONFIG] 填写器模式: selenium ")
