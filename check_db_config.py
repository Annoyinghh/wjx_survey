#!/usr/bin/env python
"""
检查数据库配置脚本
用法：python check_db_config.py
"""

import os
from dotenv import load_dotenv

load_dotenv()

print("=" * 60)
print("数据库配置检查")
print("=" * 60)

print(f"\n环境变量：")
print(f"  FLASK_ENV: {os.getenv('FLASK_ENV', '未设置')}")
print(f"  DATABASE_URL: {'已设置' if os.getenv('DATABASE_URL') else '未设置'}")
print(f"  DB_TYPE: {os.getenv('DB_TYPE', '未设置')}")

from config import DB_TYPE, DB_CONFIG, MYSQL_CONFIG, POSTGRESQL_CONFIG

print(f"\n检测到的数据库类型: {DB_TYPE}")

if DB_TYPE == 'postgresql':
    print(f"\nPostgreSQL 配置：")
    print(f"  Host: {DB_CONFIG.get('host')}")
    print(f"  Port: {DB_CONFIG.get('port')}")
    print(f"  User: {DB_CONFIG.get('user')}")
    print(f"  Database: {DB_CONFIG.get('database')}")
    print(f"  Password: {'*' * len(DB_CONFIG.get('password', ''))}")
else:
    print(f"\nMySQL 配置：")
    print(f"  Host: {DB_CONFIG.get('host')}")
    print(f"  Port: {DB_CONFIG.get('port')}")
    print(f"  User: {DB_CONFIG.get('user')}")
    print(f"  Database: {DB_CONFIG.get('database')}")
    print(f"  Password: {'*' * len(DB_CONFIG.get('password', ''))}")

print("\n" + "=" * 60)
print("测试数据库连接...")
print("=" * 60)

try:
    if DB_TYPE == 'postgresql':
        import psycopg2
        conn = psycopg2.connect(
            host=DB_CONFIG['host'],
            port=DB_CONFIG['port'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            database=DB_CONFIG['database']
        )
        print("✓ PostgreSQL 连接成功！")
        conn.close()
    else:
        import pymysql
        conn = pymysql.connect(**DB_CONFIG)
        print("✓ MySQL 连接成功！")
        conn.close()
except Exception as e:
    print(f"✗ 连接失败: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
