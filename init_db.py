#!/usr/bin/env python3
"""
数据库初始化脚本
执行 create_database.sql 中的 SQL 语句来初始化数据库
"""

import os
import sys
import pymysql
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 数据库配置
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = int(os.getenv('DB_PORT', 3306))
DB_USER = os.getenv('DB_USER', 'root')
DB_PASSWORD = os.getenv('DB_PASSWORD', '')
DB_NAME = 'wjx_survey'

def read_sql_file(filepath):
    """读取 SQL 文件"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        return content
    except FileNotFoundError:
        print(f"❌ 错误: 找不到文件 {filepath}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 读取文件出错: {e}")
        sys.exit(1)

def split_sql_statements(sql_content):
    """将 SQL 文件内容分割成单个语句"""
    statements = []
    current_statement = []
    
    for line in sql_content.split('\n'):
        # 跳过注释和空行
        line = line.strip()
        if not line or line.startswith('--'):
            continue
        
        current_statement.append(line)
        
        # 检查是否是语句结束（以分号结尾）
        if line.endswith(';'):
            statement = ' '.join(current_statement)
            if statement:
                statements.append(statement)
            current_statement = []
    
    return statements

def execute_sql_file(sql_file):
    """执行 SQL 文件"""
    print(f"📖 读取 SQL 文件: {sql_file}")
    sql_content = read_sql_file(sql_file)
    
    # 分割 SQL 语句
    statements = split_sql_statements(sql_content)
    print(f"📝 找到 {len(statements)} 条 SQL 语句")
    
    # 连接数据库
    try:
        print(f"🔗 连接数据库: {DB_HOST}:{DB_PORT}")
        
        # 先连接到 MySQL 服务器（不指定数据库）
        conn = pymysql.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            charset='utf8mb4'
        )
        cursor = conn.cursor()
        
        # 执行每条 SQL 语句
        for i, statement in enumerate(statements, 1):
            try:
                print(f"  [{i}/{len(statements)}] 执行: {statement[:60]}...")
                cursor.execute(statement)
                conn.commit()
            except Exception as e:
                print(f"  ❌ 执行失败: {e}")
                conn.rollback()
                # 继续执行下一条语句
                continue
        
        cursor.close()
        conn.close()
        
        print("✅ 数据库初始化完成！")
        return True
        
    except pymysql.Error as e:
        print(f"❌ 数据库连接错误: {e}")
        print("\n💡 请检查:")
        print(f"   - MySQL 服务是否运行")
        print(f"   - 数据库地址: {DB_HOST}:{DB_PORT}")
        print(f"   - 用户名: {DB_USER}")
        print(f"   - 密码是否正确")
        return False
    except Exception as e:
        print(f"❌ 未知错误: {e}")
        return False

def main():
    """主函数"""
    print("=" * 60)
    print("🚀 问卷星数据库初始化工具")
    print("=" * 60)
    
    # 获取 SQL 文件路径
    script_dir = os.path.dirname(os.path.abspath(__file__))
    sql_file = os.path.join(script_dir, 'create_database.sql')
    
    # 检查文件是否存在
    if not os.path.exists(sql_file):
        print(f"❌ 错误: 找不到 SQL 文件 {sql_file}")
        sys.exit(1)
    
    print(f"\n📂 SQL 文件路径: {sql_file}")
    print(f"🗄️  数据库配置:")
    print(f"   - 主机: {DB_HOST}")
    print(f"   - 端口: {DB_PORT}")
    print(f"   - 用户: {DB_USER}")
    print(f"   - 数据库: {DB_NAME}")
    
    # 确认执行
    print("\n⚠️  即将初始化数据库，这将创建所有必要的表和数据。")
    response = input("是否继续? (yes/no): ").strip().lower()
    
    if response not in ['yes', 'y']:
        print("❌ 已取消")
        sys.exit(0)
    
    print("\n" + "=" * 60)
    print("开始初始化...")
    print("=" * 60 + "\n")
    
    # 执行 SQL 文件
    success = execute_sql_file(sql_file)
    
    print("\n" + "=" * 60)
    if success:
        print("✅ 初始化成功！")
        print("\n📋 默认管理员账号:")
        print("   - 用户名: Bear")
        print("   - 密码: xzx123456")
        print("\n💡 请妥善保管管理员账号密码！")
    else:
        print("❌ 初始化失败，请检查错误信息")
        sys.exit(1)
    print("=" * 60)

if __name__ == '__main__':
    main()
