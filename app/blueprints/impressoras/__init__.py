from flask import Blueprint, jsonify, render_template, request
from datetime import datetime
from app.db import get_db_connection
from app.blueprints.impressoras.services import verificar_impressoras_snmp

impressoras_bp = Blueprint('impressoras', __name__)

@impressoras_bp.route('/impressoras')
def page_impressoras():
    return render_template('impressoras.html')

@impressoras_bp.route('/api/impressoras')
def get_impressoras():
    conn = get_db_connection()
    impressoras = conn.execute('SELECT * FROM impressoras').fetchall()
    conn.close()
    return jsonify([dict(ix) for ix in impressoras])

@impressoras_bp.route('/api/impressoras/adicionar', methods=['POST'])
def adicionar_impressora():
    dados = request.json
    nome = dados.get('nome', '').strip()
    ip = dados.get('ip', '').strip()
    comunidade = dados.get('comunidade_snmp', 'public').strip()
    if not nome or not ip:
        return jsonify({"status": "error", "message": "Nome e IP são obrigatórios"}), 400
    conn = get_db_connection()
    conn.execute(
        'INSERT INTO impressoras (nome, ip, comunidade_snmp) VALUES (?, ?, ?)',
        (nome, ip, comunidade)
    )
    conn.commit()
    conn.close()
    return jsonify({"status": "success", "message": "Impressora cadastrada!"})

@impressoras_bp.route('/api/impressoras/remover/<int:id>', methods=['DELETE'])
def remover_impressora(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM impressoras WHERE id=?', (id,))
    conn.commit()
    conn.close()
    return jsonify({"status": "success", "message": "Impressora removida!"})

@impressoras_bp.route('/api/sync/impressoras', methods=['POST'])
def sync_impressoras():
    conn_db = get_db_connection()
    impressoras = conn_db.execute('SELECT * FROM impressoras').fetchall()
    conn_db.close()
    if not impressoras:
        return jsonify({"status": "success", "message": "Nenhuma impressora cadastrada", "dados": []})
    resultados_async = verificar_impressoras_snmp(impressoras)
    resultados = []
    for idx, (online, modelo) in enumerate(resultados_async):
        prt = impressoras[idx]
        agora = datetime.now().strftime('%d/%m/%Y %H:%M')
        conn_db = get_db_connection()
        conn_db.execute(
            'UPDATE impressoras SET status=?, modelo=?, ultima_verificacao=? WHERE id=?',
            ('ok' if online else 'offline', modelo, agora, prt['id'])
        )
        conn_db.commit()
        conn_db.close()
        resultados.append({
            'id': prt['id'], 'nome': prt['nome'], 'ip': prt['ip'],
            'status': 'ok' if online else 'offline',
            'modelo': modelo, 'ultima_verificacao': agora
        })
    return jsonify({"status": "success", "message": f"Verificadas {len(resultados)} impressoras", "dados": resultados})
