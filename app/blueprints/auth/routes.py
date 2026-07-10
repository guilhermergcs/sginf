from flask import jsonify, request, make_response, render_template, g, current_app
from werkzeug.security import generate_password_hash, check_password_hash
from app.blueprints.auth import auth_bp
from app.blueprints.auth.services import (make_jwt, verify_jwt, generate_csrf,
                                          require_auth, require_admin, CSRF_COOKIE)
from app.db import get_db_connection

@auth_bp.before_request
def csrf_check():
    if request.method in ('GET', 'HEAD', 'OPTIONS'):
        return
    if request.path.startswith('/api/bot/'):
        return
    if request.path.startswith('/api/auth/'):
        token = request.cookies.get(CSRF_COOKIE)
        header = request.headers.get('X-CSRF-Token')
        if not token or not header or token != header:
            return {'ok': False, 'error': 'CSRF invalido'}, 403

@auth_bp.after_request
def set_csrf_cookie(response):
    if request.path.startswith('/api/auth/') or request.path == '/login':
        if CSRF_COOKIE not in request.cookies:
            response.set_cookie(CSRF_COOKIE, generate_csrf(),
                               httponly=False, samesite='Lax')
    return response

@auth_bp.route('/login')
def login_page():
    return render_template('login.html')

@auth_bp.route('/register')
@require_admin
def register_page():
    return render_template('register.html')

@auth_bp.route('/settings')
@require_auth
def settings_page():
    return render_template('settings.html')

@auth_bp.route('/api/auth/login', methods=['POST'])
def api_login():
    data = request.get_json(silent=True) or {}
    username = data.get('username', '').strip()
    password = data.get('password', '')
    if not username or not password:
        return jsonify({'ok': False, 'error': 'Preencha usuario e senha'}), 400
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM usuarios_sistema WHERE username = ?',
                       (username,)).fetchone()
    conn.close()
    if not user or not check_password_hash(user['senha_hash'], password):
        return jsonify({'ok': False, 'error': 'Credenciais invalidas'}), 401
    token = make_jwt(user)
    resp = make_response(jsonify({'ok': True, 'redirect': '/'}))
    resp.set_cookie('session_token', token,
                   httponly=True, samesite='Lax',
                   max_age=8*3600)
    return resp

@auth_bp.route('/api/auth/logout', methods=['POST'])
@require_auth
def api_logout():
    resp = make_response(jsonify({'ok': True}))
    resp.delete_cookie('session_token')
    resp.delete_cookie(CSRF_COOKIE)
    return resp

@auth_bp.route('/api/auth/me')
@require_auth
def api_me():
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM usuarios_sistema WHERE id = ?',
                       (g.current_user['id'],)).fetchone()
    conn.close()
    return jsonify({
        'username': user['username'],
        'tipo': user['tipo'],
        'telegram_linked': bool(user['telegram_linked']),
    })

@auth_bp.route('/api/auth/register', methods=['POST'])
@require_admin
def api_register():
    data = request.get_json(silent=True) or {}
    username = data.get('username', '').strip()
    password = data.get('password', '')
    tipo = data.get('tipo', 'admin')
    if not username or len(username) < 3:
        return jsonify({'ok': False, 'error': 'Usuario deve ter ao menos 3 caracteres'}), 400
    if not password or len(password) < 4:
        return jsonify({'ok': False, 'error': 'Senha deve ter ao menos 4 caracteres'}), 400
    conn = get_db_connection()
    existing = conn.execute('SELECT id FROM usuarios_sistema WHERE username = ?',
                           (username,)).fetchone()
    if existing:
        conn.close()
        return jsonify({'ok': False, 'error': 'Usuario ja existe'}), 409
    pw_hash = generate_password_hash(password)
    conn.execute('INSERT INTO usuarios_sistema (username, senha_hash, tipo) VALUES (?, ?, ?)',
                (username, pw_hash, tipo))
    conn.commit()
    conn.close()
    return jsonify({'ok': True})

@auth_bp.route('/api/auth/change-password', methods=['POST'])
@require_auth
def api_change_password():
    data = request.get_json(silent=True) or {}
    old_pw = data.get('old_password', '')
    new_pw = data.get('new_password', '')
    if not old_pw or not new_pw:
        return jsonify({'ok': False, 'error': 'Preencha senha atual e nova'}), 400
    if len(new_pw) < 4:
        return jsonify({'ok': False, 'error': 'Nova senha deve ter ao menos 4 caracteres'}), 400
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM usuarios_sistema WHERE id = ?',
                       (g.current_user['id'],)).fetchone()
    if not check_password_hash(user['senha_hash'], old_pw):
        conn.close()
        return jsonify({'ok': False, 'error': 'Senha atual incorreta'}), 401
    conn.execute('UPDATE usuarios_sistema SET senha_hash = ? WHERE id = ?',
                (generate_password_hash(new_pw), user['id']))
    conn.commit()
    conn.close()
    return jsonify({'ok': True})
