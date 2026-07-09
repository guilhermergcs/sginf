from flask import Blueprint, jsonify, render_template, request
from app.db import get_db_connection
from app.blueprints.grupos.services import listar_grupos_ad, listar_membros_grupo, adicionar_membro_grupo, remover_membro_grupo, _create_group, _update_group, _delete_group

grupos_bp = Blueprint('grupos', __name__)

@grupos_bp.route('/grupos')
def page_grupos():
    return render_template('grupos.html')

@grupos_bp.route('/api/grupos')
def get_grupos():
    conn_db = get_db_connection()
    config = conn_db.execute('SELECT * FROM config_ad WHERE id=1').fetchone()
    conn_db.close()
    if not config:
        return jsonify({"status": "error", "message": "Configuração AD não encontrada"}), 400
    try:
        grupos = listar_grupos_ad(dict(config))
        return jsonify({"status": "success", "dados": grupos})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@grupos_bp.route('/api/grupos/membros')
def get_membros():
    group = request.args.get('group')
    if not group:
        return jsonify({"status": "error", "message": "Grupo é obrigatório"}), 400
    conn_db = get_db_connection()
    config = conn_db.execute('SELECT * FROM config_ad WHERE id=1').fetchone()
    conn_db.close()
    if not config:
        return jsonify({"status": "error", "message": "Configuração AD não encontrada"}), 400
    try:
        membros = listar_membros_grupo(dict(config), group)
        return jsonify({"status": "success", "dados": membros})
    except ValueError as e:
        return jsonify({"status": "error", "message": str(e)}), 404
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@grupos_bp.route('/api/grupos/adicionar-membro', methods=['POST'])
def adicionar_membro():
    dados = request.json
    group = dados.get('group')
    user = dados.get('user')
    if not group or not user:
        return jsonify({"status": "error", "message": "Grupo e usuário são obrigatórios"}), 400
    conn_db = get_db_connection()
    config = conn_db.execute('SELECT * FROM config_ad WHERE id=1').fetchone()
    conn_db.close()
    if not config:
        return jsonify({"status": "error", "message": "Configuração AD não encontrada"}), 400
    try:
        adicionar_membro_grupo(dict(config), group, user)
        return jsonify({"status": "success", "message": f"Usuário {user} adicionado ao grupo {group}"})
    except ValueError as e:
        return jsonify({"status": "error", "message": str(e)}), 404
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@grupos_bp.route('/api/grupos/remover-membro', methods=['POST'])
def remover_membro():
    dados = request.json
    group = dados.get('group')
    user = dados.get('user')
    if not group or not user:
        return jsonify({"status": "error", "message": "Grupo e usuário são obrigatórios"}), 400
    conn_db = get_db_connection()
    config = conn_db.execute('SELECT * FROM config_ad WHERE id=1').fetchone()
    conn_db.close()
    if not config:
        return jsonify({"status": "error", "message": "Configuração AD não encontrada"}), 400
    try:
        remover_membro_grupo(dict(config), group, user)
        return jsonify({"status": "success", "message": f"Usuário {user} removido do grupo {group}"})
    except ValueError as e:
        return jsonify({"status": "error", "message": str(e)}), 404
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@grupos_bp.route('/api/grupos/criar', methods=['POST'])
def criar_grupo():
    dados = request.json
    cn = dados.get('cn', '').strip()
    if not cn:
        return jsonify({"status": "error", "message": "Nome do grupo é obrigatório"}), 400
    description = dados.get('description', '').strip()
    conn_db = get_db_connection()
    config = conn_db.execute('SELECT * FROM config_ad WHERE id=1').fetchone()
    conn_db.close()
    if not config:
        return jsonify({"status": "error", "message": "Configuração AD não encontrada"}), 400
    try:
        _create_group(dict(config), cn, description)
        return jsonify({"status": "success", "message": f"Grupo {cn} criado com sucesso!"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@grupos_bp.route('/api/grupos/editar', methods=['POST'])
def editar_grupo():
    dados = request.json
    group_antigo = dados.get('group_antigo')
    if not group_antigo:
        return jsonify({"status": "error", "message": "Grupo original é obrigatório"}), 400
    novo_cn = dados.get('novo_cn', '').strip()
    description = dados.get('description', '').strip()
    if not novo_cn and not description:
        return jsonify({"status": "error", "message": "Nenhum campo para alterar"}), 400
    conn_db = get_db_connection()
    config = conn_db.execute('SELECT * FROM config_ad WHERE id=1').fetchone()
    conn_db.close()
    if not config:
        return jsonify({"status": "error", "message": "Configuração AD não encontrada"}), 400
    try:
        _update_group(dict(config), group_antigo, novo_cn, description)
        novo = novo_cn or group_antigo
        return jsonify({"status": "success", "message": f"Grupo {novo} atualizado com sucesso!"})
    except ValueError as e:
        return jsonify({"status": "error", "message": str(e)}), 404
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@grupos_bp.route('/api/grupos/excluir', methods=['POST'])
def excluir_grupo():
    dados = request.json
    group = dados.get('group')
    if not group:
        return jsonify({"status": "error", "message": "Grupo é obrigatório"}), 400
    conn_db = get_db_connection()
    config = conn_db.execute('SELECT * FROM config_ad WHERE id=1').fetchone()
    conn_db.close()
    if not config:
        return jsonify({"status": "error", "message": "Configuração AD não encontrada"}), 400
    try:
        _delete_group(dict(config), group)
        return jsonify({"status": "success", "message": f"Grupo {group} excluído com sucesso!"})
    except ValueError as e:
        return jsonify({"status": "error", "message": str(e)}), 404
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
