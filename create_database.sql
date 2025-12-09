-- 问卷调查系统数据库创建脚本
-- 数据库: wjx_survey

-- 创建数据库（如果不存在）
CREATE DATABASE IF NOT EXISTS wjx_survey DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE wjx_survey;

-- 1. 用户表
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '用户ID',
    email VARCHAR(128) UNIQUE NOT NULL COMMENT '邮箱（登录账号）',
    username VARCHAR(64) NOT NULL COMMENT '用户名',
    password VARCHAR(128) NOT NULL COMMENT '密码（SHA256加密）',
    phone VARCHAR(20) COMMENT '手机号',
    role VARCHAR(20) DEFAULT 'user' COMMENT '角色（user/admin）',
    points INT DEFAULT 0 COMMENT '积分余额',
    last_signin DATE COMMENT '最后签到日期',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '注册时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户表';

-- 2. 管理员表
CREATE TABLE IF NOT EXISTS admins (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '管理员ID',
    username VARCHAR(64) UNIQUE NOT NULL COMMENT '管理员用户名',
    password VARCHAR(128) NOT NULL COMMENT '密码（SHA256加密）',
    phone VARCHAR(20) COMMENT '联系电话',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='管理员表';

-- 3. 充值申请表
CREATE TABLE IF NOT EXISTS recharge_requests (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '申请ID',
    user_id INT NOT NULL COMMENT '用户ID',
    amount INT NOT NULL COMMENT '充值金额（积分数）',
    payment_method VARCHAR(20) DEFAULT 'alipay' COMMENT '支付方式（alipay/wechat）',
    remark VARCHAR(255) DEFAULT '' COMMENT '备注',
    status ENUM('pending', 'approved', 'rejected') DEFAULT 'pending' COMMENT '状态：待审核/已批准/已拒绝',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '申请时间',
    processed_at TIMESTAMP NULL COMMENT '处理时间',
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='充值申请表';

-- 4. 积分变动日志表
CREATE TABLE IF NOT EXISTS points_log (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '日志ID',
    user_id INT NOT NULL COMMENT '用户ID',
    points_change INT NOT NULL COMMENT '积分变化（正数为增加，负数为减少）',
    reason VARCHAR(255) COMMENT '变动原因',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '记录时间',
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='积分变动日志表';

-- 5. 问卷填写记录表
CREATE TABLE IF NOT EXISTS survey_records (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '记录ID',
    user_id INT NOT NULL COMMENT '用户ID',
    survey_url VARCHAR(512) COMMENT '问卷URL',
    status VARCHAR(32) COMMENT '填写状态（success/failed/error）',
    points_deducted INT DEFAULT 0 COMMENT '扣除的积分数',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '填写时间',
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='问卷填写记录表';

-- 插入默认管理员账号
-- 用户名: Bear
-- 密码: xzx123456 (SHA256加密后的值)
INSERT INTO admins (username, password) 
VALUES ('Bear', '0a54e673433e578d80643e03b5c0b7c7ea3418cb670e4682fae81685cda185c0')
ON DUPLICATE KEY UPDATE username=username;

-- 创建索引以提高查询性能
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_recharge_user_status ON recharge_requests(user_id, status);
CREATE INDEX idx_points_log_user ON points_log(user_id);
CREATE INDEX idx_survey_records_user ON survey_records(user_id);

-- 显示所有表
SHOW TABLES;
