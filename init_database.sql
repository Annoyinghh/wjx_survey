-- 问卷星自动填答系统数据库初始化脚本
-- 在Navicat中执行此脚本以创建数据库和表

-- 创建数据库
CREATE DATABASE IF NOT EXISTS `wjx_survey` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE `wjx_survey`;

-- 创建用户表
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
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 创建管理员表
CREATE TABLE IF NOT EXISTS `admins` (
  `id` int NOT NULL AUTO_INCREMENT,
  `username` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL UNIQUE,
  `password` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `phone` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 创建问卷填写记录表
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
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 创建积分日志表
CREATE TABLE IF NOT EXISTS `points_log` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `points_change` int NOT NULL,
  `reason` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `user_id` (`user_id`),
  CONSTRAINT `points_log_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 插入默认管理员账户
-- 用户名: Bear
-- 密码: xzx123456 (SHA256加密后)
INSERT INTO `admins` (`username`, `password`, `phone`) VALUES 
('Bear', 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855', NULL);

-- 创建索引以提高查询性能
CREATE INDEX `idx_users_email` ON `users` (`email`);
CREATE INDEX `idx_users_created_at` ON `users` (`created_at`);
CREATE INDEX `idx_survey_records_user_id` ON `survey_records` (`user_id`);
CREATE INDEX `idx_survey_records_created_at` ON `survey_records` (`created_at`);
CREATE INDEX `idx_points_log_user_id` ON `points_log` (`user_id`);
CREATE INDEX `idx_points_log_created_at` ON `points_log` (`created_at`);

-- 创建视图：用户积分统计
CREATE OR REPLACE VIEW `user_points_summary` AS
SELECT 
  u.id,
  u.username,
  u.email,
  u.points,
  COUNT(sr.id) as survey_count,
  SUM(sr.points_deducted) as total_points_deducted,
  u.created_at
FROM users u
LEFT JOIN survey_records sr ON u.id = sr.user_id
GROUP BY u.id, u.username, u.email, u.points, u.created_at;

-- 创建视图：管理员统计
CREATE OR REPLACE VIEW `admin_statistics` AS
SELECT 
  COUNT(DISTINCT u.id) as total_users,
  COUNT(DISTINCT a.id) as total_admins,
  SUM(u.points) as total_points,
  AVG(u.points) as avg_points,
  COUNT(DISTINCT sr.id) as total_surveys,
  NOW() as last_updated
FROM users u
CROSS JOIN admins a
LEFT JOIN survey_records sr ON u.id = sr.user_id;

-- 注释：
-- 1. users 表：存储普通用户信息
-- 2. admins 表：存储管理员信息
-- 3. survey_records 表：记录每次问卷填写
-- 4. points_log 表：记录积分变化日志
-- 5. user_points_summary 视图：用户积分统计
-- 6. admin_statistics 视图：系统统计信息
