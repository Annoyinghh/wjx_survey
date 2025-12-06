from flask import Flask, render_template, request, jsonify, session
from user import user_bp, init_db
from config import DB_TYPE, DB_CONFIG, MYSQL_CONFIG
from survey_filler_http import SurveyFillerHTTP as SurveyFiller
from survey_parser_http import SurveyParserHTTP as SurveyParser
import json
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import re
import os
from dotenv import load_dotenv

load_dotenv()
print("使用 HTTP 模式（云端兼容）")
print(f"数据库类型: {DB_TYPE}")

# 初始化数据库（创建表和默认管理员）
try:
    init_db()
    print("✓ 数据库初始化完成")
except Exception as e:
    print(f"⚠ 数据库初始化出错: {e}")

try:
    import pymysql
except ImportError:
    pymysql = None

try:
    import psycopg2
except ImportError:
    psycopg2 = None

# 全局变量用于跟踪进度
progress_data = {
    'current': 0,
    'total': 0,
    'success_count': 0,
    'failed_count': 0,
    'is_running': False,
    'should_stop': False
}
progress_lock = threading.Lock()

app = Flask(__name__)
app.secret_key = 'wjx_survey_secret_key'
app.register_blueprint(user_bp, url_prefix='/user')

# 数据库配置 - MySQL
DB_CONFIG = MYSQL_CONFIG


def get_db_connection():
    """获取数据库连接"""
    if DB_TYPE == 'postgresql':
        if psycopg2 is None:
            raise ImportError("psycopg2 is not installed. Install it with: pip install psycopg2-binary")
        return psycopg2.connect(DB_CONFIG['database_url'])
    else:  # MySQL
        if pymysql is None:
            raise ImportError("pymysql is not installed. Install it with: pip install pymysql")
        return pymysql.connect(**DB_CONFIG)

def hash_password(pw):
    return hashlib.sha256(pw.encode('utf-8')).hexdigest()

def valid_email(email):
    EMAIL_REGEX = r'^[A-Za-z0-9._%+-]+@(qq\.com|163\.com|126\.com|gmail\.com|outlook\.com|hotmail\.com|sina\.com|foxmail\.com)'
    return re.match(EMAIL_REGEX, email)

@app.route('/')
def index():
    return render_template('login.html')

@app.route('/parse', methods=['POST'])
def parse_survey():
    url = request.form.get('url')
    parser = SurveyParser()
    survey_data = parser.parse_survey(url)
    
    if survey_data:
        return jsonify({
            'status': 'success',
            'data': survey_data
        })
    else:
        return jsonify({
            'status': 'error',
            'message': '解析问卷失败'
        })

@app.route('/submit', methods=['POST'])
def submit():
    try:
        # 检查用户是否登录
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({
                'status': 'error',
                'message': '请先登录'
            }), 401
        
        url = request.form.get('url')
        count = int(request.form.get('count', 1))
        use_ai = request.form.get('useAI') == 'true'
        weights_json = request.form.get('weights', '{}')
        
        print(f"接收到的数据:")
        print(f"用户ID: {user_id}")
        print(f"URL: {url}")
        print(f"填写份数: {count}")
        print(f"使用AI: {use_ai}")
        print(f"权重数据: {weights_json}")
        
        try:
            weights_dict = json.loads(weights_json)
            print(f"解析后的权重数据: {json.dumps(weights_dict, ensure_ascii=False, indent=2)}")
        except json.JSONDecodeError as e:
            print(f"权重数据解析失败: {e}")
            weights_dict = {}
        
        # 重置进度数据
        with progress_lock:
            progress_data['current'] = 0
            progress_data['total'] = count
            progress_data['success_count'] = 0
            progress_data['failed_count'] = 0
            progress_data['is_running'] = True
            progress_data['should_stop'] = False
        
        def record_survey_and_deduct_points(uid, survey_url, status):
            """记录问卷填写并扣积分"""
            try:
                conn = get_db_connection()
                with conn.cursor() as cur:
                    # 只在成功时扣积分
                    if status == 'success':
                        # 扣1个积分
                        cur.execute('UPDATE users SET points = points - 1 WHERE id = %s AND points > 0', (uid,))
                        
                        # 记录问卷填写
                        cur.execute(
                            'INSERT INTO survey_records (user_id, survey_url, status, points_deducted) VALUES (%s, %s, %s, %s)',
                            (uid, survey_url, status, 1)
                        )
                        
                        # 记录积分日志
                        cur.execute(
                            'INSERT INTO points_log (user_id, points_change, reason) VALUES (%s, %s, %s)',
                            (uid, -1, f'填写问卷: {survey_url}')
                        )
                        
                        print(f"用户 {uid} 成功填写问卷，扣除1个积分")
                    else:
                        # 失败或错误时不扣积分，但记录
                        cur.execute(
                            'INSERT INTO survey_records (user_id, survey_url, status, points_deducted) VALUES (%s, %s, %s, %s)',
                            (uid, survey_url, status, 0)
                        )
                        print(f"用户 {uid} 填写问卷失败，不扣积分")
                
                conn.commit()
                conn.close()
            except Exception as e:
                print(f"记录问卷和扣积分时出错: {e}")
        
        # 使用线程池并行填写
        def fill_single_survey(survey_index):
            """填写单份问卷（保证浏览器一定被关闭）"""
            # 检查是否需要停止
            with progress_lock:
                if progress_data['should_stop']:
                    print(f"任务已被中断，跳过第 {survey_index} 份问卷")
                    return False
            
            filler = None
            try:
                print(f"开始填写第 {survey_index} 份问卷")
                filler = SurveyFiller()
                filler.use_ai = use_ai
                filler.weights = weights_dict
                print(f"设置权重: {json.dumps(weights_dict, ensure_ascii=False, indent=2)}")
                
                # 再次检查是否需要停止
                with progress_lock:
                    if progress_data['should_stop']:
                        print(f"任务已被中断，停止填写第 {survey_index} 份问卷")
                        return False
                
                result = filler.fill_survey(url)
                
                # 更新进度和记录（在填写完成后）
                with progress_lock:
                    if result:
                        print(f"第 {survey_index} 份问卷填写成功")
                        progress_data['success_count'] += 1
                        status = 'success'
                    else:
                        print(f"第 {survey_index} 份问卷填写失败")
                        progress_data['failed_count'] += 1
                        status = 'failed'
                    # 更新current为已完成的总数
                    progress_data['current'] = progress_data['success_count'] + progress_data['failed_count']
                
                # 记录问卷填写和扣积分
                record_survey_and_deduct_points(user_id, url, status)
                
                return result
            except Exception as e:
                print(f"第 {survey_index} 份问卷填写异常: {e}")
                with progress_lock:
                    progress_data['failed_count'] += 1
                    progress_data['current'] = progress_data['success_count'] + progress_data['failed_count']
                # 记录失败的问卷
                record_survey_and_deduct_points(user_id, url, 'error')
                return False
            finally:
                # 无论成功、失败还是异常，都确保关闭浏览器
                try:
                    if filler is not None:
                        filler.close()
                except Exception as close_err:
                    print(f"关闭浏览器时出错: {close_err}")
        
        # 在后台线程中执行填写任务
        def run_fill_tasks():
            try:
                if count > 1:
                    max_workers = min(count, 3)
                    print(f"使用 {max_workers} 个并发线程")
                    
                    with ThreadPoolExecutor(max_workers=max_workers) as pool:
                        futures = [pool.submit(fill_single_survey, i+1) for i in range(count)]
                        
                        for future in as_completed(futures):
                            try:
                                future.result()
                            except Exception as e:
                                print(f"任务执行异常: {e}")
                else:
                    fill_single_survey(1)
            finally:
                # 标记任务完成
                with progress_lock:
                    progress_data['is_running'] = False
                    print(f"所有任务完成 - 成功: {progress_data['success_count']}, 失败: {progress_data['failed_count']}")
        
        # 启动后台线程
        thread = threading.Thread(target=run_fill_tasks, daemon=True)
        thread.start()
        
        return jsonify({
            'status': 'success',
            'message': '任务已开始，请查看进度'
        })
    except Exception as e:
        print(f"提交过程中出错: {str(e)}")
        with progress_lock:
            progress_data['is_running'] = False
        return jsonify({
            'status': 'error',
            'message': f'提交失败：{str(e)}'
        })

@app.route('/progress')
def get_progress():
    """获取填写进度"""
    with progress_lock:
        return jsonify({
            'status': 'success',
            'data': progress_data.copy()
        })

@app.route('/stop', methods=['POST'])
def stop_task():
    """停止当前填写任务"""
    with progress_lock:
        if progress_data['is_running']:
            progress_data['should_stop'] = True
            return jsonify({
                'status': 'success',
                'message': '正在停止任务...'
            })
        else:
            return jsonify({
                'status': 'error',
                'message': '当前没有正在运行的任务'
            })

@app.route('/register.html')
def register_page():
    return render_template('register.html')

@app.route('/index.html')
def index_page():
    return render_template('index.html')

@app.route('/login.html')
def login_page():
    return render_template('login.html')

@app.route('/admin.html')
def admin_page():
    return render_template('admin.html')

@app.route('/survey-records', methods=['GET'])
def get_survey_records():
    """获取当前用户的问卷填写记录"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'status': 'error', 'message': '未登录'}), 401
    
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                'SELECT id, survey_url, status, points_deducted, created_at FROM survey_records WHERE user_id = %s ORDER BY created_at DESC LIMIT 100',
                (user_id,)
            )
            records = cur.fetchall()
            keys = ['id', 'survey_url', 'status', 'points_deducted', 'created_at']
            return jsonify({
                'status': 'success',
                'data': [dict(zip(keys, r)) for r in records]
            })
    finally:
        conn.close()

@app.route('/points-log', methods=['GET'])
def get_points_log():
    """获取当前用户的积分变化日志"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'status': 'error', 'message': '未登录'}), 401
    
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                'SELECT id, points_change, reason, created_at FROM points_log WHERE user_id = %s ORDER BY created_at DESC LIMIT 100',
                (user_id,)
            )
            logs = cur.fetchall()
            keys = ['id', 'points_change', 'reason', 'created_at']
            return jsonify({
                'status': 'success',
                'data': [dict(zip(keys, l)) for l in logs]
            })
    finally:
        conn.close()

@app.route('/admin/users', methods=['GET'])
def admin_get_users():
    """获取所有用户列表"""
    if not session.get('admin_id'):
        return jsonify({'status': 'error', 'message': '无权限，请使用管理员账号登录'}), 403
    
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute('SELECT id, email, username, points, last_signin, created_at FROM users ORDER BY id DESC')
            users = cur.fetchall()
            keys = ['id', 'email', 'username', 'points', 'last_signin', 'created_at']
            return jsonify({
                'status': 'success',
                'data': [dict(zip(keys, u)) for u in users]
            })
    finally:
        conn.close()

@app.route('/admin/user/<int:user_id>', methods=['GET'])
def admin_get_user(user_id):
    """获取单个用户信息"""
    if not session.get('admin_id'):
        return jsonify({'status': 'error', 'message': '无权限'}), 403
    
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute('SELECT id, email, username, points, last_signin, created_at FROM users WHERE id=%s', (user_id,))
            user = cur.fetchone()
            if not user:
                return jsonify({'status': 'error', 'message': '用户不存在'}), 404
            keys = ['id', 'email', 'username', 'points', 'last_signin', 'created_at']
            return jsonify({'status': 'success', 'data': dict(zip(keys, user))})
    finally:
        conn.close()

@app.route('/admin/user/<int:user_id>/points', methods=['POST'])
def admin_update_points(user_id):
    """修改用户积分"""
    if not session.get('admin_id'):
        return jsonify({'status': 'error', 'message': '无权限'}), 403
    
    data = request.json
    points = data.get('points')
    
    if points is None:
        return jsonify({'status': 'error', 'message': '积分不能为空'}), 400
    
    try:
        points = int(points)
    except (TypeError, ValueError):
        return jsonify({'status': 'error', 'message': '积分必须是整数'}), 400
    
    if points < 0:
        return jsonify({'status': 'error', 'message': '积分不能为负数'}), 400
    
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute('UPDATE users SET points=%s WHERE id=%s', (points, user_id))
            if cur.rowcount == 0:
                return jsonify({'status': 'error', 'message': '用户不存在'}), 404
        conn.commit()
        return jsonify({'status': 'success', 'message': '积分修改成功'})
    finally:
        conn.close()

@app.route('/admin/add-user', methods=['POST'])
def admin_add_user():
    """管理员添加用户"""
    if not session.get('admin_id'):
        return jsonify({'status': 'error', 'message': '无权限'}), 403
    
    data = request.json
    email = data.get('email', '').strip()
    username = data.get('username', '').strip()
    password = data.get('password', '')
    phone = data.get('phone', '').strip()
    
    if not (email and username and password):
        return jsonify({'status': 'error', 'message': '邮箱、用户名、密码必填'}), 400
    
    if not valid_email(email):
        return jsonify({'status': 'error', 'message': '邮箱格式不正确'}), 400
    
    if len(password) < 6:
        return jsonify({'status': 'error', 'message': '密码至少6位'}), 400
    
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute('INSERT INTO users (email, username, password, phone) VALUES (%s, %s, %s, %s)',
                       (email, username, hash_password(password), phone))
        conn.commit()
        return jsonify({'status': 'success', 'message': '用户添加成功'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': '该邮箱已被注册'}), 400
    finally:
        conn.close()

@app.route('/admin/user/<int:user_id>/role', methods=['POST'])
def admin_update_role(user_id):
    """修改用户角色"""
    if not session.get('admin_id'):
        return jsonify({'status': 'error', 'message': '无权限'}), 403
    
    data = request.json
    role = data.get('role', '').strip()
    
    if role not in ['user', 'admin']:
        return jsonify({'status': 'error', 'message': '角色只能是user或admin'}), 400
    
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute('UPDATE users SET role=%s WHERE id=%s', (role, user_id))
            if cur.rowcount == 0:
                return jsonify({'status': 'error', 'message': '用户不存在'}), 404
        conn.commit()
        return jsonify({'status': 'success', 'message': '角色修改成功'})
    finally:
        conn.close()

@app.route('/admin/user/<int:user_id>', methods=['DELETE'])
def admin_delete_user(user_id):
    """删除用户"""
    if not session.get('admin_id'):
        return jsonify({'status': 'error', 'message': '无权限'}), 403
    
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute('DELETE FROM users WHERE id=%s', (user_id,))
            if cur.rowcount == 0:
                return jsonify({'status': 'error', 'message': '用户不存在'}), 404
        conn.commit()
        return jsonify({'status': 'success', 'message': '用户删除成功'})
    finally:
        conn.close()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    app.run(host='0.0.0.0', port=port, debug=debug)
