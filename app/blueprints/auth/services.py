import jwt as pyjwt
from datetime import datetime, timedelta, timezone
import secrets
from flask import current_app, g, request, jsonify

ALGORITHM = 'HS256'
CSRF_COOKIE = 'csrf_token'

def make_jwt(user):
    now = datetime.now(timezone.utc)
    payload = {
        'sub': str(user['id']),
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
        if 'current_user' not in g or not g.current_user:
            return jsonify({'ok': False, 'error': 'Nao autenticado'}), 401
        return f(*args, **kwargs)
    return decorated

def secure_cookie():
    return current_app.config.get('COOKIE_SECURE', True)

def require_admin(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'current_user' not in g or not g.current_user:
            return jsonify({'ok': False, 'error': 'Nao autenticado'}), 401
        if g.current_user.get('tipo') != 'admin':
            return jsonify({'ok': False, 'error': 'Acesso restrito a administradores'}), 403
        return f(*args, **kwargs)
    return decorated
