from flask import Blueprint, jsonify, render_template, request
from datetime import datetime
from app.db import get_db_connection
from app.blueprints.wifi.services import verificar_wifi_snmp
from app.blueprints.wifi.unifi_api import UnifiController, UnifiError, testar_conexao

wifi_bp = Blueprint('wifi', __name__)

@wifi_bp.route('/wifi')
def page_wifi():
    conn = get_db_connection()
    config = conn.execute('SELECT * FROM config_unifi WHERE id=1').fetchone()
    conn.close()
    return render_template('wifi.html', controller_host=config['host'] if config else '')

@wifi_bp.route('/api/wifi')
def get_wifi():
    conn = get_db_connection()
    dispositivos = conn.execute('SELECT * FROM dispositivos_wifi ORDER BY nome').fetchall()
    conn.close()
    return jsonify([dict(d) for d in dispositivos])

@wifi_bp.route('/api/wifi/adicionar', methods=['POST'])
def adicionar_wifi():
    dados = request.json
    nome = dados.get('nome', '').strip()
    ip = dados.get('ip', '').strip()
    comunidade = dados.get('comunidade_snmp', 'public').strip()
    if not nome or not ip:
        return jsonify({"status": "error", "message": "Nome e IP são obrigatórios"}), 400
    conn = get_db_connection()
    try:
        conn.execute(
            'INSERT INTO dispositivos_wifi (nome, ip, comunidade_snmp) VALUES (?, ?, ?)',
            (nome, ip, comunidade)
        )
        conn.commit()
        return jsonify({"status": "success", "message": "Dispositivo Wi-Fi cadastrado!"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400
    finally:
        conn.close()

@wifi_bp.route('/api/wifi/remover/<int:id>', methods=['DELETE'])
def remover_wifi(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM dispositivos_wifi WHERE id=?', (id,))
    conn.commit()
    conn.close()
    return jsonify({"status": "success", "message": "Dispositivo removido!"})

@wifi_bp.route('/api/config/unifi')
def get_config_unifi():
    conn = get_db_connection()
    config = conn.execute('SELECT host, username FROM config_unifi WHERE id=1').fetchone()
    conn.close()
    if config:
        return jsonify({'host': config['host'], 'username': config['username']})
    return jsonify({'host': '', 'username': ''})

@wifi_bp.route('/api/config/unifi/salvar', methods=['POST'])
def salvar_config_unifi():
    dados = request.json
    conn = get_db_connection()
    conn.execute(
        'REPLACE INTO config_unifi (id, host, username, password) VALUES (1, ?, ?, ?)',
        (dados.get('host', '').strip(), dados.get('username', '').strip(), dados.get('password', '').strip())
    )
    conn.commit()
    conn.close()
    return jsonify({"status": "success", "message": "Configuração salva!"})

@wifi_bp.route('/api/config/unifi/testar', methods=['POST'])
def testar_config_unifi():
    dados = request.json
    ok, msg = testar_conexao(
        dados.get('host', '').strip(),
        dados.get('username', '').strip(),
        dados.get('password', '').strip()
    )
    if ok:
        return jsonify({"status": "success", "message": msg})
    return jsonify({"status": "error", "message": msg}), 400

@wifi_bp.route('/api/sync/wifi', methods=['POST'])
def sync_wifi():
    conn_db = get_db_connection()
    config = conn_db.execute('SELECT * FROM config_unifi WHERE id=1').fetchone()
    agora = datetime.now().strftime('%d/%m/%Y %H:%M')

    # Tenta Controller API primeiro
    if config and config['host'] and config['username'] and config['password']:
        try:
            ctrl = UnifiController(config['host'], config['username'], config['password'])
            devices = ctrl.get_devices()
            conn_db.execute('DELETE FROM dispositivos_wifi')
            resultados = []
            for d in devices:
                num_sta = d['num_sta'] or 0
                n2 = d['clientes_2g'] or 0
                n5 = d['clientes_5g'] or 0
                n6 = d['clientes_6g'] or 0
                online = d['state'] == 1
                conn_db.execute(
                    'INSERT INTO dispositivos_wifi (nome, ip, modelo, clientes_2g, clientes_5g, clientes_6g, clientes_total, status, ultima_verificacao) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
                    (d['name'], d['ip'], d['model'], n2, n5, n6, num_sta, 'online' if online else 'offline', agora)
                )
                resultados.append({
                    'nome': d['name'], 'ip': d['ip'], 'modelo': d['model'],
                    'clientes_2g': n2, 'clientes_5g': n5, 'clientes_6g': n6,
                    'clientes_total': num_sta,
                    'status': 'online' if online else 'offline',
                    'ultima_verificacao': agora
                })
            conn_db.commit()
            conn_db.close()
            return jsonify({"status": "success", "message": f"Controller OK! {len(resultados)} APs sincronizados.", "dados": resultados})
        except UnifiError as e:
            conn_db.close()
            return jsonify({"status": "error", "message": f"Controller: {str(e)}"}), 400
        except Exception as e:
            conn_db.close()
            return jsonify({"status": "error", "message": f"Controller: {str(e)}"}), 500

    # Fallback: SNMP para dispositivos cadastrados manualmente
    dispositivos = conn_db.execute('SELECT * FROM dispositivos_wifi').fetchall()
    conn_db.close()
    if not dispositivos:
        return jsonify({"status": "success", "message": "Nenhum dispositivo cadastrado", "dados": []})

    resultados_async = verificar_wifi_snmp(dispositivos)
    resultados = []
    for idx, (online, nome, modelo, clientes_2g, clientes_5g) in enumerate(resultados_async):
        d = dispositivos[idx]
        clientes_total = clientes_2g + clientes_5g
        conn_db = get_db_connection()
        snmp_nome = nome or None
        conn_db.execute(
            'UPDATE dispositivos_wifi SET status=?, modelo=?, clientes_2g=?, clientes_5g=?, clientes_total=?, ultima_verificacao=?, nome=COALESCE(?, nome) WHERE id=?',
            ('online' if online else 'offline', modelo, clientes_2g, clientes_5g, clientes_total, agora, snmp_nome, d['id'])
        )
        conn_db.commit()
        conn_db.close()
        resultados.append({
            'id': d['id'], 'nome': nome or d['nome'], 'ip': d['ip'],
            'status': 'online' if online else 'offline',
            'modelo': modelo, 'clientes_2g': clientes_2g,
            'clientes_5g': clientes_5g, 'clientes_total': clientes_total,
            'ultima_verificacao': agora
        })
    return jsonify({"status": "success", "message": f"Verificados {len(resultados)} dispositivos via SNMP", "dados": resultados})
