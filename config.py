import os
from urllib.parse import urlparse
from dotenv import load_dotenv

# 优先加载本地 .env 文件，如果不存在则加载 .env.local
if os.path.exists('.env'):
    load_dotenv('.env')
elif os.path.exists('.env.local'):
    load_dotenv('.env.local')

# 获取运行环境（local 或 production）
ENV = os.getenv('FLASK_ENV', 'local')

# 数据库配置逻辑
# 1. 如果有 DATABASE_URL（Render 云端），使用 PostgreSQL
# 2. 否则根据 DB_TYPE 选择（本地开发）
if os.getenv('DATABASE_URL'):
    # Render 云端：使用 DATABASE_URL
    db_url = urlparse(os.getenv('DATABASE_URL'))
    POSTGRESQL_CONFIG = {
        'host': db_url.hostname,
        'port': db_url.port or 5432,
        'user': db_url.username,
        'password': db_url.password,
        'database': db_url.path[1:] if db_url.path else 'wjx_survey'
    }
    DB_TYPE = 'postgresql'
    print(f"[CONFIG] 使用 PostgreSQL (DATABASE_URL)")
else:
    # 本地开发：根据 DB_TYPE 选择
    DB_TYPE = os.getenv('DB_TYPE', 'mysql')
    
    # PostgreSQL 配置
    POSTGRESQL_CONFIG = {
        'host': os.getenv('PG_HOST', 'localhost'),
        'port': int(os.getenv('PG_PORT', 5432)),
        'user': os.getenv('PG_USER', 'postgres'),
        'password': os.getenv('PG_PASSWORD', 'postgres'),
        'database': os.getenv('PG_NAME', 'wjx_survey')
    }
    
    # MySQL 配置
    MYSQL_CONFIG = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': int(os.getenv('DB_PORT', 3306)),
        'user': os.getenv('DB_USER', 'root'),
        'password': os.getenv('DB_PASSWORD', '123456'),
        'database': os.getenv('DB_NAME', 'wjx_survey'),
        'charset': 'utf8mb4',
        'autocommit': True
    }
    
    print(f"[CONFIG] 使用 {DB_TYPE.upper()} (本地开发)")

# 如果没有定义 MYSQL_CONFIG（云端环境），创建一个空的
if 'MYSQL_CONFIG' not in locals():
    MYSQL_CONFIG = {}

# Flask 配置
SECRET_KEY = os.getenv('SECRET_KEY', 'wjx_survey_secret_key')
DEBUG = os.getenv('DEBUG', 'True').lower() == 'true' if ENV == 'local' else False
