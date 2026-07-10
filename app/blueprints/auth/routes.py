from flask import jsonify, request, make_response, render_template, g, current_app
from werkzeug.security import check_password_hash
from app.blueprints.auth import auth_bp
from app.blueprints.auth.services import (make_jwt, verify_jwt, generate_csrf,
                                          require_auth, CSRF_COOKIE)
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
    return jsonify({
        'username': g.current_user['username'],
        'tipo': g.current_user['tipo'],
    })
