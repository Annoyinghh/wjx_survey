#!/usr/bin/env python
"""
云端完整设置脚本
用法：在 Render Shell 中运行 python setup_cloud.py
"""

import os
import sys
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

print("=" * 70)
print("Render 云端数据库完整设置")
print("=" * 70)

# 第1步：验证配置
print("\n[步骤1] 验证数据库配置...")
from config import DB_TYPE, DB_CONFIG, POSTGRESQL_CONFIG

print(f"  ✓ 数据库类型: {DB_TYPE}")
print(f"  ✓ 主机: {DB_CONFIG.get('host')}")
print(f"  ✓ 端口: {DB_CONFIG.get('port')}")
print(f"  ✓ 用户: {DB_CONFIG.get('user')}")
print(f"  ✓ 数据库: {DB_CONFIG.get('database')}")

# 第2步：测试连接
print("\n[步骤2] 测试数据库连接...")
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
    conn.close()
except Exception as e:
    print(f"  ✗ 连接失败: {e}")
    sys.exit(1)

# 第3步：初始化数据库表
print("\n[步骤3] 初始化数据库表...")
try:
    from user import init_db
    init_db()
    print("  ✓ 数据库表创建成功！")
except Exception as e:
    print(f"  ✗ 初始化失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 第4步：验证表
print("\n[步骤4] 验证数据库表...")
try:
    import psycopg2
    conn = psycopg2.connect(
        host=DB_CONFIG['host'],
        port=DB_CONFIG['port'],
        user=DB_CONFIG['user'],
        password=DB_CONFIG['password'],
        database=DB_CONFIG['database']
    )
    cur = conn.cursor()
    
    # 查询所有表
    cur.execute("""
        SELECT table_name FROM information_schema.tables 
        WHERE table_schema = 'public'
    """)
    tables = cur.fetchall()
    
    print(f"  ✓ 找到 {len(tables)} 个表:")
    for table in tables:
        print(f"    - {table[0]}")
    
    # 验证关键表
    required_tables = ['users', 'admins', 'survey_records', 'points_log']
    for table in required_tables:
        cur.execute(f"SELECT COUNT(*) FROM {table}")
        count = cur.fetchone()[0]
        print(f"    - {table}: {count} 条记录")
    
    conn.close()
    print("  ✓ 所有表验证成功！")
except Exception as e:
    print(f"  ✗ 验证失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 70)
print("✓ 云端数据库设置完成！")
print("=" * 70)
print("\n默认管理员账号：")
print("  用户名: Bear")
print("  密码: xzx123456")
print("\n⚠️  请立即修改管理员密码！")
print("\n现在可以访问应用了：https://wjx-survey.onrender.com")
print("=" * 70)
