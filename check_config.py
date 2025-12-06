#!/usr/bin/env python
"""
配置检查脚本 - 验证数据库连接和环境配置
"""

import os
import sys
from config import DB_TYPE, MYSQL_CONFIG, POSTGRESQL_CONFIG, ENV

def check_mysql():
    """检查 MySQL 连接"""
    try:
        import pymysql
        conn = pymysql.connect(**MYSQL_CONFIG)
        conn.close()
        print("✅ MySQL 连接成功")
        return True
    except Exception as e:
        print(f"❌ MySQL 连接失败: {e}")
        return False

def check_postgresql():
    """检查 PostgreSQL 连接"""
    try:
        import psycopg2
        conn = psycopg2.connect(
            host=POSTGRESQL_CONFIG['host'],
            port=POSTGRESQL_CONFIG['port'],
            user=POSTGRESQL_CONFIG['user'],
            password=POSTGRESQL_CONFIG['password'],
            database=POSTGRESQL_CONFIG['database']
        )
        conn.close()
        print("✅ PostgreSQL 连接成功")
        return True
    except Exception as e:
        print(f"❌ PostgreSQL 连接失败: {e}")
        return False

def main():
    print("=" * 50)
    print("WJX Survey 配置检查")
    print("=" * 50)
    
    print(f"\n📋 环境信息：")
    print(f"  运行环境: {ENV}")
    print(f"  数据库类型: {DB_TYPE}")
    
    if DB_TYPE == 'mysql':
        print(f"\n🔍 MySQL 配置：")
        print(f"  主机: {MYSQL_CONFIG['host']}")
        print(f"  端口: {MYSQL_CONFIG['port']}")
        print(f"  用户: {MYSQL_CONFIG['user']}")
        print(f"  数据库: {MYSQL_CONFIG['database']}")
        print(f"\n测试连接...")
        if check_mysql():
            print("\n✅ 所有检查通过！")
            return 0
        else:
            print("\n❌ 请检查数据库配置")
            return 1
    
    elif DB_TYPE == 'postgresql':
        print(f"\n🔍 PostgreSQL 配置：")
        print(f"  主机: {POSTGRESQL_CONFIG['host']}")
        print(f"  端口: {POSTGRESQL_CONFIG['port']}")
        print(f"  用户: {POSTGRESQL_CONFIG['user']}")
        print(f"  数据库: {POSTGRESQL_CONFIG['database']}")
        print(f"\n测试连接...")
        if check_postgresql():
            print("\n✅ 所有检查通过！")
            return 0
        else:
            print("\n❌ 请检查数据库配置")
            return 1
    
    else:
        print(f"\n❌ 未知的数据库类型: {DB_TYPE}")
        return 1

if __name__ == '__main__':
    sys.exit(main())
