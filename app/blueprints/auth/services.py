import jwt as pyjwt
from datetime import datetime, timedelta, timezone
import secrets
from flask import current_app, g, request

ALGORITHM = 'HS256'
CSRF_COOKIE = 'csrf_token'

def make_jwt(user):
    now = datetime.now(timezone.utc)
    payload = {
        'sub': user['id'],
        'username': user['username'],
        'tipo': user['tipo'],
        'iat': now,
        'exp': now + timedelta(hours=8),
    }
    return pyjwt.encode(payload, current_app.config['SECRET_KEY'], algorithm=ALGORITHM)

def verify_jwt(token):
    try:
        return pyjwt.decode(token, current_app.config['SECRET_KEY'], algorithms=[ALGORITHM])
    except pyjwt.ExpiredSignatureError:
        return None
    except pyjwt.InvalidTokenError:
        return None

def generate_csrf():
    return secrets.token_hex(32)

def require_auth(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.cookies.get('session_token')
        if not token:
            return {'ok': False, 'error': 'Nao autenticado'}, 401
        payload = verify_jwt(token)
        if not payload:
            return {'ok': False, 'error': 'Sessao expirada ou invalida'}, 401
        from app.db import get_db_connection
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM usuarios_sistema WHERE id = ?',
                           (payload['sub'],)).fetchone()
        conn.close()
        if not user:
            return {'ok': False, 'error': 'Usuario nao encontrado'}, 401
        g.current_user = dict(user)
        return f(*args, **kwargs)
    return decorated

def secure_cookie():
    return not current_app.debug

def require_admin(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.cookies.get('session_token')
        if not token:
            return {'ok': False, 'error': 'Nao autenticado'}, 401
        payload = verify_jwt(token)
        if not payload:
            return {'ok': False, 'error': 'Sessao expirada ou invalida'}, 401
        from app.db import get_db_connection
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM usuarios_sistema WHERE id = ?',
                           (payload['sub'],)).fetchone()
        conn.close()
        if not user:
            return {'ok': False, 'error': 'Usuario nao encontrado'}, 401
        if user['tipo'] != 'admin':
            return {'ok': False, 'error': 'Acesso restrito a administradores'}, 403
        g.current_user = dict(user)
        return f(*args, **kwargs)
    return decorated
