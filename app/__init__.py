from flask import Flask


def create_app():
    app = Flask(__name__, template_folder='templates')
    from app.blueprints.computadores import computadores_bp
    from app.blueprints.impressoras import impressoras_bp
    from app.blueprints.config_ad import config_ad_bp
    app.register_blueprint(computadores_bp)
    app.register_blueprint(impressoras_bp)
    app.register_blueprint(config_ad_bp)
    return app
