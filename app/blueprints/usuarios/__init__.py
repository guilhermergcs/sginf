from flask import Blueprint, jsonify, render_template, request
from app.db import get_db_connection
from app.blueprints.usuarios.services import listar_usuarios_ad, _set_user_status

usuarios_bp = Blueprint('usuarios', __name__)

@usuarios_bp.route('/usuarios')
def page_usuarios():
    return render_template('usuarios.html')

@usuarios_bp.route('/api/usuarios')
def get_usuarios():
    conn_db = get_db_connection()
    config = conn_db.execute('SELECT * FROM config_ad WHERE id=1').fetchone()
    conn_db.close()
    if not config:
        return jsonify({"status": "error", "message": "Configuração AD não encontrada"}), 400
    try:
        usuarios = listar_usuarios_ad(config)
        return jsonify({"status": "success", "dados": usuarios})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@usuarios_bp.route('/api/usuarios/ativar', methods=['POST'])
def ativar_usuario():
    return _alterar_status(True)

@usuarios_bp.route('/api/usuarios/desativar', methods=['POST'])
def desativar_usuario():
    return _alterar_status(False)

def _alterar_status(ativo):
    dados = request.json
    login = dados.get('login')
    if not login:
        return jsonify({"status": "error", "message": "Login é obrigatório"}), 400
    conn_db = get_db_connection()
    config = conn_db.execute('SELECT * FROM config_ad WHERE id=1').fetchone()
    conn_db.close()
    if not config:
        return jsonify({"status": "error", "message": "Configuração AD não encontrada"}), 400
    try:
        _set_user_status(config, login, ativo)
        acao = 'ativado' if ativo else 'desativado'
        return jsonify({"status": "success", "message": f"Usuário {login} {acao} com sucesso!"})
    except ValueError as e:
        return jsonify({"status": "error", "message": str(e)}), 404
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
