import re
import hashlib
import datetime
import os
from flask import Blueprint, request, session, jsonify, g
from config import DB_TYPE, MYSQL_CONFIG

try:
    import pymysql
except ImportError:
    pymysql = None

user_bp = Blueprint('user', __name__)

# 数据库配置 - MySQL
DB_CONFIG = MYSQL_CONFIG

EMAIL_REGEX = r'^[A-Za-z0-9._%+-]+@(qq\.com|163\.com|126\.com|gmail\.com|outlook\.com|hotmail\.com|sina\.com|foxmail\.com)'

# --- 数据库连接 ---
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        if pymysql is None:
            raise ImportError("pymysql is not installed. Install it with: pip install pymysql")
        db = g._database = pymysql.connect(**DB_CONFIG)
    return db

@user_bp.teardown_app_request
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

# --- 工具函数 ---
def hash_password(pw):
    return hashlib.sha256(pw.encode('utf-8')).hexdigest()

def valid_email(email):
    return re.match(EMAIL_REGEX, email)

# --- 初始化数据库 ---
def init_db():
    if pymysql is None:
        raise ImportError("pymysql is not installed. Install it with: pip install pymysql")
    conn = pymysql.connect(**DB_CONFIG)
    
    c = conn.cursor()
    
    # 创建用户表
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INT AUTO_INCREMENT PRIMARY KEY,
        email VARCHAR(128) UNIQUE NOT NULL,
        username VARCHAR(64) NOT NULL,
        password VARCHAR(128) NOT NULL,
        points INT DEFAULT 0,
        last_signin DATE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # 创建管理员表
    c.execute('''CREATE TABLE IF NOT EXISTS admins (
        id INT AUTO_INCREMENT PRIMARY KEY,
        username VARCHAR(64) UNIQUE NOT NULL,
        password VARCHAR(128) NOT NULL,
        phone VARCHAR(20),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # 创建充值申请表
    c.execute('''CREATE TABLE IF NOT EXISTS recharge_requests (
        id INT AUTO_INCREMENT PRIMARY KEY,
        user_id INT NOT NULL,
        amount INT NOT NULL,
        remark VARCHAR(255) DEFAULT '',
        status ENUM('pending', 'approved', 'rejected') DEFAULT 'pending',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        processed_at TIMESTAMP NULL,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )''')
    
    # 创建积分日志表（如果不存在）
    c.execute('''CREATE TABLE IF NOT EXISTS points_log (
        id INT AUTO_INCREMENT PRIMARY KEY,
        user_id INT NOT NULL,
        points_change INT NOT NULL,
        reason VARCHAR(255),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )''')
    
    # 创建问卷记录表（如果不存在）
    c.execute('''CREATE TABLE IF NOT EXISTS survey_records (
        id INT AUTO_INCREMENT PRIMARY KEY,
        user_id INT NOT NULL,
        survey_url VARCHAR(512),
        status VARCHAR(32),
        points_deducted INT DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )''')
    
    # 创建默认管理员（如果不存在）
    c.execute('SELECT * FROM admins WHERE username=%s', ('Bear',))
    if not c.fetchone():
        default_password = hash_password('xzx123456')
        c.execute('INSERT INTO admins (username, password) VALUES (%s, %s)', ('Bear', default_password))
        print("✓ 默认管理员账号已创建: 用户名=Bear, 密码=xzx123456")
    
    conn.commit()
    conn.close()

# --- 注册 ---
@user_bp.route('/register', methods=['POST'])
def register():
    data = request.json
    email = data.get('email', '').strip()
    username = data.get('username', '').strip()
    password = data.get('password', '')
    confirm = data.get('confirm', '')

    if not (email and username and password and confirm):
        return jsonify({'status': 'error', 'message': '所有字段均为必填'}), 400
    if not valid_email(email):
        return jsonify({'status': 'error', 'message': '仅支持常见邮箱注册'}), 400
    if password != confirm:
        return jsonify({'status': 'error', 'message': '两次密码不一致'}), 400
    if len(password) < 6:
        return jsonify({'status': 'error', 'message': '密码至少6位'}), 400

    db = get_db()
    try:
        with db.cursor() as cur:
            cur.execute('INSERT INTO users (email, username, password) VALUES (%s, %s, %s)',
                        (email, username, hash_password(password)))
        db.commit()
        return jsonify({'status': 'success', 'message': '注册成功'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': '该邮箱已被注册'}), 400

# --- 登录 ---
@user_bp.route('/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email', '').strip()
    password = data.get('password', '')
    
    if not (email and password):
        return jsonify({'status': 'error', 'message': '邮箱/用户名和密码必填'}), 400
    
    # 清除旧的session数据
    session.clear()
    
    db = get_db()
    
    # 先检查是否是管理员账号（英文用户名）
    with db.cursor() as cur:
        cur.execute('SELECT * FROM admins WHERE username=%s', (email,))
        admin = cur.fetchone()
        if admin:
            # 是管理员账号
            if admin[2] != hash_password(password):
                return jsonify({'status': 'error', 'message': '用户名或密码错误'}), 400
            session['admin_id'] = admin[0]
            session['role'] = 'admin'
            return jsonify({'status': 'success', 'message': '登录成功', 'username': admin[1], 'role': 'admin'})
    
    # 再检查是否是普通用户（邮箱）
    with db.cursor() as cur:
        cur.execute('SELECT * FROM users WHERE email=%s', (email,))
        user = cur.fetchone()
        if user:
            # 是普通用户账号
            if user[3] != hash_password(password):
                return jsonify({'status': 'error', 'message': '邮箱或密码错误'}), 400
            session['user_id'] = user[0]
            session['role'] = 'user'
            return jsonify({'status': 'success', 'message': '登录成功', 'username': user[2], 'role': 'user', 'points': user[4]})
    
    # 都不匹配
    return jsonify({'status': 'error', 'message': '用户名或密码错误'}), 400

# --- 登出 ---
@user_bp.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'status': 'success', 'message': '已登出', 'redirect': '/login.html'})

# --- 用户信息 ---
@user_bp.route('/profile', methods=['GET'])
def profile():
    admin_id = session.get('admin_id')
    user_id = session.get('user_id')
    
    if admin_id:
        # 管理员信息
        db = get_db()
        with db.cursor() as cur:
            cur.execute('SELECT id, username, phone, created_at FROM admins WHERE id=%s', (admin_id,))
            admin = cur.fetchone()
            if not admin:
                return jsonify({'status': 'error', 'message': '管理员不存在'}), 404
            keys = ['id', 'username', 'phone', 'created_at']
            return jsonify({'status': 'success', 'data': dict(zip(keys, admin)), 'role': 'admin'})
    elif user_id:
        # 普通用户信息
        db = get_db()
        with db.cursor() as cur:
            cur.execute('SELECT id, email, username, points, last_signin, created_at FROM users WHERE id=%s', (user_id,))
            user = cur.fetchone()
            if not user:
                return jsonify({'status': 'error', 'message': '用户不存在'}), 404
            keys = ['id', 'email', 'username', 'points', 'last_signin', 'created_at']
            return jsonify({'status': 'success', 'data': dict(zip(keys, user)), 'role': 'user'})
    else:
        return jsonify({'status': 'error', 'message': '未登录'}), 401

# --- 签到（每天仅可签到一次，数据库层面保证原子性） ---
@user_bp.route('/signin', methods=['POST'])
def signin():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'status': 'error', 'message': '未登录'}), 401

    today = datetime.date.today()
    db = get_db()
    with db.cursor() as cur:
        # 先查询当前积分
        cur.execute('SELECT points, last_signin FROM users WHERE id=%s', (user_id,))
        row = cur.fetchone()
        current_points = row[0] if row else 0

        # 通过条件更新保证"每天只能签到一次"
        cur.execute(
            '''
            UPDATE users
            SET points = points + 5, last_signin = %s
            WHERE id = %s AND (last_signin IS NULL OR last_signin < %s)
            ''',
            (today, user_id, today)
        )
        if cur.rowcount == 0:
            # 没有任何行被更新，说明今天已经签过到
            return jsonify({'status': 'error', 'message': '今日已签到'}), 400

        # 重新查询最新积分
        cur.execute('SELECT points FROM users WHERE id=%s', (user_id,))
        new_points = cur.fetchone()[0]

    db.commit()
    return jsonify({'status': 'success', 'message': '签到成功，积分+5', 'points': new_points})

# --- 积分充值申请 ---
# 固定充值金额选项
RECHARGE_OPTIONS = [50, 100, 200, 1000]
PAYMENT_METHODS = ['alipay', 'wechat']

@user_bp.route('/recharge', methods=['POST'])
def recharge():
    """
    积分充值申请接口：
    - 普通用户：提交充值申请，等待管理员审核
    - 固定金额: 50, 100, 200, 1000
    - 支付方式: alipay, wechat
    """
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'status': 'error', 'message': '未登录'}), 401

    data = request.json or {}
    amount = data.get('amount')
    payment_method = data.get('payment_method', 'alipay')

    # 校验金额
    try:
        amount = int(amount)
    except (TypeError, ValueError):
        return jsonify({'status': 'error', 'message': '请选择充值金额'}), 400

    if amount not in RECHARGE_OPTIONS:
        return jsonify({'status': 'error', 'message': f'请选择有效的充值金额: {RECHARGE_OPTIONS}'}), 400

    # 校验支付方式
    if payment_method not in PAYMENT_METHODS:
        return jsonify({'status': 'error', 'message': '请选择有效的支付方式'}), 400

    db = get_db()
    with db.cursor() as cur:
        # 获取用户信息
        cur.execute('SELECT email, username FROM users WHERE id=%s', (user_id,))
        user = cur.fetchone()
        if not user:
            return jsonify({'status': 'error', 'message': '用户不存在'}), 404
        
        # 创建充值申请记录
        cur.execute('''
            INSERT INTO recharge_requests (user_id, amount, payment_method, status)
            VALUES (%s, %s, %s, 'pending')
        ''', (user_id, amount, payment_method))
    
    db.commit()
    
    payment_name = '支付宝' if payment_method == 'alipay' else '微信'
    return jsonify({
        'status': 'success',
        'message': f'充值申请已提交！金额: {amount}积分，支付方式: {payment_name}，请等待管理员审核'
    })

# --- 获取充值申请列表（管理员） ---
@user_bp.route('/recharge_requests', methods=['GET'])
def get_recharge_requests():
    """获取所有充值申请（管理员用）"""
    if not session.get('admin_id'):
        return jsonify({'status': 'error', 'message': '无权限'}), 403
    
    status_filter = request.args.get('status', 'pending')
    
    db = get_db()
    with db.cursor() as cur:
        if status_filter == 'all':
            cur.execute('''
                SELECT r.id, r.user_id, u.email, u.username, r.amount, r.payment_method, r.status, r.created_at, r.processed_at
                FROM recharge_requests r
                JOIN users u ON r.user_id = u.id
                ORDER BY r.created_at DESC
                LIMIT 100
            ''')
        else:
            cur.execute('''
                SELECT r.id, r.user_id, u.email, u.username, r.amount, r.payment_method, r.status, r.created_at, r.processed_at
                FROM recharge_requests r
                JOIN users u ON r.user_id = u.id
                WHERE r.status = %s
                ORDER BY r.created_at DESC
                LIMIT 100
            ''', (status_filter,))
        
        requests_list = cur.fetchall()
        keys = ['id', 'user_id', 'email', 'username', 'amount', 'payment_method', 'status', 'created_at', 'processed_at']
        return jsonify({
            'status': 'success',
            'data': [dict(zip(keys, r)) for r in requests_list]
        })

# --- 处理充值申请（管理员） ---
@user_bp.route('/recharge_requests/<int:request_id>', methods=['POST'])
def process_recharge_request(request_id):
    """处理充值申请（管理员审核）"""
    if not session.get('admin_id'):
        return jsonify({'status': 'error', 'message': '无权限'}), 403
    
    data = request.json or {}
    action = data.get('action')  # 'approve' 或 'reject'
    
    if action not in ['approve', 'reject']:
        return jsonify({'status': 'error', 'message': '无效操作'}), 400
    
    db = get_db()
    with db.cursor() as cur:
        # 获取申请信息
        cur.execute('SELECT user_id, amount, status FROM recharge_requests WHERE id=%s', (request_id,))
        req = cur.fetchone()
        
        if not req:
            return jsonify({'status': 'error', 'message': '申请不存在'}), 404
        
        if req[2] != 'pending':
            return jsonify({'status': 'error', 'message': '该申请已处理'}), 400
        
        user_id, amount, _ = req
        
        if action == 'approve':
            # 批准：增加用户积分
            cur.execute('UPDATE users SET points = points + %s WHERE id = %s', (amount, user_id))
            cur.execute('''
                UPDATE recharge_requests 
                SET status = 'approved', processed_at = NOW()
                WHERE id = %s
            ''', (request_id,))
            
            # 记录积分日志
            cur.execute('''
                INSERT INTO points_log (user_id, points_change, reason)
                VALUES (%s, %s, %s)
            ''', (user_id, amount, f'充值申请审核通过 (申请ID: {request_id})'))
            
            message = f'已批准充值申请，用户积分 +{amount}'
        else:
            # 拒绝
            cur.execute('''
                UPDATE recharge_requests 
                SET status = 'rejected', processed_at = NOW()
                WHERE id = %s
            ''', (request_id,))
            message = '已拒绝充值申请'
    
    db.commit()
    return jsonify({'status': 'success', 'message': message})

# --- 获取用户自己的充值申请记录 ---
@user_bp.route('/my_recharge_requests', methods=['GET'])
def get_my_recharge_requests():
    """获取当前用户的充值申请记录"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'status': 'error', 'message': '未登录'}), 401
    
    db = get_db()
    with db.cursor() as cur:
        cur.execute('''
            SELECT id, amount, payment_method, status, created_at, processed_at
            FROM recharge_requests
            WHERE user_id = %s
            ORDER BY created_at DESC
            LIMIT 50
        ''', (user_id,))
        
        requests_list = cur.fetchall()
        keys = ['id', 'amount', 'payment_method', 'status', 'created_at', 'processed_at']
        return jsonify({
            'status': 'success',
            'data': [dict(zip(keys, r)) for r in requests_list]
        })

# --- 管理员接口示例（可扩展） ---
@user_bp.route('/users', methods=['GET'])
def list_users():
    if session.get('role') != 'admin':
        return jsonify({'status': 'error', 'message': '无权限'}), 403
    db = get_db()
    with db.cursor() as cur:
        cur.execute('SELECT id, email, username, points, last_signin, created_at FROM users')
        users = cur.fetchall()
        keys = ['id', 'email', 'username', 'points', 'last_signin', 'created_at']
        return jsonify({'status': 'success', 'data': [dict(zip(keys, u)) for u in users]})

# --- 修改用户名 ---
@user_bp.route('/update_username', methods=['POST'])
def update_username():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'status': 'error', 'message': '未登录'}), 401
    data = request.json
    username = data.get('username', '').strip()
    if not username:
        return jsonify({'status': 'error', 'message': '用户名不能为空'}), 400
    db = get_db()
    with db.cursor() as cur:
        cur.execute('UPDATE users SET username=%s WHERE id=%s', (username, user_id))
    db.commit()
    return jsonify({'status': 'success', 'message': '用户名修改成功'})

# --- 修改密码 ---
@user_bp.route('/update_password', methods=['POST'])
def update_password():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'status': 'error', 'message': '未登录'}), 401
    data = request.json
    old_password = data.get('old_password', '')
    new_password = data.get('new_password', '')
    confirm = data.get('confirm', '')
    if not (old_password and new_password and confirm):
        return jsonify({'status': 'error', 'message': '所有字段均为必填'}), 400
    if new_password != confirm:
        return jsonify({'status': 'error', 'message': '两次新密码不一致'}), 400
    if len(new_password) < 6:
        return jsonify({'status': 'error', 'message': '新密码至少6位'}), 400
    db = get_db()
    with db.cursor() as cur:
        cur.execute('SELECT password FROM users WHERE id=%s', (user_id,))
        user = cur.fetchone()
        if not user or user[0] != hash_password(old_password):
            return jsonify({'status': 'error', 'message': '原密码错误'}), 400
        cur.execute('UPDATE users SET password=%s WHERE id=%s', (hash_password(new_password), user_id))
    db.commit()
    return jsonify({'status': 'success', 'message': '密码修改成功'})

# --- 初始化数据库脚本入口 ---
if __name__ == '__main__':
    init_db()
    print('用户表已初始化')
