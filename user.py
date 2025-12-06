import re
import hashlib
import datetime
import os
from flask import Blueprint, request, session, jsonify, g
from config import DB_TYPE, MYSQL_CONFIG, POSTGRESQL_CONFIG

try:
    import psycopg2
except ImportError:
    psycopg2 = None

try:
    import pymysql
except ImportError:
    pymysql = None

user_bp = Blueprint('user', __name__)

# 根据环境选择数据库配置
# 云端环境：必须使用 PostgreSQL
if os.getenv('FLASK_ENV') == 'production' or os.getenv('DATABASE_URL'):
    DB_CONFIG = POSTGRESQL_CONFIG
    DB_TYPE = 'postgresql'
elif DB_TYPE == 'postgresql':
    DB_CONFIG = POSTGRESQL_CONFIG
else:
    DB_CONFIG = MYSQL_CONFIG

EMAIL_REGEX = r'^[A-Za-z0-9._%+-]+@(qq\.com|163\.com|126\.com|gmail\.com|outlook\.com|hotmail\.com|sina\.com|foxmail\.com)'

# --- 数据库连接 ---
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        # 检查是否在云端环境
        is_production = os.getenv('FLASK_ENV') == 'production' or os.getenv('DATABASE_URL')
        
        if is_production or DB_TYPE == 'postgresql':
            # 云端或 PostgreSQL 环境
            if psycopg2 is None:
                raise ImportError("psycopg2 is not installed. Install it with: pip install psycopg2-binary")
            try:
                db = g._database = psycopg2.connect(
                    host=DB_CONFIG['host'],
                    port=DB_CONFIG['port'],
                    user=DB_CONFIG['user'],
                    password=DB_CONFIG['password'],
                    database=DB_CONFIG['database']
                )
            except Exception as e:
                print(f"[ERROR] PostgreSQL 连接失败: {e}")
                raise
        else:
            # 本地 MySQL 环境
            if pymysql is None:
                raise ImportError("pymysql is not installed. Install it with: pip install pymysql")
            try:
                db = g._database = pymysql.connect(**DB_CONFIG)
            except Exception as e:
                print(f"[ERROR] MySQL 连接失败: {e}")
                raise
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
    if DB_TYPE == 'postgresql':
        if psycopg2 is None:
            raise ImportError("psycopg2 is not installed. Install it with: pip install psycopg2-binary")
        conn = psycopg2.connect(
            host=DB_CONFIG['host'],
            port=DB_CONFIG['port'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            database=DB_CONFIG['database']
        )
    else:
        if pymysql is None:
            raise ImportError("pymysql is not installed. Install it with: pip install pymysql")
        conn = pymysql.connect(**DB_CONFIG)
    
    c = conn.cursor()
    
    # 创建用户表
    if DB_TYPE == 'postgresql':
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
    else:
        c.execute('''CREATE TABLE IF NOT EXISTS users (
            id INT PRIMARY KEY AUTO_INCREMENT,
            email VARCHAR(128) UNIQUE NOT NULL,
            username VARCHAR(64) NOT NULL,
            password VARCHAR(128) NOT NULL,
            points INT DEFAULT 0,
            last_signin DATE,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )''')
        
        # 创建管理员表
        c.execute('''CREATE TABLE IF NOT EXISTS admins (
            id INT PRIMARY KEY AUTO_INCREMENT,
            username VARCHAR(64) UNIQUE NOT NULL,
            password VARCHAR(128) NOT NULL,
            phone VARCHAR(20),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )''')
    
    # 创建默认管理员（如果不存在）
    c.execute('SELECT * FROM admins WHERE username=%s', ('Bear',))
    if not c.fetchone():
        default_password = hash_password('xzx123456')
        c.execute('INSERT INTO admins (username, password) VALUES (%s, %s)', ('Bear', default_password))
    
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
    login_type = data.get('type', 'user')  # 'user' 或 'admin'
    
    if not (email and password):
        return jsonify({'status': 'error', 'message': '邮箱/用户名和密码必填'}), 400
    
    db = get_db()
    
    if login_type == 'admin':
        # 管理员登录
        with db.cursor() as cur:
            cur.execute('SELECT * FROM admins WHERE username=%s', (email,))
            admin = cur.fetchone()
            if not admin or admin[2] != hash_password(password):
                return jsonify({'status': 'error', 'message': '用户名或密码错误'}), 400
            session['admin_id'] = admin[0]
            session['role'] = 'admin'
            return jsonify({'status': 'success', 'message': '登录成功', 'username': admin[1], 'role': 'admin'})
    else:
        # 普通用户登录
        with db.cursor() as cur:
            cur.execute('SELECT * FROM users WHERE email=%s', (email,))
            user = cur.fetchone()
            if not user or user[3] != hash_password(password):
                return jsonify({'status': 'error', 'message': '邮箱或密码错误'}), 400
            session['user_id'] = user[0]
            session['role'] = 'user'
            return jsonify({'status': 'success', 'message': '登录成功', 'username': user[2], 'role': 'user', 'points': user[4]})

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

# --- 积分充值 ---
@user_bp.route('/recharge', methods=['POST'])
def recharge():
    """
    积分充值接口：
    - 普通用户：给自己充值
    - 管理员：可以在 body 中传入 user_id 给指定用户充值
    """
    user_id = session.get('user_id')
    role = session.get('role')
    if not user_id:
        return jsonify({'status': 'error', 'message': '未登录'}), 401

    data = request.json or {}
    amount = data.get('amount')
    target_user_id = data.get('user_id') if role == 'admin' else user_id

    # 基本校验
    try:
        amount = int(amount)
    except (TypeError, ValueError):
        return jsonify({'status': 'error', 'message': '充值积分必须是整数'}), 400

    if amount <= 0:
        return jsonify({'status': 'error', 'message': '充值积分必须大于0'}), 400
    if amount > 100000:
        return jsonify({'status': 'error', 'message': '单次充值积分过大，请联系管理员'}), 400

    db = get_db()
    with db.cursor() as cur:
        cur.execute('UPDATE users SET points = points + %s WHERE id = %s', (amount, target_user_id))
        if cur.rowcount == 0:
            return jsonify({'status': 'error', 'message': '用户不存在，充值失败'}), 404

        cur.execute('SELECT points FROM users WHERE id = %s', (target_user_id,))
        row = cur.fetchone()
        new_points = row[0] if row else 0

    db.commit()
    return jsonify({
        'status': 'success',
        'message': f'充值成功，本次增加 {amount} 积分',
        'points': new_points
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
