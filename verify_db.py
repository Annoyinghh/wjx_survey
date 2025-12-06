#!/usr/bin/env python
"""
验证数据库连接脚本
用法：python verify_db.py
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()

print("=" * 70)
print("数据库连接验证")
print("=" * 70)

# 检查环境变量
print("\n[步骤1] 检查环境变量...")
database_url = os.getenv('DATABASE_URL')
flask_env = os.getenv('FLASK_ENV')

print(f"  DATABASE_URL: {'已设置' if database_url else '未设置'}")
print(f"  FLASK_ENV: {flask_env or '未设置'}")

if database_url:
    print(f"  DATABASE_URL 值: {database_url[:50]}...")

# 导入配置
print("\n[步骤2] 导入配置...")
try:
    from config import DB_TYPE, DB_CONFIG, POSTGRESQL_CONFIG
    print(f"  ✓ 配置导入成功")
    print(f"  DB_TYPE: {DB_TYPE}")
    print(f"  Host: {DB_CONFIG.get('host')}")
    print(f"  Database: {DB_CONFIG.get('database')}")
except Exception as e:
    print(f"  ✗ 配置导入失败: {e}")
    sys.exit(1)

# 测试连接
print("\n[步骤3] 测试数据库连接...")
try:
    import psycopg2
    conn = psycopg2.connect(
        host=DB_CONFIG['host'],
        port=DB_CONFIG['port'],
        user=DB_CONFIG['user'],
        password=DB_CONFIG['password'],
        database=DB_CONFIG['database']
    )
    print("  ✓ PostgreSQL 连接成功！")
    
    # 查询表
    cur = conn.cursor()
    cur.execute("""
        SELECT table_name FROM information_schema.tables 
        WHERE table_schema = 'public'
    """)
    tables = cur.fetchall()
    print(f"  ✓ 找到 {len(tables)} 个表:")
    for table in tables:
        print(f"    - {table[0]}")
    
    conn.close()
except Exception as e:
    print(f"  ✗ 连接失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 70)
print("✓ 验证完成！")
print("=" * 70)
