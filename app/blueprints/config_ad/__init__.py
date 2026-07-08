from flask import Blueprint, jsonify, render_template, request
from app.db import get_db_connection
from app.blueprints.config_ad.services import testar_conexao_ldap

config_ad_bp = Blueprint('config_ad', __name__)

@config_ad_bp.route('/config')
def page_config():
    conn = get_db_connection()
    config = conn.execute('SELECT * FROM config_ad WHERE id=1').fetchone()
    conn.close()
    if config:
        return render_template('config.html', server=config['server'], ad_ip=config['ad_ip'] or '', base_dn=config['base_dn'], username=config['username'], ou_usuarios=config['ou_usuarios'] or 'OU=Domain Users')
    return render_template('config.html', server='', ad_ip='', base_dn='', username='', ou_usuarios='OU=Domain Users')

@config_ad_bp.route('/api/config')
def get_config():
    conn = get_db_connection()
    config = conn.execute('SELECT server, ad_ip, base_dn, username, ou_usuarios FROM config_ad WHERE id=1').fetchone()
    conn.close()
    if config:
        return jsonify(dict(config))
    return jsonify({})

@config_ad_bp.route('/api/config/salvar', methods=['POST'])
def salvar_config():
    dados = request.json
    conn = get_db_connection()
    conn.execute(
        'REPLACE INTO config_ad (id, server, ad_ip, base_dn, username, password, ou_usuarios) VALUES (1, ?, ?, ?, ?, ?, ?)',
        (dados.get('server'), dados.get('ad_ip'), dados.get('base_dn'), dados.get('username'), dados.get('password'), dados.get('ou_usuarios'))
    )
    conn.commit()
    conn.close()
    return jsonify({"status": "success", "message": "Configuração salva com sucesso!"})

@config_ad_bp.route('/api/config/testar', methods=['POST'])
def testar_config():
    from ldap3 import core
    dados = request.json
    server = dados.get('server')
    ad_ip = dados.get('ad_ip')
    base_dn = dados.get('base_dn')
    username = dados.get('username')
    password = dados.get('password')
    if not all([server, base_dn, username, password]):
        return jsonify({"status": "error", "message": "Todos os campos são obrigatórios"}), 400
    try:
        ok, msg = testar_conexao_ldap(server, ad_ip, base_dn, username, password)
        return jsonify({"status": "success", "message": msg})
    except core.exceptions.LDAPBindError as e:
        return jsonify({"status": "error", "message": f"Falha na autenticação: {str(e)}"}), 401
    except Exception as e:
        return jsonify({"status": "error", "message": f"Falha ao conectar: {str(e)}"}), 500
