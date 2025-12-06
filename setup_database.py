#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库初始化脚本
用于创建数据库表和默认数据
"""

import pymysql
import hashlib
import sys

# MySQL配置
MYSQL_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',
    'password': '123456',
    'charset': 'utf8mb4',
    'autocommit': True
}

def hash_password(pw):
    """SHA256加密密码"""
    return hashlib.sha256(pw.encode('utf-8')).hexdigest()

def create_database():
    """创建数据库"""
    try:
        conn = pymysql.connect(**MYSQL_CONFIG)
        with conn.cursor() as cur:
            # 创建数据库
            cur.execute('CREATE DATABASE IF NOT EXISTS `wjx_survey` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci')
            print("✓ 数据库创建成功")
        conn.close()
    except Exception as e:
        print(f"✗ 创建数据库失败: {e}")
        return False
    return True

def create_tables():
    """创建表"""
    config = MYSQL_CONFIG.copy()
    config['database'] = 'wjx_survey'
    
    try:
        conn = pymysql.connect(**config)
        with conn.cursor() as cur:
            # 创建用户表
            cur.execute('''
                CREATE TABLE IF NOT EXISTS `users` (
                    `id` int NOT NULL AUTO_INCREMENT,
                    `email` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL UNIQUE,
                    `username` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
                    `password` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
                    `phone` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci,
                    `points` int NOT NULL DEFAULT 0,
                    `last_signin` date,
                    `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (`id`),
                    UNIQUE KEY `email` (`email`)
                ) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            ''')
            print("✓ users 表创建成功")
            
            # 创建管理员表
            cur.execute('''
                CREATE TABLE IF NOT EXISTS `admins` (
                    `id` int NOT NULL AUTO_INCREMENT,
                    `username` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL UNIQUE,
                    `password` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
                    `phone` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci,
                    `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (`id`),
                    UNIQUE KEY `username` (`username`)
                ) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            ''')
            print("✓ admins 表创建成功")
            
            # 创建问卷填写记录表
            cur.execute('''
                CREATE TABLE IF NOT EXISTS `survey_records` (
                    `id` int NOT NULL AUTO_INCREMENT,
                    `user_id` int NOT NULL,
                    `survey_url` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
                    `status` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT 'success',
                    `points_deducted` int DEFAULT 1,
                    `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (`id`),
                    KEY `user_id` (`user_id`),
                    CONSTRAINT `survey_records_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
                ) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            ''')
            print("✓ survey_records 表创建成功")
            
            # 创建积分日志表
            cur.execute('''
                CREATE TABLE IF NOT EXISTS `points_log` (
                    `id` int NOT NULL AUTO_INCREMENT,
                    `user_id` int NOT NULL,
                    `points_change` int NOT NULL,
                    `reason` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci,
                    `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (`id`),
                    KEY `user_id` (`user_id`),
                    CONSTRAINT `points_log_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
                ) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            ''')
            print("✓ points_log 表创建成功")
            
            # 创建索引
            cur.execute('CREATE INDEX IF NOT EXISTS `idx_users_email` ON `users` (`email`)')
            cur.execute('CREATE INDEX IF NOT EXISTS `idx_users_created_at` ON `users` (`created_at`)')
            cur.execute('CREATE INDEX IF NOT EXISTS `idx_survey_records_user_id` ON `survey_records` (`user_id`)')
            cur.execute('CREATE INDEX IF NOT EXISTS `idx_survey_records_created_at` ON `survey_records` (`created_at`)')
            cur.execute('CREATE INDEX IF NOT EXISTS `idx_points_log_user_id` ON `points_log` (`user_id`)')
            cur.execute('CREATE INDEX IF NOT EXISTS `idx_points_log_created_at` ON `points_log` (`created_at`)')
            print("✓ 索引创建成功")
        
        conn.close()
    except Exception as e:
        print(f"✗ 创建表失败: {e}")
        return False
    return True

def insert_default_admin():
    """插入默认管理员"""
    config = MYSQL_CONFIG.copy()
    config['database'] = 'wjx_survey'
    
    try:
        conn = pymysql.connect(**config)
        with conn.cursor() as cur:
            # 检查是否已存在
            cur.execute('SELECT * FROM admins WHERE username=%s', ('Bear',))
            if cur.fetchone():
                print("✓ 默认管理员已存在，跳过插入")
                conn.close()
                return True
            
            # 插入默认管理员
            # 密码: xzx123456
            password_hash = hash_password('xzx123456')
            cur.execute(
                'INSERT INTO admins (username, password) VALUES (%s, %s)',
                ('Bear', password_hash)
            )
            print("✓ 默认管理员创建成功")
            print("  用户名: Bear")
            print("  密码: xzx123456")
        
        conn.close()
    except Exception as e:
        print(f"✗ 插入默认管理员失败: {e}")
        return False
    return True

def main():
    """主函数"""
    print("=" * 50)
    print("问卷星自动填答系统 - 数据库初始化")
    print("=" * 50)
    print()
    
    # 创建数据库
    if not create_database():
        sys.exit(1)
    
    # 创建表
    if not create_tables():
        sys.exit(1)
    
    # 插入默认管理员
    if not insert_default_admin():
        sys.exit(1)
    
    print()
    print("=" * 50)
    print("✓ 数据库初始化完成！")
    print("=" * 50)
    print()
    print("默认管理员账户:")
    print("  用户名: Bear")
    print("  密码: xzx123456")
    print()
    print("请使用管理员账户登录后台进行管理。")
    print()

if __name__ == '__main__':
    main()
