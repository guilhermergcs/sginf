from flask import Flask, request, g
import os


def create_app():
    from setup_db import migrar
    migrar()

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

    @app.before_request
    def skip_auth():
        g.current_user = {'id': 1, 'username': 'admin', 'tipo': 'admin'}

    if not app.debug or os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
        bot_token = app.config.get('TELEGRAM_BOT_TOKEN', '')
        if bot_token:
            from app.blueprints.auth.telegram_bot import TelegramBot
            bot = TelegramBot(bot_token)
            bot.start(app)
            app.config['TELEGRAM_BOT'] = bot

    return app
