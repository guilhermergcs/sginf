from flask import Flask, request, g, abort
import os

def create_app():
    app = Flask(__name__, template_folder='templates')
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or os.urandom(32).hex()
    app.config['TELEGRAM_BOT_TOKEN'] = os.environ.get('TELEGRAM_BOT_TOKEN', '')

    from app.blueprints.auth import auth_bp
    app.register_blueprint(auth_bp)

    from app.blueprints.computadores import computadores_bp
    from app.blueprints.impressoras import impressoras_bp
    from app.blueprints.usuarios import usuarios_bp
    from app.blueprints.grupos import grupos_bp
    from app.blueprints.config_ad import config_ad_bp
    from app.blueprints.wifi import wifi_bp
    app.register_blueprint(computadores_bp)
    app.register_blueprint(impressoras_bp)
    app.register_blueprint(usuarios_bp)
    app.register_blueprint(grupos_bp)
    app.register_blueprint(config_ad_bp)
    app.register_blueprint(wifi_bp)

    @app.before_request
    def global_auth_check():
        if request.path.startswith(('/login', '/api/auth/', '/static/', '/api/bot/')):
            return
        from app.blueprints.auth.services import verify_jwt
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

    from app.blueprints.auth.telegram_bot import TelegramBot
    bot = TelegramBot(app.config.get('TELEGRAM_BOT_TOKEN', ''))
    bot.start(app)
    app.config['TELEGRAM_BOT'] = bot

    return app
