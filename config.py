import os
from dotenv import load_dotenv

# 优先加载本地 .env 文件（本地开发）
if os.path.exists('.env'):
    load_dotenv('.env')
elif os.path.exists('.env.local'):
    load_dotenv('.env.local')

# 获取运行环境
ENV = os.getenv('FLASK_ENV', 'local')

# 数据库配置 - MySQL
DB_TYPE = 'mysql'

MYSQL_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', 3306)),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', '123456'),
    'database': os.getenv('DB_NAME', 'wjx_survey'),
    'charset': 'utf8mb4',
    'autocommit': True
}

DB_CONFIG = MYSQL_CONFIG

print(f"[CONFIG] 使用 MySQL (本地开发)")

# Flask 配置
SECRET_KEY = os.getenv('SECRET_KEY', 'wjx_survey_secret_key')
DEBUG = os.getenv('DEBUG', 'True').lower() == 'true' if ENV == 'local' else False

# 问卷填写器使用 HTTP 模式（云端兼容）
print(f"[CONFIG] 填写器模式: HTTP")
