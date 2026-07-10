import json
import base64
from io import BytesIO
import qrcode
from flask import jsonify, request, make_response, render_template, g, current_app
from werkzeug.security import generate_password_hash, check_password_hash
from app.blueprints.auth import auth_bp
from app.blueprints.auth.services import (make_jwt, verify_jwt, generate_csrf,
                                          require_auth, require_admin, CSRF_COOKIE)
from app.blueprints.auth.webauthn_service import (
    register_begin, register_complete,
    login_begin, login_complete,
)
from app.blueprints.auth.telegram_bot import create_auth_token, get_user_by_telegram
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
                               httponly=False, samesite='Lax',
                               secure=not current_app.debug)
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
                   secure=not current_app.debug,
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

# WebAuthn

@auth_bp.route('/api/auth/webauthn/register/begin', methods=['POST'])
@require_auth
def api_webauthn_register_begin():
    try:
        options = register_begin(g.current_user['id'], g.current_user['username'])
        return jsonify({'ok': True, 'options': json.loads(options)})
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 400

@auth_bp.route('/api/auth/webauthn/register/complete', methods=['POST'])
@require_auth
def api_webauthn_register_complete():
    try:
        cred = request.get_json(silent=True)
        result = register_complete(g.current_user['id'], cred)
        return jsonify({'ok': True, 'credential': result})
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 400

@auth_bp.route('/api/auth/webauthn/login/begin', methods=['POST'])
def api_webauthn_login_begin():
    try:
        data = request.get_json(silent=True) or {}
        options, cred_id, challenge_id = login_begin(data.get('username'))
        return jsonify({'ok': True, 'options': json.loads(options), 'challenge_id': challenge_id})
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 400

@auth_bp.route('/api/auth/webauthn/login/complete', methods=['POST'])
def api_webauthn_login_complete():
    try:
        data = request.get_json(silent=True)
        user = login_complete(data['credential'], data['credential_id'], data['challenge_id'])
        token = make_jwt(user)
        resp = make_response(jsonify({'ok': True, 'redirect': '/'}))
        resp.set_cookie('session_token', token,
                       httponly=True, samesite='Lax',
                       secure=not current_app.debug,
                       max_age=8*3600)
        return resp
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 400

@auth_bp.route('/api/auth/webauthn/credentials')
@require_auth
def api_webauthn_credentials():
    conn = get_db_connection()
    creds = conn.execute(
        'SELECT id, name, created_at FROM webauthn_credentials WHERE user_id = ?',
        (g.current_user['id'],),
    ).fetchall()
    conn.close()
    return jsonify([dict(c) for c in creds])

@auth_bp.route('/api/auth/webauthn/credentials/<int:cred_id>', methods=['DELETE'])
@require_auth
def api_delete_webauthn_credential(cred_id):
    conn = get_db_connection()
    conn.execute('DELETE FROM webauthn_credentials WHERE id = ? AND user_id = ?',
                (cred_id, g.current_user['id']))
    conn.commit()
    conn.close()
    return jsonify({'ok': True})

# Telegram

@auth_bp.route('/api/auth/telegram/qrcode', methods=['GET'])
def api_telegram_qrcode():
    purpose = request.args.get('purpose', 'login')
    user_id = None
    if purpose == 'link':
        if not request.cookies.get('session_token'):
            return jsonify({'ok': False, 'error': 'Nao autenticado'}), 401
        payload = verify_jwt(request.cookies.get('session_token'))
        if not payload:
            return jsonify({'ok': False, 'error': 'Sessao invalida'}), 401
        user_id = payload['sub']
    token = create_auth_token('telegram_' + purpose, user_id)
    qr = qrcode.make(token, box_size=8)
    buf = BytesIO()
    qr.save(buf, format='PNG')
    b64 = base64.b64encode(buf.getvalue()).decode()
    return jsonify({'ok': True, 'token': token, 'qr_base64': b64})

@auth_bp.route('/api/auth/telegram/check', methods=['POST'])
def api_telegram_check():
    data = request.get_json(silent=True) or {}
    token = data.get('token', '')
    conn = get_db_connection()
    t = conn.execute(
        'SELECT * FROM auth_tokens WHERE token = ? AND consumed = 1',
        (token,),
    ).fetchone()
    if not t:
        conn.close()
        return jsonify({'ok': False, 'consumed': False})
    conn.close()
    if t['purpose'] == 'telegram_login':
        user = get_user_by_telegram(t['telegram_chat_id'])
        if not user:
            return jsonify({'ok': False, 'consumed': True, 'error': 'Usuario nao encontrado'})
        from app.blueprints.auth.services import make_jwt as mk_jwt
        jwt_token = mk_jwt(user)
        resp = make_response(jsonify({'ok': True, 'consumed': True, 'redirect': '/'}))
        resp.set_cookie('session_token', jwt_token,
                       httponly=True, samesite='Lax',
                       secure=not current_app.debug,
                       max_age=8*3600)
        return resp
    return jsonify({'ok': True, 'consumed': True})
