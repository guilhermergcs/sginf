from flask import Blueprint, jsonify, render_template, request
from datetime import datetime
from app.db import get_db_connection
from app.blueprints.wifi.services import verificar_wifi_snmp

wifi_bp = Blueprint('wifi', __name__)

@wifi_bp.route('/wifi')
def page_wifi():
    return render_template('wifi.html')

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

@wifi_bp.route('/api/sync/wifi', methods=['POST'])
def sync_wifi():
    conn_db = get_db_connection()
    dispositivos = conn_db.execute('SELECT * FROM dispositivos_wifi').fetchall()
    conn_db.close()
    if not dispositivos:
        return jsonify({"status": "success", "message": "Nenhum dispositivo cadastrado", "dados": []})
    resultados_async = verificar_wifi_snmp(dispositivos)
    resultados = []
    for idx, (online, nome, modelo, clientes_2g, clientes_5g) in enumerate(resultados_async):
        d = dispositivos[idx]
        agora = datetime.now().strftime('%d/%m/%Y %H:%M')
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
    return jsonify({"status": "success", "message": f"Verificados {len(resultados)} dispositivos", "dados": resultados})
