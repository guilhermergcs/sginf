from flask import Blueprint, jsonify, render_template, request
from app.db import get_db_connection
from app.blueprints.usuarios.services import listar_usuarios_ad, _set_user_status, _set_password, _update_user

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
        usuarios = listar_usuarios_ad(dict(config))
        return jsonify({"status": "success", "dados": usuarios})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@usuarios_bp.route('/api/usuarios/ativar', methods=['POST'])
def ativar_usuario():
    return _alterar_status(True)

@usuarios_bp.route('/api/usuarios/desativar', methods=['POST'])
def desativar_usuario():
    return _alterar_status(False)

@usuarios_bp.route('/api/usuarios/trocar-senha', methods=['POST'])
def trocar_senha():
    dados = request.json
    login = dados.get('login')
    nova_senha = dados.get('nova_senha')
    if not login or not nova_senha:
        return jsonify({"status": "error", "message": "Login e nova senha são obrigatórios"}), 400
    if len(nova_senha) < 6:
        return jsonify({"status": "error", "message": "A senha deve ter no mínimo 6 caracteres"}), 400
    conn_db = get_db_connection()
    config = conn_db.execute('SELECT * FROM config_ad WHERE id=1').fetchone()
    conn_db.close()
    if not config:
        return jsonify({"status": "error", "message": "Configuração AD não encontrada"}), 400
    try:
        _set_password(dict(config), login, nova_senha)
        return jsonify({"status": "success", "message": f"Senha do usuário {login} alterada com sucesso!"})
    except ValueError as e:
        return jsonify({"status": "error", "message": str(e)}), 404
    except Exception as e:
        return jsonify({"status": "error", "message": f"Erro ao alterar senha: {str(e)}"}), 500

@usuarios_bp.route('/api/usuarios/editar', methods=['POST'])
def editar_usuario():
    dados = request.json
    login_antigo = dados.get('login_antigo')
    if not login_antigo:
        return jsonify({"status": "error", "message": "Login antigo é obrigatório"}), 400
    campos = dados.get('campos', {})
    if not campos:
        return jsonify({"status": "error", "message": "Nenhum campo para alterar"}), 400
    conn_db = get_db_connection()
    config = conn_db.execute('SELECT * FROM config_ad WHERE id=1').fetchone()
    conn_db.close()
    if not config:
        return jsonify({"status": "error", "message": "Configuração AD não encontrada"}), 400
    try:
        _update_user(dict(config), login_antigo, campos)
        novo_login = campos.get('login', login_antigo)
        return jsonify({"status": "success", "message": f"Usuário {novo_login} atualizado com sucesso!"})
    except ValueError as e:
        return jsonify({"status": "error", "message": str(e)}), 404
    except Exception as e:
        return jsonify({"status": "error", "message": f"Erro ao atualizar usuário: {str(e)}"}), 500

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
        _set_user_status(dict(config), login, ativo)
        acao = 'ativado' if ativo else 'desativado'
        return jsonify({"status": "success", "message": f"Usuário {login} {acao} com sucesso!"})
    except ValueError as e:
        return jsonify({"status": "error", "message": str(e)}), 404
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
