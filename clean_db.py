#!/usr/bin/env python
"""
清理数据库脚本 - 删除所有表
用法：python clean_db.py
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()

print("=" * 70)
print("清理数据库 - 删除所有表")
print("=" * 70)

try:
    import psycopg2
    
    # 使用外部数据库 URL
    db_url = "postgresql://wjx_survey_db_ld9r_user:awy3dVvk7u77Y0WG25rbbc5cqD9NeYyS@dpg-d4pv20e3jp1c73985c6g-a.singapore-postgres.render.com/wjx_survey_db_ld9r"
    
    print("\n连接到数据库...")
    conn = psycopg2.connect(db_url)
    cur = conn.cursor()
    
    print("✓ 连接成功！")
    
    # 删除所有表
    tables = ['survey_records', 'points_log', 'admins', 'users']
    
    print("\n删除表...")
    for table in tables:
        try:
            cur.execute(f"DROP TABLE IF EXISTS {table} CASCADE")
            print(f"  ✓ 删除表: {table}")
        except Exception as e:
            print(f"  ✗ 删除表 {table} 失败: {e}")
    
    conn.commit()
    conn.close()
    
    print("\n✓ 数据库清理完成！")
    print("\n现在可以运行 setup_cloud.py 来重新初始化数据库")
    
except Exception as e:
    print(f"✗ 清理失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("=" * 70)