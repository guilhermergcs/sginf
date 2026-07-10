from flask import jsonify, request, make_response, render_template
from app.blueprints.auth import auth_bp

@auth_bp.route('/login')
def login_page():
    return render_template('login.html')

@auth_bp.route('/api/auth/login', methods=['POST'])
def api_login():
    data = request.get_json(silent=True) or {}
    username = data.get('username', '')
    password = data.get('password', '')
    if username == 'admin' and password == 'admin':
        resp = make_response(jsonify({'ok': True, 'redirect': '/'}))
        resp.set_cookie('session_token', 'dummy', httponly=True, samesite='Lax')
        return resp
    return jsonify({'ok': False, 'error': 'Credenciais invalidas'}), 401

@auth_bp.route('/api/auth/me')
def api_me():
    return jsonify({'username': 'admin', 'tipo': 'admin'})
