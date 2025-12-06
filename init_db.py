#!/usr/bin/env python
"""
数据库初始化脚本
用法：python init_db.py
"""

import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

from user import init_db

if __name__ == '__main__':
    print("正在初始化数据库...")
    try:
        init_db()
        print("✓ 数据库初始化成功！")
        print("\n默认管理员账号：")
        print("  用户名: Bear")
        print("  密码: xzx123456")
        print("\n请立即修改管理员密码！")
    except Exception as e:
        print(f"✗ 初始化失败: {e}")
        exit(1)
