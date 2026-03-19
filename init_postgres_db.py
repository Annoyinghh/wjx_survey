#!/usr/bin/env python3
"""
PostgreSQL 数据库初始化脚本
用于清空和重建云端PostgreSQL数据库
"""

import os
import sys
from dotenv import load_dotenv

# 加载环境变量
if os.path.exists('.env'):
    load_dotenv('.env')
elif os.path.exists('.env.local'):
    load_dotenv('.env.local')

DATABASE_URL = os.getenv('DATABASE_URL')

if not DATABASE_URL:
    print("❌ 错误: 未找到 DATABASE_URL 环境变量")
    print("请在 .env 或 .env.local 中设置 DATABASE_URL")
    sys.exit(1)

try:
    import psycopg2
    from psycopg2 import sql
except ImportError:
    print("❌ 错误: psycopg2 未安装")
    print("请运行: pip install psycopg2-binary")
    sys.exit(1)

import hashlib


def hash_password(pw):
    """密码哈希"""
    return hashlib.sha256(pw.encode('utf-8')).hexdigest()


def init_postgres_db():
    """初始化PostgreSQL数据库"""
    try:
        # 连接到PostgreSQL
        conn = psycopg2.connect(DATABASE_URL)
        conn.autocommit = True
        cur = conn.cursor()
        
        print("🔄 正在连接到PostgreSQL数据库...")
        
        # 删除现有表（如果存在）
        print("🗑️  正在清空现有表...")
        tables = [
            'survey_records',
            'points_log',
            'recharge_requests',
            'admins',
            'users'
        ]
        
        for table in tables:
            try:
                cur.execute(f'DROP TABLE IF EXISTS {table} CASCADE')
                print(f"   ✓ 删除表: {table}")
            except Exception as e:
                print(f"   ⚠️  删除表 {table} 失败: {e}")
        
        conn.commit()
        
        # 创建用户表
        print("\n📝 正在创建表...")
        cur.execute('''
            CREATE TABLE users (
                id SERIAL PRIMARY KEY,
                email VARCHAR(128) UNIQUE NOT NULL,
                username VARCHAR(64) NOT NULL,
                password VARCHAR(128) NOT NULL,
                phone VARCHAR(20),
                points INT DEFAULT 0,
                role VARCHAR(32) DEFAULT 'user',
                last_signin DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        print("   ✓ 创建表: users")
        
        # 创建管理员表
        cur.execute('''
            CREATE TABLE admins (
                id SERIAL PRIMARY KEY,
                username VARCHAR(64) UNIQUE NOT NULL,
                password VARCHAR(128) NOT NULL,
                phone VARCHAR(20),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        print("   ✓ 创建表: admins")
        
        # 创建充值申请表
        cur.execute('''
            CREATE TABLE recharge_requests (
                id SERIAL PRIMARY KEY,
                user_id INT NOT NULL,
                amount INT NOT NULL,
                payment_method VARCHAR(32) DEFAULT 'alipay',
                remark VARCHAR(255) DEFAULT '',
                status VARCHAR(32) DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                processed_at TIMESTAMP NULL,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        ''')
        print("   ✓ 创建表: recharge_requests")
        
        # 创建积分日志表
        cur.execute('''
            CREATE TABLE points_log (
                id SERIAL PRIMARY KEY,
                user_id INT NOT NULL,
                points_change INT NOT NULL,
                reason VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        ''')
        print("   ✓ 创建表: points_log")
        
        # 创建问卷记录表
        cur.execute('''
            CREATE TABLE survey_records (
                id SERIAL PRIMARY KEY,
                user_id INT NOT NULL,
                survey_url VARCHAR(512),
                status VARCHAR(32),
                points_deducted INT DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        ''')
        print("   ✓ 创建表: survey_records")
        
        conn.commit()
        
        # 创建默认管理员
        print("\n👤 正在创建默认管理员...")
        default_admin_password = hash_password('xzx123456')
        
        try:
            cur.execute(
                'INSERT INTO admins (username, password) VALUES (%s, %s)',
                ('Bear', default_admin_password)
            )
            conn.commit()
            print("   ✓ 默认管理员已创建")
            print("   📌 用户名: Bear")
            print("   📌 密码: xzx123456")
        except psycopg2.IntegrityError:
            conn.rollback()
            print("   ⚠️  管理员账号已存在，跳过创建")
        
        # 创建索引
        print("\n🔍 正在创建索引...")
        cur.execute('CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)')
        cur.execute('CREATE INDEX IF NOT EXISTS idx_admins_username ON admins(username)')
        cur.execute('CREATE INDEX IF NOT EXISTS idx_survey_records_user_id ON survey_records(user_id)')
        cur.execute('CREATE INDEX IF NOT EXISTS idx_points_log_user_id ON points_log(user_id)')
        conn.commit()
        print("   ✓ 索引创建完成")
        
        cur.close()
        conn.close()
        
        print("\n✅ PostgreSQL 数据库初始化成功！")
        print("\n📊 数据库信息:")
        print(f"   数据库URL: {DATABASE_URL[:50]}...")
        print(f"   表数量: 5")
        print(f"   默认管理员: Bear / xzx123456")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 初始化失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = init_postgres_db()
    sys.exit(0 if success else 1)
