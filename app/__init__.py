from flask import Flask, request, g, redirect
import os


def create_app():
    app = Flask(__name__, template_folder='templates')

    secret_key = os.environ.get('SECRET_KEY')
    if not secret_key:
        raise RuntimeError(
            'SECRET_KEY environment variable is required. '
            'Generate one with: python -c "import secrets; print(secrets.token_hex(32))"'
        )
    app.config['SECRET_KEY'] = secret_key
    app.config['COOKIE_SECURE'] = os.environ.get('COOKIE_SECURE', 'false').lower() not in ('0', 'false', 'no')
    app.config['TELEGRAM_BOT_TOKEN'] = os.environ.get('TELEGRAM_BOT_TOKEN', '')

    from app.blueprints.auth import auth_bp
    from app.blueprints.computadores import computadores_bp
    from app.blueprints.impressoras import impressoras_bp
    from app.blueprints.usuarios import usuarios_bp
    from app.blueprints.grupos import grupos_bp
    from app.blueprints.config_ad import config_ad_bp
    from app.blueprints.wifi import wifi_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(computadores_bp)
    app.register_blueprint(impressoras_bp)
    app.register_blueprint(usuarios_bp)
    app.register_blueprint(grupos_bp)
    app.register_blueprint(config_ad_bp)
    app.register_blueprint(wifi_bp)

    from app.blueprints.auth.services import verify_jwt, CSRF_COOKIE, generate_csrf
    from app.db import get_db_connection

    PUBLIC_PATHS = ('/login', '/static/', '/api/auth/', '/api/bot/')

    @app.before_request
    def global_auth_check():
        if request.path.startswith(PUBLIC_PATHS):
            return

        if request.method not in ('GET', 'HEAD', 'OPTIONS'):
            csrf_token = request.cookies.get(CSRF_COOKIE)
            header_token = request.headers.get('X-CSRF-Token')
            if not csrf_token or not header_token or csrf_token != header_token:
                return {'ok': False, 'error': 'CSRF invalido'}, 403

        token = request.cookies.get('session_token')
        if not token:
            return _unauthenticated_response()

        payload = verify_jwt(token)
        if not payload:
            return _unauthenticated_response()

        conn = get_db_connection()
        try:
            user = conn.execute(
                'SELECT * FROM usuarios_sistema WHERE id = ?', (payload['sub'],)
            ).fetchone()
        finally:
            conn.close()

        if not user:
            return _unauthenticated_response()

        g.current_user = dict(user)

    def _unauthenticated_response():
        if request.path.startswith('/api/'):
            return {'ok': False, 'error': 'Nao autenticado'}, 401
        return redirect('/login')

    @app.after_request
    def set_csrf_cookie(response):
        if CSRF_COOKIE not in request.cookies:
            response.set_cookie(
                CSRF_COOKIE, generate_csrf(),
                httponly=False, samesite='Lax',
                secure=app.config['COOKIE_SECURE'],
            )
        return response

    if not app.debug or os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
        bot_token = app.config.get('TELEGRAM_BOT_TOKEN', '')
        if bot_token:
            from app.blueprints.auth.telegram_bot import TelegramBot
            bot = TelegramBot(bot_token)
            bot.start(app)
            app.config['TELEGRAM_BOT'] = bot

    return app
