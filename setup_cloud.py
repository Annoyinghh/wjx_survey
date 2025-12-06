#!/usr/bin/env python
"""
云端完整设置脚本
用法：在 Render Shell 中运行 python setup_cloud.py
"""

import os
import sys
from dotenv import load_dotenv
from urllib.parse import urlparse

# 加载环境变量
load_dotenv()

print("=" * 70)
print("Render 云端数据库完整设置")
print("=" * 70)

# 第1步：验证配置
print("\n[步骤1] 验证数据库配置...")

# 使用外部数据库 URL
db_url = os.getenv('DATABASE_URL') or "postgresql://wjx_survey_db_ld9r_user:awy3dVvk7u77Y0WG25rbbc5cqD9NeYyS@dpg-d4pv20e3jp1c73985c6g-a.singapore-postgres.render.com/wjx_survey_db_ld9r"

db_parsed = urlparse(db_url)
print(f"  ✓ 数据库类型: PostgreSQL")
print(f"  ✓ 主机: {db_parsed.hostname}")
print(f"  ✓ 端口: {db_parsed.port or 5432}")
print(f"  ✓ 用户: {db_parsed.username}")
print(f"  ✓ 数据库: {db_parsed.path[1:] if db_parsed.path else 'unknown'}")

# 第2步：测试连接
print("\n[步骤2] 测试数据库连接...")
try:
    import psycopg2
    conn = psycopg2.connect(db_url)
    print("  ✓ PostgreSQL 连接成功！")
    conn.close()
except Exception as e:
    print(f"  ✗ 连接失败: {e}")
    sys.exit(1)

# 第3步：初始化数据库表
print("\n[步骤3] 初始化数据库表...")
try:
    import psycopg2
    conn = psycopg2.connect(db_url)
    c = conn.cursor()
    
    # 创建用户表
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        email VARCHAR(128) UNIQUE NOT NULL,
        username VARCHAR(64) NOT NULL,
        password VARCHAR(128) NOT NULL,
        points INT DEFAULT 0,
        last_signin DATE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # 创建管理员表
    c.execute('''CREATE TABLE IF NOT EXISTS admins (
        id SERIAL PRIMARY KEY,
        username VARCHAR(64) UNIQUE NOT NULL,
        password VARCHAR(128) NOT NULL,
        phone VARCHAR(20),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # 创建问卷记录表
    c.execute('''CREATE TABLE IF NOT EXISTS survey_records (
        id SERIAL PRIMARY KEY,
        user_id INT NOT NULL,
        survey_url VARCHAR(500) NOT NULL,
        status VARCHAR(20),
        points_deducted INT DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # 创建积分日志表
    c.execute('''CREATE TABLE IF NOT EXISTS points_log (
        id SERIAL PRIMARY KEY,
        user_id INT NOT NULL,
        points_change INT NOT NULL,
        reason VARCHAR(200),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # 创建默认管理员
    import hashlib
    default_password = hashlib.sha256('xzx123456'.encode('utf-8')).hexdigest()
    c.execute('SELECT * FROM admins WHERE username=%s', ('Bear',))
    if not c.fetchone():
        c.execute('INSERT INTO admins (username, password) VALUES (%s, %s)', ('Bear', default_password))
    
    conn.commit()
    conn.close()
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
    conn = psycopg2.connect(db_url)
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
