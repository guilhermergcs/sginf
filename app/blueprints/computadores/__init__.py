from flask import Blueprint, jsonify, render_template, request
import socket
import threading
from app.db import get_db_connection
from app.blueprints.computadores.services import sync_computadores_ad, verificar_status_computador

computadores_bp = Blueprint('computadores', __name__)

@computadores_bp.route('/')
@computadores_bp.route('/computadores')
def page_computadores():
    return render_template('computadores.html')

@computadores_bp.route('/api/computadores')
def get_computadores():
    conn = get_db_connection()
    computadores = conn.execute('SELECT * FROM computadores').fetchall()
    conn.close()
    return jsonify([dict(ix) for ix in computadores])

@computadores_bp.route('/api/sync/computadores', methods=['POST'])
def sync_computadores():
    from ldap3 import core
    conn_db = get_db_connection()
    config = conn_db.execute('SELECT * FROM config_ad WHERE id=1').fetchone()
    conn_db.close()
    if not config:
        return jsonify({"status": "error", "message": "Configuração AD não encontrada"}), 400
    config = dict(config)
    try:
        total = sync_computadores_ad(config)
        return jsonify({"status": "success", "message": f"Sincronizados {total} computadores do AD!"})
    except core.exceptions.LDAPBindError as e:
        return jsonify({"status": "error", "message": f"Falha na autenticação: {str(e)}"}), 401
    except Exception as e:
        return jsonify({"status": "error", "message": f"Falha ao sincronizar: {str(e)}"}), 500

@computadores_bp.route('/api/sync/status', methods=['POST'])
def sync_status():
    conn_db = get_db_connection()
    config = conn_db.execute('SELECT * FROM config_ad WHERE id=1').fetchone()
    computadores = conn_db.execute('SELECT id, nome, ip FROM computadores').fetchall()
    conn_db.close()
    ad_user = config['username'] if config else ''
    ad_pass = config['password'] if config else ''
    if config:
        config = dict(config)
        dns_server = config.get('ad_ip') or config.get('server')
    else:
        dns_server = None
    resultados = []

    def verificar(pc):
        resultado = verificar_status_computador(dict(pc), ad_user, ad_pass, dns_server)
        resultados.append(resultado)

    threads = []
    for pc in computadores:
        t = threading.Thread(target=verificar, args=(pc,))
        t.start()
        threads.append(t)
    for t in threads:
        t.join()

    return jsonify({"status": "success", "message": f"Verificados {len(resultados)} computadores", "dados": resultados})